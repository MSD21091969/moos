package migrate

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	_ "github.com/jackc/pgx/v5/stdlib"
)

type Runner struct {
	db  *sql.DB
	dir string
}

type StatusItem struct {
	Version   string
	AppliedAt time.Time
}

func NewRunner(databaseURL string, migrationDir string) (*Runner, error) {
	db, err := sql.Open("pgx", databaseURL)
	if err != nil {
		return nil, err
	}
	if pingErr := db.Ping(); pingErr != nil {
		_ = db.Close()
		return nil, pingErr
	}
	if _, statErr := os.Stat(migrationDir); statErr != nil {
		_ = db.Close()
		return nil, statErr
	}
	return &Runner{db: db, dir: migrationDir}, nil
}

func (runner *Runner) Close() error {
	return runner.db.Close()
}

func (runner *Runner) Up(ctx context.Context) ([]string, error) {
	if err := runner.ensureTable(ctx); err != nil {
		return nil, err
	}

	entries, err := os.ReadDir(runner.dir)
	if err != nil {
		return nil, err
	}

	migrationFiles := sortedSQLFiles(entries)
	applied := make([]string, 0)

	for _, fileName := range migrationFiles {
		version := strings.TrimSuffix(fileName, filepath.Ext(fileName))
		isApplied, checkErr := runner.hasVersion(ctx, version)
		if checkErr != nil {
			return applied, checkErr
		}
		if isApplied {
			continue
		}

		path := filepath.Join(runner.dir, fileName)
		sqlBytes, readErr := os.ReadFile(path)
		if readErr != nil {
			return applied, readErr
		}
		sqlText := strings.TrimSpace(string(sqlBytes))
		if sqlText == "" {
			continue
		}

		tx, txErr := runner.db.BeginTx(ctx, nil)
		if txErr != nil {
			return applied, txErr
		}
		if _, execErr := tx.ExecContext(ctx, sqlText); execErr != nil {
			_ = tx.Rollback()
			return applied, fmt.Errorf("migration %s failed: %w", fileName, execErr)
		}
		if _, insertErr := tx.ExecContext(ctx,
			"INSERT INTO schema_migrations(version, applied_at) VALUES ($1, NOW())",
			version,
		); insertErr != nil {
			_ = tx.Rollback()
			return applied, insertErr
		}
		if commitErr := tx.Commit(); commitErr != nil {
			return applied, commitErr
		}

		applied = append(applied, fileName)
	}

	return applied, nil
}

func (runner *Runner) Status(ctx context.Context) ([]StatusItem, error) {
	if err := runner.ensureTable(ctx); err != nil {
		return nil, err
	}
	rows, err := runner.db.QueryContext(ctx, "SELECT version, applied_at FROM schema_migrations ORDER BY version")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := make([]StatusItem, 0)
	for rows.Next() {
		var item StatusItem
		if scanErr := rows.Scan(&item.Version, &item.AppliedAt); scanErr != nil {
			return nil, scanErr
		}
		result = append(result, item)
	}
	if rowsErr := rows.Err(); rowsErr != nil {
		return nil, rowsErr
	}
	return result, nil
}

func (runner *Runner) ensureTable(ctx context.Context) error {
	_, err := runner.db.ExecContext(ctx, `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version TEXT PRIMARY KEY,
			applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
		)
	`)
	return err
}

func (runner *Runner) hasVersion(ctx context.Context, version string) (bool, error) {
	var exists bool
	err := runner.db.QueryRowContext(ctx,
		"SELECT EXISTS(SELECT 1 FROM schema_migrations WHERE version = $1)",
		version,
	).Scan(&exists)
	if err != nil {
		return false, err
	}
	return exists, nil
}

func sortedSQLFiles(entries []fs.DirEntry) []string {
	result := make([]string, 0)
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		name := entry.Name()
		if strings.HasSuffix(strings.ToLower(name), ".sql") {
			result = append(result, name)
		}
	}
	sort.Strings(result)
	return result
}

var ErrNoMigrationsDir = errors.New("migrations directory not found")
