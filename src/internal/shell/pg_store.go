package shell

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"moos/src/internal/cat"
)

// PostgresStore stores the morphism log in PostgreSQL.
type PostgresStore struct {
	pool *pgxpool.Pool
}

// NewPostgresStore creates a Postgres-backed store.
// It creates the morphism_log table if it doesn't exist.
func NewPostgresStore(ctx context.Context, connString string) (*PostgresStore, error) {
	pool, err := pgxpool.New(ctx, connString)
	if err != nil {
		return nil, fmt.Errorf("connecting to postgres: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("pinging postgres: %w", err)
	}
	if _, err := pool.Exec(ctx, `
		CREATE TABLE IF NOT EXISTS morphism_log (
			id         BIGSERIAL    PRIMARY KEY,
			issued_at  TIMESTAMPTZ  NOT NULL,
			envelope   JSONB        NOT NULL
		)
	`); err != nil {
		pool.Close()
		return nil, fmt.Errorf("creating morphism_log table: %w", err)
	}
	return &PostgresStore{pool: pool}, nil
}

func (s *PostgresStore) Append(entries []cat.PersistedEnvelope) error {
	ctx := context.Background()
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return fmt.Errorf("beginning tx: %w", err)
	}
	defer tx.Rollback(ctx)

	for _, entry := range entries {
		data, err := json.Marshal(entry.Envelope)
		if err != nil {
			return fmt.Errorf("marshalling envelope: %w", err)
		}
		if _, err := tx.Exec(ctx,
			`INSERT INTO morphism_log (issued_at, envelope) VALUES ($1, $2)`,
			entry.IssuedAt, data,
		); err != nil {
			return fmt.Errorf("inserting morphism: %w", err)
		}
	}
	return tx.Commit(ctx)
}

func (s *PostgresStore) ReadAll() ([]cat.PersistedEnvelope, error) {
	ctx := context.Background()
	rows, err := s.pool.Query(ctx,
		`SELECT issued_at, envelope FROM morphism_log ORDER BY id`)
	if err != nil {
		return nil, fmt.Errorf("querying morphism_log: %w", err)
	}
	defer rows.Close()

	var entries []cat.PersistedEnvelope
	for rows.Next() {
		var entry cat.PersistedEnvelope
		var envData []byte
		if err := rows.Scan(&entry.IssuedAt, &envData); err != nil {
			return nil, fmt.Errorf("scanning row: %w", err)
		}
		if err := json.Unmarshal(envData, &entry.Envelope); err != nil {
			return nil, fmt.Errorf("unmarshalling envelope: %w", err)
		}
		entries = append(entries, entry)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterating rows: %w", err)
	}
	return entries, nil
}

// Close shuts down the connection pool.
func (s *PostgresStore) Close() {
	s.pool.Close()
}

// ensure PostgresStore implements pgx import usage at compile time
var _ pgx.Tx = (pgx.Tx)(nil)
