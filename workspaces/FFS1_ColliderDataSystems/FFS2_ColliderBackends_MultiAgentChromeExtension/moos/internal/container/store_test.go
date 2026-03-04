package container

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"regexp"
	"testing"
	"time"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/jackc/pgx/v5/pgconn"
)

func TestErrNotFoundIdentity(t *testing.T) {
	if !errors.Is(ErrNotFound, ErrNotFound) {
		t.Fatalf("ErrNotFound should match itself")
	}
}

func TestCreateAppliesDefaults(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	mock.ExpectExec(regexp.QuoteMeta("INSERT INTO containers (urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version)")).
		WithArgs(
			"urn:test:create",
			sql.NullString{},
			"data",
			json.RawMessage(`{}`),
			json.RawMessage(`{}`),
			json.RawMessage(`{}`),
			int64(1),
		).
		WillReturnResult(sqlmock.NewResult(1, 1))

	err = store.Create(context.Background(), Record{URN: "urn:test:create"})
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("sql expectations not met: %v", err)
	}
}

func TestGetByURNNotFound(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	mock.ExpectQuery(regexp.QuoteMeta("SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version")).
		WithArgs("urn:missing").
		WillReturnError(sql.ErrNoRows)

	_, err = store.GetByURN(context.Background(), "urn:missing")
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("expected ErrNotFound, got %v", err)
	}
}

func TestListChildrenReturnsRows(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	rows := sqlmock.NewRows([]string{"urn", "parent_urn", "kind", "interface_json", "kernel_json", "permissions_json", "version"}).
		AddRow("urn:child:1", "urn:root", "data", []byte(`{}`), []byte(`{"k":1}`), []byte(`{}`), int64(2))
	mock.ExpectQuery(regexp.QuoteMeta("SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version")).
		WithArgs("urn:root").
		WillReturnRows(rows)

	result, err := store.ListChildren(context.Background(), "urn:root")
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if len(result) != 1 || result[0].URN != "urn:child:1" {
		t.Fatalf("unexpected list result: %+v", result)
	}
}

func TestTreeTraversalRootNotFound(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	mock.ExpectQuery(regexp.QuoteMeta("WITH RECURSIVE tree AS")).WithArgs("urn:none").WillReturnRows(
		sqlmock.NewRows([]string{"urn", "parent_urn", "kind", "interface_json", "kernel_json", "permissions_json", "version"}),
	)

	_, err = store.TreeTraversal(context.Background(), "urn:none")
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("expected ErrNotFound, got %v", err)
	}
}

func TestMutateKernelValidationAndConflict(t *testing.T) {
	store := &Store{}
	if _, err := store.MutateKernel(context.Background(), "", 1, json.RawMessage(`{}`)); err == nil {
		t.Fatalf("expected validation error for empty urn")
	}
	if _, err := store.MutateKernel(context.Background(), "urn:x", 0, json.RawMessage(`{}`)); err == nil {
		t.Fatalf("expected validation error for version")
	}

	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()
	store.db = db

	mock.ExpectExec(regexp.QuoteMeta("UPDATE containers SET kernel_json = $1, version = version + 1 WHERE urn = $2 AND version = $3")).
		WithArgs(json.RawMessage(`{"next":true}`), "urn:x", int64(1)).
		WillReturnResult(sqlmock.NewResult(0, 0))

	rows := sqlmock.NewRows([]string{"urn", "parent_urn", "kind", "interface_json", "kernel_json", "permissions_json", "version"}).
		AddRow("urn:x", sql.NullString{}, "data", []byte(`{}`), []byte(`{}`), []byte(`{}`), int64(3))
	mock.ExpectQuery(regexp.QuoteMeta("SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version")).
		WithArgs("urn:x").
		WillReturnRows(rows)

	current, err := store.MutateKernel(context.Background(), "urn:x", 1, json.RawMessage(`{"next":true}`))
	if !errors.Is(err, ErrVersionConflict) {
		t.Fatalf("expected ErrVersionConflict, got %v", err)
	}
	if current != 3 {
		t.Fatalf("expected current version 3, got %d", current)
	}
}

