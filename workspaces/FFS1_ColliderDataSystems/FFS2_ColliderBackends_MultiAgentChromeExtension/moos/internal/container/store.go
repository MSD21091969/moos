package container

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgconn"
	_ "github.com/jackc/pgx/v5/stdlib"
)

type Record struct {
	URN             string
	ParentURN       sql.NullString
	Kind            string
	InterfaceJSON   json.RawMessage
	KernelJSON      json.RawMessage
	PermissionsJSON json.RawMessage
	Version         int64
}

type Store struct {
	db *sql.DB
}

type WireRecord struct {
	FromContainerURN string
	FromPort         string
	ToContainerURN   string
	ToPort           string
	MetadataJSON     json.RawMessage
}

type MorphismLogRecord struct {
	Type            string
	ActorURN        string
	ScopeURN        string
	ExpectedVersion *int64
	PayloadJSON     json.RawMessage
	MetadataJSON    json.RawMessage
	IssuedAt        time.Time
}

type MorphismLogQuery struct {
	ScopeURN string
	Type     string
	Limit    int
}

type MorphismLogEntry struct {
	ID              string          `json:"id"`
	Type            string          `json:"type"`
	ActorURN        string          `json:"actor_urn"`
	ScopeURN        string          `json:"scope_urn"`
	ExpectedVersion *int64          `json:"expected_version,omitempty"`
	PayloadJSON     json.RawMessage `json:"payload_json"`
	MetadataJSON    json.RawMessage `json:"metadata_json"`
	IssuedAt        time.Time       `json:"issued_at"`
	CommittedAt     time.Time       `json:"committed_at"`
}

var ErrNotFound = errors.New("container not found")
var ErrVersionConflict = errors.New("container version conflict")
var ErrAlreadyExists = errors.New("resource already exists")

func NewStore(databaseURL string) (*Store, error) {
	db, err := sql.Open("pgx", databaseURL)
	if err != nil {
		return nil, err
	}
	if pingErr := db.Ping(); pingErr != nil {
		_ = db.Close()
		return nil, pingErr
	}
	return &Store{db: db}, nil
}

func (store *Store) Close() error {
	return store.db.Close()
}

func (store *Store) Health(ctx context.Context) error {
	return store.db.PingContext(ctx)
}

func (store *Store) GetByURN(ctx context.Context, urn string) (*Record, error) {
	row := store.db.QueryRowContext(ctx, `
		SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version
		FROM containers
		WHERE urn = $1
	`, urn)

	var record Record
	if err := row.Scan(
		&record.URN,
		&record.ParentURN,
		&record.Kind,
		&record.InterfaceJSON,
		&record.KernelJSON,
		&record.PermissionsJSON,
		&record.Version,
	); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, ErrNotFound
		}
		return nil, err
	}
	return &record, nil
}

func (store *Store) Create(ctx context.Context, record Record) error {
	if record.URN == "" {
		return fmt.Errorf("urn is required")
	}
	if record.Kind == "" {
		record.Kind = "data"
	}
	if len(record.InterfaceJSON) == 0 {
		record.InterfaceJSON = json.RawMessage(`{}`)
	}
	if len(record.KernelJSON) == 0 {
		record.KernelJSON = json.RawMessage(`{}`)
	}
	if len(record.PermissionsJSON) == 0 {
		record.PermissionsJSON = json.RawMessage(`{}`)
	}
	if record.Version <= 0 {
		record.Version = 1
	}

	_, err := store.db.ExecContext(ctx, `
		INSERT INTO containers (urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`,
		record.URN,
		record.ParentURN,
		record.Kind,
		record.InterfaceJSON,
		record.KernelJSON,
		record.PermissionsJSON,
		record.Version,
	)
	return err
}

func (store *Store) ListChildren(ctx context.Context, parentURN string) ([]Record, error) {
	rows, err := store.db.QueryContext(ctx, `
		SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version
		FROM containers
		WHERE parent_urn = $1
		ORDER BY urn
	`, parentURN)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := make([]Record, 0)
	for rows.Next() {
		var record Record
		if scanErr := rows.Scan(
			&record.URN,
			&record.ParentURN,
			&record.Kind,
			&record.InterfaceJSON,
			&record.KernelJSON,
			&record.PermissionsJSON,
			&record.Version,
		); scanErr != nil {
			return nil, scanErr
		}
		result = append(result, record)
	}
	if rowsErr := rows.Err(); rowsErr != nil {
		return nil, rowsErr
	}

	return result, nil
}

