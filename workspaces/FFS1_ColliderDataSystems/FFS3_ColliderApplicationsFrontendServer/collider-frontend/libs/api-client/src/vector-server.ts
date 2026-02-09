import type { SearchResult } from "./types";

const DEFAULT_BASE_URL = "http://localhost:8002";

export class VectorServerClient {
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async search(
    query: string,
    collection: string = "tools",
    nResults: number = 5
  ): Promise<SearchResult[]> {
    const res = await fetch(`${this.baseUrl}/api/v1/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, collection, n_results: nResults }),
    });
    if (!res.ok) throw new Error(`Search failed: ${res.status}`);
    const data = await res.json();
    return data.results;
  }

  async embed(texts: string[]): Promise<number[][]> {
    const res = await fetch(`${this.baseUrl}/api/v1/embed`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts }),
    });
    if (!res.ok) throw new Error(`Embed failed: ${res.status}`);
    const data = await res.json();
    return data.embeddings;
  }

  async index(
    collection: string,
    ids: string[],
    documents: string[],
    metadatas?: Record<string, unknown>[]
  ): Promise<number> {
    const res = await fetch(`${this.baseUrl}/api/v1/index`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ collection, ids, documents, metadatas }),
    });
    if (!res.ok) throw new Error(`Index failed: ${res.status}`);
    const data = await res.json();
    return data.indexed;
  }
}