func TestLinkUnlinkAndLogMappings(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	wire := WireRecord{FromContainerURN: "urn:a", FromPort: "out", ToContainerURN: "urn:b", ToPort: "in"}

	mock.ExpectExec(regexp.QuoteMeta("INSERT INTO wires (from_container_urn, from_port, to_container_urn, to_port, metadata_json) VALUES ($1, $2, $3, $4, $5)")).
		WithArgs("urn:a", "out", "urn:b", "in", json.RawMessage(`{}`)).
		WillReturnError(&pgconn.PgError{Code: "23505"})
	if err := store.Link(context.Background(), wire); !errors.Is(err, ErrAlreadyExists) {
		t.Fatalf("expected ErrAlreadyExists, got %v", err)
	}

	mock.ExpectExec(regexp.QuoteMeta("DELETE FROM wires WHERE from_container_urn = $1 AND from_port = $2 AND to_container_urn = $3 AND to_port = $4")).
		WithArgs("urn:a", "out", "urn:b", "in").
		WillReturnResult(sqlmock.NewResult(0, 0))
	if err := store.Unlink(context.Background(), wire); !errors.Is(err, ErrNotFound) {
		t.Fatalf("expected ErrNotFound, got %v", err)
	}

	mock.ExpectExec(regexp.QuoteMeta("INSERT INTO morphism_log (id, type, actor_urn, scope_urn, expected_version, payload_json, metadata_json, issued_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)")).
		WithArgs(sqlmock.AnyArg(), "MUTATE", "urn:actor", "urn:scope", sqlmock.AnyArg(), json.RawMessage(`{"ok":true}`), json.RawMessage(`{}`), sqlmock.AnyArg()).
		WillReturnResult(sqlmock.NewResult(0, 1))
	expectedVersion := int64(2)
	err = store.AppendMorphismLog(context.Background(), MorphismLogRecord{
		Type:            "MUTATE",
		ActorURN:        "urn:actor",
		ScopeURN:        "urn:scope",
		ExpectedVersion: &expectedVersion,
		PayloadJSON:     json.RawMessage(`{"ok":true}`),
		IssuedAt:        time.Now().UTC(),
	})
	if err != nil {
		t.Fatalf("expected no error appending morphism log, got %v", err)
	}

	queryRows := sqlmock.NewRows([]string{"id", "type", "actor_urn", "scope_urn", "expected_version", "payload_json", "metadata_json", "issued_at", "committed_at"}).
		AddRow("id-1", "MUTATE", "urn:actor", "urn:scope", int64(2), []byte(`{"ok":true}`), []byte(`{}`), time.Now().UTC(), time.Now().UTC())
	mock.ExpectQuery(regexp.QuoteMeta("SELECT id, type, actor_urn, scope_urn, expected_version, payload_json, metadata_json, issued_at, committed_at FROM morphism_log")).
		WithArgs("urn:scope", "MUTATE", 20).
		WillReturnRows(queryRows)
	entries, err := store.ListMorphismLog(context.Background(), MorphismLogQuery{ScopeURN: "urn:scope", Type: "MUTATE", Limit: 20})
	if err != nil {
		t.Fatalf("expected no error listing log, got %v", err)
	}
	if len(entries) != 1 || entries[0].ID != "id-1" {
		t.Fatalf("unexpected entries: %+v", entries)
	}

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("sql expectations not met: %v", err)
	}
}

func TestNewUUIDString(t *testing.T) {
	id, err := newUUIDString()
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if len(id) != 36 {
		t.Fatalf("expected UUID length 36, got %d", len(id))
	}
}

