package shell

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	_ "github.com/jackc/pgx/v5/stdlib"

	"moos/platform/kernel/internal/core"
)

const defaultPostgresTable = "moos_kernel_morphism_log"

type PostgresStore struct {
	db    *sql.DB
	table string
}

func NewPostgresStore(databaseURL string) (*PostgresStore, error) {
	if databaseURL == "" {
		return nil, fmt.Errorf("database url is required for postgres store")
	}
	db, err := sql.Open("pgx", databaseURL)
	if err != nil {
		return nil, err
	}
	store := &PostgresStore{db: db, table: defaultPostgresTable}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		_ = db.Close()
		return nil, err
	}
	if err := store.ensureSchema(ctx); err != nil {
		_ = db.Close()
		return nil, err
	}
	return store, nil
}

func (store *PostgresStore) AppendBatch(entries []core.PersistedEnvelope) error {
	if len(entries) == 0 {
		return nil
	}
	tx, err := store.db.BeginTx(context.Background(), nil)
	if err != nil {
		return err
	}
	query := fmt.Sprintf("INSERT INTO %s (issued_at, envelope) VALUES ($1, $2)", store.table)
	for _, entry := range entries {
		encoded, err := json.Marshal(entry.Envelope)
		if err != nil {
			_ = tx.Rollback()
			return err
		}
		if _, err := tx.ExecContext(context.Background(), query, entry.IssuedAt.UTC(), encoded); err != nil {
			_ = tx.Rollback()
			return err
		}
	}
	return tx.Commit()
}

func (store *PostgresStore) Load() ([]core.PersistedEnvelope, error) {
	query := fmt.Sprintf("SELECT issued_at, envelope FROM %s ORDER BY id ASC", store.table)
	rows, err := store.db.QueryContext(context.Background(), query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	entries := []core.PersistedEnvelope{}
	for rows.Next() {
		var issuedAt time.Time
		var envelopeJSON []byte
		if err := rows.Scan(&issuedAt, &envelopeJSON); err != nil {
			return nil, err
		}
		var envelope core.Envelope
		if err := json.Unmarshal(envelopeJSON, &envelope); err != nil {
			return nil, err
		}
		entries = append(entries, core.PersistedEnvelope{Envelope: envelope, IssuedAt: issuedAt.UTC()})
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return entries, nil
}

func (store *PostgresStore) Close() error {
	return store.db.Close()
}

func (store *PostgresStore) ensureSchema(ctx context.Context) error {
	query := fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s (
			id BIGSERIAL PRIMARY KEY,
			issued_at TIMESTAMPTZ NOT NULL,
			envelope JSONB NOT NULL
		)
	`, store.table)
	_, err := store.db.ExecContext(ctx, query)
	return err
}
