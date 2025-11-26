# baseline_retrieval.py

from pyserini.search import lucene
from pyserini.index.lucene import LuceneIndexer
import json
import os
import sys
from pathlib import Path


class ProviderSearchEngine:
    def __init__(self, index_dir: str):
        self.index_dir = index_dir
        self.searcher = lucene.LuceneSearcher(index_dir)

    def bm25_search(self, query: str, k: int = 100, k1: float = 0.9, b: float = 0.4):
        """Perform BM25 search using pyserini."""
        self.searcher.set_bm25(k1=k1, b=b)
        hits = self.searcher.search(query, k)
        return [{"provider_id": hit.docid, "score": hit.score} for hit in hits]

    def ql_dirichlet_search(self, query: str, k: int = 100, mu: float = 1000.0):
        """Perform Query Likelihood search with Dirichlet smoothing."""
        self.searcher.set_qld(mu)
        hits = self.searcher.search(query, k)
        return [{"provider_id": hit.docid, "score": hit.score} for hit in hits]


def build_index_from_jsonl(jsonl_path: str, index_dir: str):
    """Build a pyserini index from a JSONL file."""
    print(f"Building index from {jsonl_path}...")
    print("This may take a few minutes for large datasets...")
    
    os.makedirs(index_dir, exist_ok=True)
    
    indexer = LuceneIndexer(index_dir, threads=4)
    
    doc_count = 0
    batch = []
    batch_size = 1000
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 10000 == 0:
                print(f"  Processed {line_num:,} documents...")
            
            try:
                doc = json.loads(line.strip())
                
                doc_id = str(doc.get('NPI', f'doc_{line_num}'))
                
                if 'search_text' in doc and doc['search_text']:
                    contents = doc['search_text']
                else:
                    parts = []
                    if doc.get('provider_name'):
                        parts.append(doc['provider_name'])
                    if doc.get('specialty_readable'):
                        parts.append(doc['specialty_readable'])
                    if doc.get('Provider Business Practice Location Address City Name'):
                        parts.append(doc['Provider Business Practice Location Address City Name'])
                    if doc.get('Provider Business Practice Location Address State Name'):
                        parts.append(doc['Provider Business Practice Location Address State Name'])
                    contents = ' | '.join(parts)
                
                pyserini_doc = {
                    "id": doc_id,
                    "contents": contents
                }
                
                batch.append(pyserini_doc)
                doc_count += 1
                
                if len(batch) >= batch_size:
                    indexer.add_batch_dict(batch)
                    batch = []
                
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON on line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Error processing line {line_num}: {e}")
                continue
    
    if batch:
        indexer.add_batch_dict(batch)
    
    indexer.close()
    print(f"✓ Index built successfully! Indexed {doc_count:,} documents.")
    print(f"  Index location: {index_dir}")


def ensure_index_exists(index_dir: str, data_dir: str = None):
    """Check if index exists, build it if it doesn't."""
    if os.path.exists(index_dir) and os.path.isdir(index_dir):
        index_files = list(Path(index_dir).glob('*'))
        if index_files:
            return True
    
    if data_dir is None:
        script_dir = Path(__file__).parent.parent
        data_dir = script_dir / "data"
    
    jsonl_path = os.path.join(data_dir, "providers_illinois.jsonl")
    
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(
            f"Index not found at {index_dir} and data file not found at {jsonl_path}.\n"
            f"Please ensure the data file exists or the index is already built."
        )
    
    print(f"Index not found. Building index from {jsonl_path}...")
    build_index_from_jsonl(jsonl_path, index_dir)
    return True


def get_full_documents(provider_ids: list, jsonl_path: str):
    """Retrieve full document data for given provider IDs from JSONL file."""
    provider_ids_set = set(str(pid) for pid in provider_ids)
    documents = {}
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                doc = json.loads(line.strip())
                npi = str(doc.get('NPI', ''))
                if npi in provider_ids_set:
                    documents[npi] = doc
                    # Stop early if we found all documents
                    if len(documents) == len(provider_ids_set):
                        break
            except json.JSONDecodeError:
                continue
    
    return documents


