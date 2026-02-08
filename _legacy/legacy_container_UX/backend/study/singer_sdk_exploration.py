"""
Study file: Exploring Singer SDK concepts
Table Item: Singer SDK for ETL pipelines

This file helps you explore Singer's tap/target architecture.
We don't have singer-sdk installed yet, but this shows you what to explore once it is.

Usage:
1. pip install singer-sdk
2. Open this file
3. Explore with IntelliSense
"""

# Uncomment after installing singer-sdk:
# from singer_sdk import Tap, Target, Stream
# from singer_sdk.typing import PropertiesList, Property, StringType, IntegerType, DateTimeType
# from singer_sdk.helpers.jsonpath import extract_jsonpath


# Study: Tap - Extract data from sources
def explore_tap_creation():
    """How do we create a custom tap?"""

    # Basic tap structure
    # class MyCustomTap(Tap):
    #     name = "tap-custom"
    #
    #     def discover_streams(self):
    #         """Returns list of streams this tap can extract"""
    #         return [
    #             CustomersStream(self),
    #             OrdersStream(self)
    #         ]
    pass


# Study: Stream - Data flow abstraction
def explore_stream_creation():
    """How do we define a stream?"""

    # Basic stream
    # class CustomersStream(Stream):
    #     name = "customers"
    #     primary_keys = ["id"]
    #     replication_key = "updated_at"
    #
    #     schema = PropertiesList(
    #         Property("id", StringType, required=True),
    #         Property("name", StringType),
    #         Property("email", StringType),
    #         Property("created_at", DateTimeType)
    #     ).to_dict()
    #
    #     def get_records(self, context):
    #         """Yield records from the source"""
    #         for record in self.fetch_from_api():
    #             yield record
    pass


# Study: Target - Load data to destinations
def explore_target_creation():
    """How do we create a custom target?"""

    # Basic target structure
    # class MyCustomTarget(Target):
    #     name = "target-custom"
    #
    #     def get_sink(self, stream_name: str):
    #         """Returns a sink for writing to destination"""
    #         return CustomSink(
    #             target=self,
    #             stream_name=stream_name
    #         )
    pass


# Study: Sink - Where data lands
def explore_sink_creation():
    """How do we write to a destination?"""

    # Basic sink
    # class CustomSink(Sink):
    #     def process_batch(self, context: dict):
    #         """Process a batch of records"""
    #         records = context["records"]
    #         # Write to destination
    #         self.write_to_database(records)
    pass


# Study: Singer messages - The protocol
def explore_singer_protocol():
    """What messages does Singer use?"""

    import json
    from datetime import datetime

    # SCHEMA message
    schema_message = {
        "type": "SCHEMA",
        "stream": "customers",
        "schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string"},
            },
        },
        "key_properties": ["id"],
    }

    # RECORD message
    record_message = {
        "type": "RECORD",
        "stream": "customers",
        "record": {"id": "cust_123", "name": "John Doe", "email": "john@example.com"},
        "time_extracted": datetime.utcnow().isoformat(),
    }

    # STATE message
    state_message = {"type": "STATE", "value": {"customers": {"last_sync": "2024-01-01T00:00:00Z"}}}

    # Taps emit these to STDOUT, targets consume from STDIN
    print(json.dumps(schema_message))
    print(json.dumps(record_message))
    print(json.dumps(state_message))


# Study: Configuration patterns
def explore_singer_config():
    """How do taps/targets get configured?"""

    # Tap config.json
    tap_config = {
        "api_url": "https://api.example.com",
        "api_key": "secret",
        "start_date": "2024-01-01T00:00:00Z",
        "streams": ["customers", "orders"],
    }

    # Target config.json (like target-bigquery)
    target_config = {
        "project": "my-project",
        "dataset": "my_dataset",
        "method": "storage_write_api",
        "denormalized": True,
        "batch_size": 500,
        "column_name_transforms": {"snake_case": True},
    }

    # How does this relate to our sessions?
    # Each session could be a stream!


# Study: Catalog - Schema discovery
def explore_singer_catalog():
    """What's a Singer catalog?"""

    catalog = {
        "streams": [
            {
                "tap_stream_id": "customers",
                "stream": "customers",
                "schema": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
                },
                "metadata": [
                    {
                        "breadcrumb": [],
                        "metadata": {
                            "selected": True,
                            "replication-method": "INCREMENTAL",
                            "replication-key": "updated_at",
                        },
                    }
                ],
            }
        ]
    }

    # Taps generate catalogs during discovery
    # Users select which streams to sync


# Study: State management for incremental sync
def explore_singer_state():
    """How does state tracking work?"""

    # State after first sync
    initial_state = {
        "bookmarks": {"customers": {"updated_at": "2024-01-01T00:00:00Z", "version": 1}}
    }

    # Next sync only processes records after this timestamp
    # Enables incremental data extraction


# Study: How this connects to your sessions
def connect_to_sessions():
    """Mental model: Sessions as Singer streams"""

    # Your session could be a Singer tap!
    class SessionTap:
        """
        Each session is a stream of messages.
        The table metaphor maps perfectly:

        - Table = Stream
        - Items on table = Records
        - Studying = Processing
        - Clearing = Resetting state
        """

        def emit_record(self, stream_name: str, record: dict):
            """Add an item to the table"""
            import json
            from datetime import datetime

            print(
                json.dumps(
                    {
                        "type": "RECORD",
                        "stream": stream_name,
                        "record": record,
                        "time_extracted": datetime.utcnow().isoformat(),
                    }
                )
            )

        def emit_schema(self, stream_name: str, schema: dict):
            """Define what can go on this table"""
            import json

            print(
                json.dumps(
                    {
                        "type": "SCHEMA",
                        "stream": stream_name,
                        "schema": schema,
                        "key_properties": ["id"],
                    }
                )
            )

        def emit_state(self, state: dict):
            """Save the table's current state"""
            import json

            print(json.dumps({"type": "STATE", "value": state}))


# Study: Meltano integration
def explore_meltano():
    """How does Meltano orchestrate Singer pipelines?"""

    # meltano.yml structure
    meltano_config = """
    project: my-tiny-data-collider
    
    plugins:
      extractors:
      - name: tap-custom
        config:
          api_url: https://api.example.com
      
      loaders:
      - name: target-bigquery
        config:
          project: analytics
          dataset: raw_data
    
    schedules:
    - name: daily-sync
      extractor: tap-custom
      loader: target-bigquery
      interval: '@daily'
    """

    # Commands:
    # meltano elt tap-custom target-bigquery
    # meltano run tap-custom target-bigquery


if __name__ == "__main__":
    print("Singer SDK Study File")
    print("=" * 50)
    print("Install singer-sdk to explore:")
    print("  pip install singer-sdk")
    print()
    print("Then uncomment the imports and start exploring!")
    print()
    print("Key concepts:")
    print("- Tap: Extract from source")
    print("- Target: Load to destination")
    print("- Stream: Data flow unit")
    print("- Catalog: Schema discovery")
    print("- State: Incremental sync")
    print()
    print("Your sessions could be Singer streams!")
