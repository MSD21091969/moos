package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/collider/moos/internal/migrate"
)

func main() {
	databaseURL := flag.String("database-url", os.Getenv("DATABASE_URL"), "PostgreSQL connection string")
	dir := flag.String("dir", "./migrations", "Directory containing .sql migrations")
	action := flag.String("action", "up", "Migration action: up|status")
	flag.Parse()

	if *databaseURL == "" {
		log.Fatal("database-url is required (or set DATABASE_URL)")
	}

	runner, err := migrate.NewRunner(*databaseURL, *dir)
	if err != nil {
		log.Fatalf("create migration runner: %v", err)
	}
	defer runner.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	switch *action {
	case "up":
		applied, runErr := runner.Up(ctx)
		if runErr != nil {
			log.Fatalf("apply migrations: %v", runErr)
		}
		fmt.Printf("Applied %d migration(s)\n", len(applied))
		for _, name := range applied {
			fmt.Printf(" - %s\n", name)
		}
	case "status":
		items, statusErr := runner.Status(ctx)
		if statusErr != nil {
			log.Fatalf("migration status: %v", statusErr)
		}
		if len(items) == 0 {
			fmt.Println("No migrations recorded")
			return
		}
		for _, item := range items {
			fmt.Printf("%s | %s\n", item.Version, item.AppliedAt.Format(time.RFC3339))
		}
	default:
		log.Fatalf("unsupported action: %s", *action)
	}
}