func TestGetByURNSuccess(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	rows := sqlmock.NewRows([]string{"urn", "parent_urn", "kind", "interface_json", "kernel_json", "permissions_json", "version"}).
		AddRow("urn:ok", sql.NullString{}, "data", []byte(`{}`), []byte(`{"ok":true}`), []byte(`{}`), int64(2))
	mock.ExpectQuery(regexp.QuoteMeta("SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version")).
		WithArgs("urn:ok").
		WillReturnRows(rows)

	record, err := store.GetByURN(context.Background(), "urn:ok")
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if record.URN != "urn:ok" || record.Version != 2 {
		t.Fatalf("unexpected record: %+v", record)
	}
}

func TestGetByURNQueryError(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	mock.ExpectQuery(regexp.QuoteMeta("SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version")).
		WithArgs("urn:error").
		WillReturnError(errors.New("query exploded"))

	_, err = store.GetByURN(context.Background(), "urn:error")
	if err == nil {
		t.Fatalf("expected query error")
	}
}

func TestTreeTraversalSuccess(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	rows := sqlmock.NewRows([]string{"urn", "parent_urn", "kind", "interface_json", "kernel_json", "permissions_json", "version"}).
		AddRow("urn:root", sql.NullString{}, "composite", []byte(`{}`), []byte(`{}`), []byte(`{}`), int64(1)).
		AddRow("urn:child", "urn:root", "data", []byte(`{}`), []byte(`{}`), []byte(`{}`), int64(1))
	mock.ExpectQuery(regexp.QuoteMeta("WITH RECURSIVE tree AS")).WithArgs("urn:root").WillReturnRows(rows)

	records, err := store.TreeTraversal(context.Background(), "urn:root")
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if len(records) != 2 {
		t.Fatalf("expected 2 records, got %d", len(records))
	}
}

func TestMutateKernelSuccess(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	mock.ExpectExec(regexp.QuoteMeta("UPDATE containers SET kernel_json = $1, version = version + 1 WHERE urn = $2 AND version = $3")).
		WithArgs(json.RawMessage(`{"ok":1}`), "urn:mutate", int64(2)).
		WillReturnResult(sqlmock.NewResult(0, 1))

	next, err := store.MutateKernel(context.Background(), "urn:mutate", 2, json.RawMessage(`{"ok":1}`))
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if next != 3 {
		t.Fatalf("expected next version 3, got %d", next)
	}
}

func TestMutateKernelRowsAffectedAndFinalConflictBranch(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	mock.ExpectExec(regexp.QuoteMeta("UPDATE containers SET kernel_json = $1, version = version + 1 WHERE urn = $2 AND version = $3")).
		WithArgs(json.RawMessage(`{"x":1}`), "urn:rows", int64(1)).
		WillReturnResult(sqlmock.NewErrorResult(errors.New("rows affected failed")))
	if _, err := store.MutateKernel(context.Background(), "urn:rows", 1, json.RawMessage(`{"x":1}`)); err == nil {
		t.Fatalf("expected rows affected error")
	}

	mock.ExpectExec(regexp.QuoteMeta("UPDATE containers SET kernel_json = $1, version = version + 1 WHERE urn = $2 AND version = $3")).
		WithArgs(json.RawMessage(`{"x":2}`), "urn:same", int64(2)).
		WillReturnResult(sqlmock.NewResult(0, 0))
	rows := sqlmock.NewRows([]string{"urn", "parent_urn", "kind", "interface_json", "kernel_json", "permissions_json", "version"}).
		AddRow("urn:same", sql.NullString{}, "data", []byte(`{}`), []byte(`{}`), []byte(`{}`), int64(2))
	mock.ExpectQuery(regexp.QuoteMeta("SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version")).
		WithArgs("urn:same").
		WillReturnRows(rows)
	_, err = store.MutateKernel(context.Background(), "urn:same", 2, json.RawMessage(`{"x":2}`))
	if !errors.Is(err, ErrVersionConflict) {
		t.Fatalf("expected ErrVersionConflict, got %v", err)
	}
}