func (store *Store) TreeTraversal(ctx context.Context, rootURN string) ([]Record, error) {
	if strings.TrimSpace(rootURN) == "" {
		return nil, fmt.Errorf("root urn is required")
	}

	rows, err := store.db.QueryContext(ctx, `
		WITH RECURSIVE tree AS (
			SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version, 0 AS depth
			FROM containers
			WHERE urn = $1
			UNION ALL
			SELECT child.urn, child.parent_urn, child.kind, child.interface_json, child.kernel_json, child.permissions_json, child.version, tree.depth + 1
			FROM containers child
			JOIN tree ON child.parent_urn = tree.urn
		)
		SELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version
		FROM tree
		ORDER BY depth, urn
	`, rootURN)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := make([]Record, 0)
	for rows.Next() {
		var record Record
		if scanErr := rows.Scan(
			&record.URN,
			&record.ParentURN,
			&record.Kind,
			&record.InterfaceJSON,
			&record.KernelJSON,
			&record.PermissionsJSON,
			&record.Version,
		); scanErr != nil {
			return nil, scanErr
		}
		result = append(result, record)
	}
	if rowsErr := rows.Err(); rowsErr != nil {
		return nil, rowsErr
	}
	if len(result) == 0 {
		return nil, ErrNotFound
	}

	return result, nil
}

func (store *Store) MutateKernel(ctx context.Context, urn string, expectedVersion int64, kernelJSON json.RawMessage) (int64, error) {
	if strings.TrimSpace(urn) == "" {
		return 0, fmt.Errorf("urn is required")
	}
	if expectedVersion <= 0 {
		return 0, fmt.Errorf("expected_version must be > 0")
	}
	if len(kernelJSON) == 0 {
		kernelJSON = json.RawMessage(`{}`)
	}

	result, err := store.db.ExecContext(ctx, `
		UPDATE containers
		SET kernel_json = $1, version = version + 1
		WHERE urn = $2 AND version = $3
	`, kernelJSON, urn, expectedVersion)
	if err != nil {
		return 0, err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return 0, err
	}
	if rows == 1 {
		return expectedVersion + 1, nil
	}

	current, getErr := store.GetByURN(ctx, urn)
	if getErr != nil {
		if errors.Is(getErr, ErrNotFound) {
			return 0, ErrNotFound
		}
		return 0, getErr
	}
	if current.Version != expectedVersion {
		return current.Version, ErrVersionConflict
	}

	return 0, ErrVersionConflict
}

func (store *Store) Link(ctx context.Context, wire WireRecord) error {
	if strings.TrimSpace(wire.FromContainerURN) == "" {
		return fmt.Errorf("from_container_urn is required")
	}
	if strings.TrimSpace(wire.FromPort) == "" {
		return fmt.Errorf("from_port is required")
	}
	if strings.TrimSpace(wire.ToContainerURN) == "" {
		return fmt.Errorf("to_container_urn is required")
	}
	if strings.TrimSpace(wire.ToPort) == "" {
		return fmt.Errorf("to_port is required")
	}
	if len(wire.MetadataJSON) == 0 {
		wire.MetadataJSON = json.RawMessage(`{}`)
	}

	_, err := store.db.ExecContext(ctx, `
		INSERT INTO wires (from_container_urn, from_port, to_container_urn, to_port, metadata_json)
		VALUES ($1, $2, $3, $4, $5)
	`, wire.FromContainerURN, wire.FromPort, wire.ToContainerURN, wire.ToPort, wire.MetadataJSON)
	if err == nil {
		return nil
	}

	var pgError *pgconn.PgError
	if errors.As(err, &pgError) {
		switch pgError.Code {
		case "23505":
			return ErrAlreadyExists
		case "23503":
			return ErrNotFound
		}
	}

	return err
}

