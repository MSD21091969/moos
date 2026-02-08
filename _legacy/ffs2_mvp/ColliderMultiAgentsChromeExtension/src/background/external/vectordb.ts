/**
 * VectorDB Server client
 */

const VECTORDB_URL = "http://localhost:8002"

export interface SearchResult {
  id: string
  document: string
  metadata: Record<string, unknown>
  distance: number
}

/**
 * Semantic search
 */
export async function search(query: string, nResults = 10): Promise<SearchResult[]> {
  const res = await fetch(`${VECTORDB_URL}/api/v1/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, n_results: nResults }),
  })
  if (!res.ok) throw new Error(`Search failed: ${res.status}`)
  const data = await res.json()
  return data.results
}

/**
 * Embed and index a document
 */
export async function embed(
  text: string,
  documentId: string,
  metadata?: Record<string, unknown>
): Promise<{ id: string; status: string }> {
  const res = await fetch(`${VECTORDB_URL}/api/v1/embed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, document_id: documentId, metadata: metadata || {} }),
  })
  if (!res.ok) throw new Error(`Embed failed: ${res.status}`)
  return res.json()
}

/**
 * Bulk index documents
 */
export async function index(
  documents: { id: string; text: string; metadata?: Record<string, unknown> }[]
): Promise<{ count: number; status: string }> {
  const res = await fetch(`${VECTORDB_URL}/api/v1/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ documents }),
  })
  if (!res.ok) throw new Error(`Index failed: ${res.status}`)
  return res.json()
}