func TestLinkAndUnlinkValidationAndSuccess(t *testing.T) {
	store := &Store{}
	if err := store.Link(context.Background(), WireRecord{}); err == nil {
		t.Fatalf("expected validation error for empty wire")
	}
	if err := store.Unlink(context.Background(), WireRecord{}); err == nil {
		t.Fatalf("expected validation error for empty wire")
	}

	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()
	store.db = db

	wire := WireRecord{FromContainerURN: "urn:a", FromPort: "out", ToContainerURN: "urn:b", ToPort: "in"}
	mock.ExpectExec(regexp.QuoteMeta("INSERT INTO wires (from_container_urn, from_port, to_container_urn, to_port, metadata_json) VALUES ($1, $2, $3, $4, $5)")).
		WithArgs("urn:a", "out", "urn:b", "in", json.RawMessage(`{}`)).
		WillReturnResult(sqlmock.NewResult(1, 1))
	if err := store.Link(context.Background(), wire); err != nil {
		t.Fatalf("expected no error, got %v", err)
	}

	mock.ExpectExec(regexp.QuoteMeta("DELETE FROM wires WHERE from_container_urn = $1 AND from_port = $2 AND to_container_urn = $3 AND to_port = $4")).
		WithArgs("urn:a", "out", "urn:b", "in").
		WillReturnResult(sqlmock.NewResult(0, 1))
	if err := store.Unlink(context.Background(), wire); err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
}

func TestLinkAndUnlinkValidationBranchesAndRowsAffectedError(t *testing.T) {
	store := &Store{}
	if err := store.Link(context.Background(), WireRecord{FromContainerURN: "urn:a"}); err == nil {
		t.Fatalf("expected from_port validation error")
	}
	if err := store.Link(context.Background(), WireRecord{FromContainerURN: "urn:a", FromPort: "out"}); err == nil {
		t.Fatalf("expected to_container_urn validation error")
	}
	if err := store.Link(context.Background(), WireRecord{FromContainerURN: "urn:a", FromPort: "out", ToContainerURN: "urn:b"}); err == nil {
		t.Fatalf("expected to_port validation error")
	}

	if err := store.Unlink(context.Background(), WireRecord{FromContainerURN: "urn:a"}); err == nil {
		t.Fatalf("expected from_port validation error")
	}
	if err := store.Unlink(context.Background(), WireRecord{FromContainerURN: "urn:a", FromPort: "out"}); err == nil {
		t.Fatalf("expected to_container_urn validation error")
	}
	if err := store.Unlink(context.Background(), WireRecord{FromContainerURN: "urn:a", FromPort: "out", ToContainerURN: "urn:b"}); err == nil {
		t.Fatalf("expected to_port validation error")
	}

	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()
	store.db = db

	wire := WireRecord{FromContainerURN: "urn:a", FromPort: "out", ToContainerURN: "urn:b", ToPort: "in"}
	mock.ExpectExec(regexp.QuoteMeta("DELETE FROM wires WHERE from_container_urn = $1 AND from_port = $2 AND to_container_urn = $3 AND to_port = $4")).
		WithArgs("urn:a", "out", "urn:b", "in").
		WillReturnResult(sqlmock.NewErrorResult(errors.New("rows failed")))
	if err := store.Unlink(context.Background(), wire); err == nil {
		t.Fatalf("expected rows affected error")
	}
}