func (store *Store) Unlink(ctx context.Context, wire WireRecord) error {
	if strings.TrimSpace(wire.FromContainerURN) == "" {
		return fmt.Errorf("from_container_urn is required")
	}
	if strings.TrimSpace(wire.FromPort) == "" {
		return fmt.Errorf("from_port is required")
	}
	if strings.TrimSpace(wire.ToContainerURN) == "" {
		return fmt.Errorf("to_container_urn is required")
	}
	if strings.TrimSpace(wire.ToPort) == "" {
		return fmt.Errorf("to_port is required")
	}

	result, err := store.db.ExecContext(ctx, `
		DELETE FROM wires
		WHERE from_container_urn = $1 AND from_port = $2 AND to_container_urn = $3 AND to_port = $4
	`, wire.FromContainerURN, wire.FromPort, wire.ToContainerURN, wire.ToPort)
	if err != nil {
		return err
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return err
	}
	if rowsAffected == 0 {
		return ErrNotFound
	}

	return nil
}

func (store *Store) AppendMorphismLog(ctx context.Context, record MorphismLogRecord) error {
	if strings.TrimSpace(record.Type) == "" {
		return fmt.Errorf("type is required")
	}
	if strings.TrimSpace(record.ActorURN) == "" {
		return fmt.Errorf("actor_urn is required")
	}
	if strings.TrimSpace(record.ScopeURN) == "" {
		return fmt.Errorf("scope_urn is required")
	}
	if len(record.PayloadJSON) == 0 {
		record.PayloadJSON = json.RawMessage(`{}`)
	}
	if len(record.MetadataJSON) == 0 {
		record.MetadataJSON = json.RawMessage(`{}`)
	}
	if record.IssuedAt.IsZero() {
		record.IssuedAt = time.Now().UTC()
	}

	logID, err := newUUIDString()
	if err != nil {
		return err
	}

	_, err = store.db.ExecContext(ctx, `
		INSERT INTO morphism_log (id, type, actor_urn, scope_urn, expected_version, payload_json, metadata_json, issued_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`, logID, record.Type, record.ActorURN, record.ScopeURN, record.ExpectedVersion, record.PayloadJSON, record.MetadataJSON, record.IssuedAt)
	return err
}

func (store *Store) ListMorphismLog(ctx context.Context, query MorphismLogQuery) ([]MorphismLogEntry, error) {
	if query.Limit <= 0 {
		query.Limit = 50
	}
	if query.Limit > 200 {
		query.Limit = 200
	}

	const baseQuery = `
		SELECT id, type, actor_urn, scope_urn, expected_version, payload_json, metadata_json, issued_at, committed_at
		FROM morphism_log
	`

	args := make([]any, 0, 3)
	conditions := make([]string, 0, 2)
	position := 1
	if strings.TrimSpace(query.ScopeURN) != "" {
		conditions = append(conditions, fmt.Sprintf("scope_urn = $%d", position))
		args = append(args, query.ScopeURN)
		position++
	}
	if strings.TrimSpace(query.Type) != "" {
		conditions = append(conditions, fmt.Sprintf("type = $%d", position))
		args = append(args, query.Type)
		position++
	}

	sqlQuery := baseQuery
	if len(conditions) > 0 {
		sqlQuery += " WHERE " + strings.Join(conditions, " AND ")
	}
	sqlQuery += fmt.Sprintf(" ORDER BY committed_at DESC LIMIT $%d", position)
	args = append(args, query.Limit)

	rows, err := store.db.QueryContext(ctx, sqlQuery, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	entries := make([]MorphismLogEntry, 0)
	for rows.Next() {
		var entry MorphismLogEntry
		if scanErr := rows.Scan(
			&entry.ID,
			&entry.Type,
			&entry.ActorURN,
			&entry.ScopeURN,
			&entry.ExpectedVersion,
			&entry.PayloadJSON,
			&entry.MetadataJSON,
			&entry.IssuedAt,
			&entry.CommittedAt,
		); scanErr != nil {
			return nil, scanErr
		}
		entries = append(entries, entry)
	}
	if rowsErr := rows.Err(); rowsErr != nil {
		return nil, rowsErr
	}

	return entries, nil
}

func newUUIDString() (string, error) {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80

	return fmt.Sprintf(
		"%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
		b[0], b[1], b[2], b[3],
		b[4], b[5],
		b[6], b[7],
		b[8], b[9],
		b[10], b[11], b[12], b[13], b[14], b[15],
	), nil
}
