---
description: 'The most comprehensive, practical, and engineer-authored performance optimization instructions for all languages, frameworks, and stacks.'
applyTo: '*'
---

# Performance Optimization Best Practices

## Introduction
Performance isn't just a buzzword—it's the difference between a product people love and one they abandon. This guide is a living collection of the most effective, real-world performance practices, covering frontend, backend, and database layers.

## General Principles
- **Measure First, Optimize Second:** Always profile and measure before optimizing. Use benchmarks, profilers, and monitoring tools.
- **Optimize for the Common Case:** Focus on optimizing code paths that are most frequently executed.
- **Avoid Premature Optimization:** Write clear, maintainable code first; optimize only when necessary.
- **Minimize Resource Usage:** Use memory, CPU, network, and disk resources efficiently.
- **Prefer Simplicity:** Simple algorithms and data structures are often faster and easier to optimize.
- **Document Performance Assumptions:** Clearly comment on any code that is performance-critical.
- **Understand the Platform:** Know the performance characteristics of your language, framework, and runtime.
- **Automate Performance Testing:** Integrate performance tests and benchmarks into your CI/CD pipeline.
- **Set Performance Budgets:** Define acceptable limits for load time, memory usage, API latency, etc.

## Frontend Performance

### Rendering and DOM
- **Minimize DOM Manipulations:** Batch updates where possible.
- **Virtual DOM Frameworks:** Use React, Vue, or similar efficiently—avoid unnecessary re-renders.
- **Keys in Lists:** Always use stable keys in lists.
- **Avoid Inline Styles:** Prefer CSS classes.
- **CSS Animations:** Use CSS transitions/animations over JavaScript.
- **Defer Non-Critical Rendering:** Use `requestIdleCallback`.

### Asset Optimization
- **Image Compression:** Use tools like ImageOptim, Squoosh, or TinyPNG. Prefer WebP/AVIF.
- **SVGs for Icons:** SVGs scale well and are often smaller.
- **Minification and Bundling:** Use Webpack, Rollup, or esbuild. Enable tree-shaking.
- **Cache Headers:** Set long-lived cache headers for static assets.
- **Lazy Loading:** Use `loading="lazy"` for images and dynamic imports for JS.
- **Font Optimization:** Subset fonts and use `font-display: swap`.

### Network Optimization
- **Reduce HTTP Requests:** Combine files, use sprites.
- **HTTP/2 and HTTP/3:** Enable for multiplexing.
- **Client-Side Caching:** Use Service Workers, IndexedDB, localStorage.
- **CDNs:** Serve static assets from a CDN.
- **Defer/Async Scripts:** Use `defer` or `async`.
- **Preload and Prefetch:** Use `<link rel="preload">` and `<link rel="prefetch">`.

### JavaScript Performance
- **Avoid Blocking the Main Thread:** Offload heavy computation to Web Workers.
- **Debounce/Throttle Events:** Limit handler frequency for scroll/resize/input.
- **Memory Leaks:** Clean up event listeners and DOM references.
- **Efficient Data Structures:** Use Maps/Sets, TypedArrays.
- **Avoid Global Variables:** Globals can cause leaks.
- **Avoid Deep Object Cloning:** Use shallow copies where possible.

### Framework-Specific Tips
- **React:** Use `React.memo`, `useMemo`, `useCallback`. Split large components.
- **Angular:** Use OnPush change detection. Use `trackBy`.
- **Vue:** Use computed properties. Use `v-show` vs `v-if` appropriately.

## Backend Performance

### Algorithm and Data Structure Optimization
- **Choose the Right Data Structure:** Arrays, hash maps, trees, etc.
- **Efficient Algorithms:** Binary search, quicksort, hash-based algorithms.
- **Avoid O(n^2) or Worse:** Profile nested loops.
- **Batch Processing:** Process data in batches.
- **Streaming:** Use streaming APIs for large data sets.

### Concurrency and Parallelism
- **Asynchronous I/O:** Use async/await, callbacks.
- **Thread/Worker Pools:** Manage concurrency.
- **Avoid Race Conditions:** Use locks, semaphores.
- **Bulk Operations:** Batch network/database calls.
- **Backpressure:** Implement backpressure in queues.

### Caching
- **Cache Expensive Computations:** Use Redis, Memcached.
- **Cache Invalidation:** Use TTL, event-based invalidation.
- **Distributed Caching:** Be aware of consistency.
- **Cache Stampede Protection:** Use locks or request coalescing.

### API and Network
- **Minimize Payloads:** Use JSON, compress responses (gzip, Brotli).
- **Pagination:** Always paginate large result sets.
- **Rate Limiting:** Protect APIs.
- **Connection Pooling:** Reuse connections.
- **Protocol Choice:** HTTP/2, gRPC, WebSockets.

### Logging and Monitoring
- **Minimize Logging in Hot Paths:** Avoid excessive logging.
- **Structured Logging:** Use JSON logs.
- **Monitor Everything:** Latency, throughput, error rates.
- **Alerting:** Set up alerts for regressions.

### Language/Framework-Specific Tips
- **Node.js:** Use async APIs, clustering, worker threads.
- **Python:** Use built-in data structures, `multiprocessing`, `asyncio`.
- **Java:** Use efficient collections, thread pools, tune JVM.
- **.NET:** Use `async/await`, `Span<T>`, `Memory<T>`.

## Database Performance

### Query Optimization
- **Indexes:** Use indexes on frequently queried columns.
- **Avoid SELECT *:** Select only needed columns.
- **Parameterized Queries:** Prevent injection and improve caching.
- **Query Plans:** Analyze with `EXPLAIN`.
- **Avoid N+1 Queries:** Use joins or batch queries.
- **Limit Result Sets:** Use `LIMIT`/`OFFSET`.

### Schema Design
- **Normalization:** Normalize to reduce redundancy (denormalize for read-heavy if needed).
- **Data Types:** Use efficient data types.
- **Partitioning:** Partition large tables.
- **Archiving:** Archive old data.
- **Foreign Keys:** Use for integrity.

### Transactions
- **Short Transactions:** Reduce lock contention.
- **Isolation Levels:** Use lowest necessary level.
- **Avoid Long-Running Transactions:** Prevent deadlocks.

### Caching and Replication
- **Read Replicas:** Scale read-heavy workloads.
- **Cache Query Results:** Use Redis/Memcached.
- **Sharding:** Distribute data.

## Code Review Checklist for Performance
- [ ] Are there any obvious algorithmic inefficiencies (O(n^2))?
- [ ] Are data structures appropriate?
- [ ] Are there unnecessary computations?
- [ ] Is caching used appropriately?
- [ ] Are database queries optimized (indexes, no N+1)?
- [ ] Are large payloads paginated/streamed?
- [ ] Are there memory leaks?
- [ ] Are network requests minimized/batched?
- [ ] Are assets optimized?
- [ ] Are there blocking operations in hot paths?
- [ ] Is logging minimized in hot paths?

## Practical Examples

### Debouncing User Input (JS)
```javascript
let timeout;
input.addEventListener('input', (e) => {
  clearTimeout(timeout);
  timeout = setTimeout(() => { fetch(...) }, 300);
});
```

### Efficient SQL Query
```sql
-- GOOD
SELECT id, name FROM users WHERE email = 'user@example.com';
```

### Caching (Python)
```python
from functools import lru_cache
@lru_cache(maxsize=128)
def expensive_function(x): ...
```

### Lazy Loading Images (HTML)
```html
<img src="large.jpg" loading="lazy" />
```

### Async I/O (Node.js)
```javascript
fs.readFile('file.txt', (err, data) => { ... });
```
