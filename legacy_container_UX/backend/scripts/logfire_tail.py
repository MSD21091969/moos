"""Utility script for inspecting recent Logfire records via the query API."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from logfire.query_client import LogfireQueryClient, QueryExecutionError, QueryRequestError

DEFAULT_LOOKBACK_HOURS = 6.0
DEFAULT_LIMIT = 100
DEFAULT_MIN_LEVEL = "warn"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch recent Logfire records for debugging.")
    parser.add_argument(
        "--hours",
        type=float,
        default=DEFAULT_LOOKBACK_HOURS,
        help="Lookback window in hours (default: 6).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Maximum number of rows to retrieve (default: 100).",
    )
    parser.add_argument(
        "--min-level",
        choices=["debug", "info", "notice", "warn", "error", "fatal"],
        default=DEFAULT_MIN_LEVEL,
        help="Minimum log level to include (default: warn).",
    )
    parser.add_argument(
        "--service",
        dest="service_name",
        help="Optional service_name filter.",
    )
    parser.add_argument(
        "--message",
        dest="message_contains",
        help="Optional case-insensitive substring match against message field.",
    )
    parser.add_argument(
        "--trace-id",
        dest="trace_id",
        help="Optional trace identifier filter.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON rows instead of formatted text.",
    )
    return parser.parse_args()


def load_credentials() -> dict[str, Any]:
    creds_path = Path(".logfire/logfire_credentials.json")
    if not creds_path.exists():
        return {}

    try:
        return json.loads(creds_path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse {creds_path}: {exc}") from exc


def load_read_token(creds: dict[str, Any]) -> str:
    env_token = os.getenv("LOGFIRE_READ_TOKEN")
    if env_token:
        return env_token.strip()

    file_token = creds.get("read_token")
    if file_token:
        return str(file_token).strip()

    # Fallback to 'token' field if read_token not present
    token = creds.get("token")
    if token:
        return str(token).strip()

    raise SystemExit(
        "Logfire read token not configured. Set LOGFIRE_READ_TOKEN or add 'read_token'/'token' to .logfire/logfire_credentials.json."
    )


def load_api_url(creds: dict[str, Any]) -> str | None:
    env_url = os.getenv("LOGFIRE_API_URL")
    if env_url:
        return env_url.rstrip("/")

    file_url = creds.get("logfire_api_url")
    if file_url:
        return str(file_url).rstrip("/")

    return None


def escape_literal(value: str) -> str:
    return value.replace("'", "''")


def escape_like(value: str) -> str:
    escaped = value.replace("'", "''")
    return escaped.replace("%", "%%")


def build_sql(
    *,
    limit: int,
    min_level: str,
    service_name: str | None,
    message_contains: str | None,
    trace_id: str | None,
) -> str:
    clauses: list[str] = []

    if min_level:
        clauses.append(f"level >= '{escape_literal(min_level.lower())}'")

    if service_name:
        clauses.append(f"service_name = '{escape_literal(service_name)}'")

    if message_contains:
        clauses.append(f"message ILIKE '%{escape_like(message_contains)}%'")

    if trace_id:
        clauses.append(f"trace_id = '{escape_literal(trace_id)}'")

    where_clause = ""
    if clauses:
        where_clause = "WHERE " + " AND ".join(clauses)

    sql = f"""
SELECT
  start_timestamp,
  level_name(level) AS level,
  service_name,
  span_name,
  message,
  http_response_status_code,
  exception_type,
  exception_message,
  trace_id,
  span_id
FROM records
{where_clause}
ORDER BY start_timestamp DESC
LIMIT {limit}
"""
    return "\n".join(line.rstrip() for line in sql.strip().splitlines())


def render_rows(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        ts = row.get("start_timestamp", "?")
        level = str(row.get("level", "")).upper()
        service = row.get("service_name") or "-"
        span = row.get("span_name") or "-"
        status = row.get("http_response_status_code")
        message = row.get("message") or ""
        trace_id = row.get("trace_id") or "-"
        span_id = row.get("span_id") or "-"
        exception_type = row.get("exception_type")
        exception_message = row.get("exception_message")

        line = f"{ts} [{level}] {service} {span} :: {message}"
        if status:
            line += f" (status={status})"
        if exception_type:
            line += f" | {exception_type}: {exception_message or ''}"
        line += f" | trace={trace_id} span={span_id}"
        print(line)


def main() -> None:
    args = parse_args()
    credentials = load_credentials()
    read_token = load_read_token(credentials)
    api_url = load_api_url(credentials)

    lookback = timedelta(hours=args.hours)
    min_timestamp = datetime.now(timezone.utc) - lookback
    sql = build_sql(
        limit=args.limit,
        min_level=args.min_level,
        service_name=args.service_name,
        message_contains=args.message_contains,
        trace_id=args.trace_id,
    )

    try:
        if api_url:
            client = LogfireQueryClient(read_token=read_token, base_url=api_url)
        else:
            client = LogfireQueryClient(read_token=read_token)

        with client:
            results = client.query_json_rows(sql=sql, min_timestamp=min_timestamp)
    except QueryRequestError as exc:
        raise SystemExit(f"Logfire rejected the query: {exc}") from exc
    except QueryExecutionError as exc:
        raise SystemExit(f"Logfire failed to execute the query: {exc}") from exc

    rows = results.get("rows", [])
    if not rows:
        print("No records found for the requested filters.")
        return

    if args.json:
        print(json.dumps(rows, indent=2))
        return

    render_rows(rows)


if __name__ == "__main__":
    main()
