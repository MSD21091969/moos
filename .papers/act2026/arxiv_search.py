import arxiv
import sys
import json

def search_arxiv(query, max_results=5):
    try:
        # Construct the default API client.
        client = arxiv.Client()
        
        search = arxiv.Search(
            query = query,
            max_results = max_results,
            sort_by = arxiv.SortCriterion.Relevance
        )
        
        results = []
        for result in client.results(search):
            results.append({
                "title": result.title,
                "authors": [a.name for a in result.authors],
                "summary": result.summary,
                "pdf_url": result.pdf_url,
                "published": str(result.published)
            })
            
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        print(f"Error querying arXiv: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python arxiv_search.py <query>")
    else:
        search_arxiv(sys.argv[1])
