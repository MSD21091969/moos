# instances

Place your instance `.json` files here.

Each file is processed by the hydration pipeline on kernel boot (`--hydrate` flag).  
Files must conform to `../superset/schema.json`.

## Example

```json
{
  "nodes": [
    {
      "urn": "urn:myorg:my-service",
      "label": "My Service",
      "kind": "Container",
      "stratum": 2,
      "payload": {}
    }
  ],
  "wires": []
}
```

See `platform/kernel/examples/explorer-demo.materialize.json` in the repo for a full working example.
