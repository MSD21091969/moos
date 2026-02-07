"""Query Logfire for full /tools/available response details."""

from logfire.query_client import LogfireQueryClient
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load credentials
creds_path = Path('.logfire/logfire_credentials.json')
creds = json.loads(creds_path.read_text()) if creds_path.exists() else {}
read_token = os.getenv('LOGFIRE_READ_TOKEN') or creds.get('read_token') or creds.get('token')

# Query with ALL fields to see response bodies
sql = """
SELECT *
FROM records
WHERE span_name = 'GET /tools/available'
  AND http_response_status_code = 200
ORDER BY start_timestamp DESC
LIMIT 3
"""

min_timestamp = datetime.now(timezone.utc) - timedelta(hours=6)
client = LogfireQueryClient(read_token=read_token)

with client:
    results = client.query_json_rows(sql=sql, min_timestamp=min_timestamp)

# Save to file
output_file = Path('tools_available_full.json')
output_file.write_text(json.dumps(results['rows'], indent=2))
print(f"Saved {len(results['rows'])} records to {output_file}")

# Print first record's keys to see what fields are available
if results['rows']:
    print(f"\nAvailable fields: {list(results['rows'][0].keys())}")