func TestAppendMorphismLogValidationAndListClamp(t *testing.T) {
	store := &Store{}
	if err := store.AppendMorphismLog(context.Background(), MorphismLogRecord{}); err == nil {
		t.Fatalf("expected validation error for empty log")
	}

	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()
	store.db = db

	rows := sqlmock.NewRows([]string{"id", "type", "actor_urn", "scope_urn", "expected_version", "payload_json", "metadata_json", "issued_at", "committed_at"}).
		AddRow("id-2", "ADD", "urn:actor", "urn:scope", nil, []byte(`{}`), []byte(`{}`), time.Now().UTC(), time.Now().UTC())
	mock.ExpectQuery(regexp.QuoteMeta("SELECT id, type, actor_urn, scope_urn, expected_version, payload_json, metadata_json, issued_at, committed_at FROM morphism_log")).
		WithArgs(200).
		WillReturnRows(rows)
	entries, err := store.ListMorphismLog(context.Background(), MorphismLogQuery{Limit: 999})
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if len(entries) != 1 || entries[0].ID != "id-2" {
		t.Fatalf("unexpected entries: %+v", entries)
	}
}

func TestListChildrenAndTreeQueryErrors(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	mock.ExpectQuery(regexp.QuoteMeta("SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version")).
		WithArgs("urn:root").
		WillReturnError(errors.New("query failed"))
	if _, err := store.ListChildren(context.Background(), "urn:root"); err == nil {
		t.Fatalf("expected list children query error")
	}

	mock.ExpectQuery(regexp.QuoteMeta("WITH RECURSIVE tree AS")).
		WithArgs("urn:root").
		WillReturnError(errors.New("tree query failed"))
	if _, err := store.TreeTraversal(context.Background(), "urn:root"); err == nil {
		t.Fatalf("expected tree traversal query error")
	}
}

func TestTreeTraversalValidationAndRowsError(t *testing.T) {
	store := &Store{}
	if _, err := store.TreeTraversal(context.Background(), " "); err == nil {
		t.Fatalf("expected validation error for empty root urn")
	}

	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()
	store.db = db

	rows := sqlmock.NewRows([]string{"urn", "parent_urn", "kind", "interface_json", "kernel_json", "permissions_json", "version"}).
		AddRow("urn:root", sql.NullString{}, "composite", []byte(`{}`), []byte(`{}`), []byte(`{}`), int64(1)).
		RowError(0, errors.New("row failed"))
	mock.ExpectQuery(regexp.QuoteMeta("WITH RECURSIVE tree AS")).WithArgs("urn:root").WillReturnRows(rows)
	if _, err := store.TreeTraversal(context.Background(), "urn:root"); err == nil {
		t.Fatalf("expected rows error")
	}
}

func TestMutateKernelExecErrorAndNotFound(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	mock.ExpectExec(regexp.QuoteMeta("UPDATE containers SET kernel_json = $1, version = version + 1 WHERE urn = $2 AND version = $3")).
		WithArgs(json.RawMessage(`{"err":1}`), "urn:exec", int64(1)).
		WillReturnError(errors.New("exec failed"))
	if _, err := store.MutateKernel(context.Background(), "urn:exec", 1, json.RawMessage(`{"err":1}`)); err == nil {
		t.Fatalf("expected mutate exec error")
	}

	mock.ExpectExec(regexp.QuoteMeta("UPDATE containers SET kernel_json = $1, version = version + 1 WHERE urn = $2 AND version = $3")).
		WithArgs(json.RawMessage(`{"missing":1}`), "urn:missing", int64(1)).
		WillReturnResult(sqlmock.NewResult(0, 0))
	mock.ExpectQuery(regexp.QuoteMeta("SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version")).
		WithArgs("urn:missing").
		WillReturnError(sql.ErrNoRows)
	_, err = store.MutateKernel(context.Background(), "urn:missing", 1, json.RawMessage(`{"missing":1}`))
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("expected ErrNotFound, got %v", err)
	}
}

