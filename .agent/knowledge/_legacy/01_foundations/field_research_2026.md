# Field Research 2026

## Status

Placeholder — empirical grounding for the categorical model will be documented
here as runtime observations from the MOOS kernel accumulate.

## Observation Categories

- **Morphism frequency distribution**: Which of ADD/LINK/MUTATE/UNLINK dominates
  in production workloads?
- **Edge density (k/n²)**: What fraction of potential edges become actual edges?
  How does this ratio change as the graph grows?
- **Traversal depth**: Average and max path lengths in production queries.
  Indicator of effective graph diameter.
- **Replay cost**: Time to reconstruct `state_payload` from `morphism_log` for
  containers of varying ages. Threshold for materialization trigger.
- **Hypergraph fanout**: Average number of parallel edges between node pairs.
  Indicator of graph version density.

## Method

All observations will be drawn from Prometheus metrics exposed at `/metrics` on
the MOOS kernel, supplemented by direct SQL queries against the morphism_log.