def write_results_json(results: list, query: str, method: str, output_path: str):
    """Write retrieval results to JSON file."""
    output_data = {
        "query": query,
        "method": method,
        "num_results": len(results),
        "results": [
            {
                "rank": i + 1,
                "provider_id": result["provider_id"],
                "score": result["score"]
            }
            for i, result in enumerate(results)
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Results written to {output_path}")
    print(f"  Method: {method}, Results: {len(results)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Provider Search - Baseline Retrieval')
    parser.add_argument('query', nargs='*', help='Search query')
    parser.add_argument('--method', choices=['bm25', 'ql_dirichlet'], default='bm25',
                       help='Retrieval method (default: bm25)')
    parser.add_argument('--k', type=int, default=100,
                       help='Number of results to retrieve (default: 100)')
    
    args = parser.parse_args()
    
    if args.query:
        query = " ".join(args.query)
        method = args.method
        k = args.k
        
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent
        default_index_dir = repo_root / "indexes" / "provider_index"
        index_dir = os.environ.get("PROVIDER_INDEX_DIR", str(default_index_dir))
        output_path = repo_root / "output.json"
        
        try:
            ensure_index_exists(index_dir)
            
            engine = ProviderSearchEngine(index_dir)
            
            print(f"Searching for: '{query}'")
            print(f"Method: {method.upper()}, Retrieving top {k} results")
            print("=" * 50)
            
            # Perform retrieval
            if method == 'bm25':
                results = engine.bm25_search(query, k=k)
            elif method == 'ql_dirichlet':
                results = engine.ql_dirichlet_search(query, k=k)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            if results:
                # Write full results to JSON
                write_results_json(results, query, method, str(output_path))
                
                # Display top 5 in console
                script_dir = Path(__file__).parent
                jsonl_path = script_dir.parent / "data" / "providers_illinois.jsonl"
                top_5_results = results[:5]
                full_docs = get_full_documents([r['provider_id'] for r in top_5_results], str(jsonl_path))
                
                print(f"\nTop 5 results (showing {len(top_5_results)} of {len(results)}):\n")
                for i, result in enumerate(top_5_results, 1):
                    provider_id = result['provider_id']
                    doc = full_docs.get(provider_id, {})
                    
                    print(f"{i}. Provider ID: {provider_id}, Score: {result['score']:.4f}")
                    if doc:
                        search_text = doc.get('search_text', 'N/A')
                        print(f"   Search Text: {search_text}")
                    print()
            else:
                print("No results found.")
                # Still write empty results to JSON
                write_results_json([], query, method, str(output_path))
            
        except ImportError as e:
            print(f"Error: {e}")
            print("\nTo fix this, install pyserini:")
            print(f"  {sys.executable} -m pip install pyserini")
            sys.exit(1)
        except Exception as e:
            print(f"Error during search: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("=" * 50)
        print("Provider Search - Baseline Retrieval")
        print("=" * 50)
        print("\nUsage: python baseline_retrieval.py '<search query>' [--method METHOD] [--k K]")
        print("\nExamples:")
        print("  python baseline_retrieval.py 'cardiologist in Chicago'")
        print("  python baseline_retrieval.py 'cardiologist in Chicago' --method ql_dirichlet")
        print("  python baseline_retrieval.py 'pediatrician' --method bm25 --k 50")
        print("\nMethods:")
        print("  bm25        - BM25 retrieval (default)")
        print("  ql_dirichlet - Query Likelihood with Dirichlet smoothing")
        print("\nOptions:")
        print("  --k K       - Number of results to retrieve (default: 100)")
        print("\nResults are written to output.json in the repository root.")
        print("Top 5 results are displayed in the console.")
        print("\nThe index will be built automatically on first run if it doesn't exist.")
        print("=" * 50)