func TestLinkAndUnlinkExecErrors(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	wire := WireRecord{FromContainerURN: "urn:a", FromPort: "out", ToContainerURN: "urn:b", ToPort: "in"}

	mock.ExpectExec(regexp.QuoteMeta("INSERT INTO wires (from_container_urn, from_port, to_container_urn, to_port, metadata_json) VALUES ($1, $2, $3, $4, $5)")).
		WithArgs("urn:a", "out", "urn:b", "in", json.RawMessage(`{}`)).
		WillReturnError(errors.New("insert failed"))
	if err := store.Link(context.Background(), wire); err == nil {
		t.Fatalf("expected link exec error")
	}

	mock.ExpectExec(regexp.QuoteMeta("DELETE FROM wires WHERE from_container_urn = $1 AND from_port = $2 AND to_container_urn = $3 AND to_port = $4")).
		WithArgs("urn:a", "out", "urn:b", "in").
		WillReturnError(errors.New("delete failed"))
	if err := store.Unlink(context.Background(), wire); err == nil {
		t.Fatalf("expected unlink exec error")
	}
}

func TestAppendAndListValidationErrors(t *testing.T) {
	store := &Store{}
	if err := store.AppendMorphismLog(context.Background(), MorphismLogRecord{Type: "ADD"}); err == nil {
		t.Fatalf("expected actor validation error")
	}
	if err := store.AppendMorphismLog(context.Background(), MorphismLogRecord{Type: "ADD", ActorURN: "urn:a"}); err == nil {
		t.Fatalf("expected scope validation error")
	}

	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()
	store.db = db
	mock.ExpectQuery(regexp.QuoteMeta("SELECT id, type, actor_urn, scope_urn, expected_version, payload_json, metadata_json, issued_at, committed_at FROM morphism_log")).
		WithArgs("urn:scope", "ADD", 10).
		WillReturnError(errors.New("list failed"))
	if _, err := store.ListMorphismLog(context.Background(), MorphismLogQuery{ScopeURN: "urn:scope", Type: "ADD", Limit: 10}); err == nil {
		t.Fatalf("expected list morphism log error")
	}
}

func TestNewStoreHealthCloseAndDefaults(t *testing.T) {
	_, err := NewStore("postgres://invalid:invalid@127.0.0.1:1/moos?sslmode=disable&connect_timeout=1")
	if err == nil {
		t.Fatalf("expected connection failure for invalid database url")
	}

	db, mock, err := sqlmock.New(sqlmock.MonitorPingsOption(true))
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	store := &Store{db: db}
	mock.ExpectPing().WillReturnError(nil)
	if err := store.Health(context.Background()); err != nil {
		t.Fatalf("expected health success, got %v", err)
	}
	mock.ExpectClose()
	if err := store.Close(); err != nil {
		t.Fatalf("expected close success, got %v", err)
	}
}

func TestLinkForeignKeyAndAppendDefaults(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer db.Close()

	store := &Store{db: db}
	wire := WireRecord{FromContainerURN: "urn:from", FromPort: "out", ToContainerURN: "urn:to", ToPort: "in"}
	mock.ExpectExec(regexp.QuoteMeta("INSERT INTO wires (from_container_urn, from_port, to_container_urn, to_port, metadata_json) VALUES ($1, $2, $3, $4, $5)")).
		WithArgs("urn:from", "out", "urn:to", "in", json.RawMessage(`{}`)).
		WillReturnError(&pgconn.PgError{Code: "23503"})
	if err := store.Link(context.Background(), wire); !errors.Is(err, ErrNotFound) {
		t.Fatalf("expected ErrNotFound, got %v", err)
	}

	mock.ExpectExec(regexp.QuoteMeta("INSERT INTO morphism_log (id, type, actor_urn, scope_urn, expected_version, payload_json, metadata_json, issued_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)")).
		WithArgs(sqlmock.AnyArg(), "ADD", "urn:actor", "urn:scope", nil, json.RawMessage(`{}`), json.RawMessage(`{}`), sqlmock.AnyArg()).
		WillReturnResult(sqlmock.NewResult(0, 1))
	if err := store.AppendMorphismLog(context.Background(), MorphismLogRecord{Type: "ADD", ActorURN: "urn:actor", ScopeURN: "urn:scope"}); err != nil {
		t.Fatalf("expected append default success, got %v", err)
	}
}
