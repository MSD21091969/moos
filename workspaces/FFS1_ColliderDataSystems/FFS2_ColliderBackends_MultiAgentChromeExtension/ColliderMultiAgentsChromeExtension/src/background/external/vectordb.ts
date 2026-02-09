const VECTORDB_URL = "http://localhost:8002";

export interface SearchResult {
  id: string;
  document: string;
  distance: number;
  metadata: Record<string, unknown>;
}

export async function searchTools(
  query: string,
  collection: string = "tools",
  nResults: number = 5
): Promise<SearchResult[]> {
  const response = await fetch(`${VECTORDB_URL}/api/v1/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, collection, n_results: nResults }),
  });
  if (!response.ok)
    throw new Error(`Search failed: ${response.status}`);
  const data = await response.json();
  return data.results;
}

export async function embedTexts(
  texts: string[]
): Promise<number[][]> {
  const response = await fetch(`${VECTORDB_URL}/api/v1/embed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texts }),
  });
  if (!response.ok) throw new Error(`Embed failed: ${response.status}`);
  const data = await response.json();
  return data.embeddings;
}

export async function indexDocuments(
  collection: string,
  ids: string[],
  documents: string[],
  metadatas?: Record<string, unknown>[]
): Promise<number> {
  const response = await fetch(`${VECTORDB_URL}/api/v1/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ collection, ids, documents, metadatas }),
  });
  if (!response.ok) throw new Error(`Index failed: ${response.status}`);
  const data = await response.json();
  return data.indexed;
}
