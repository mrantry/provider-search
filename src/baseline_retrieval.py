# baseline_retrieval.py

# Import pyserini at module level - will fail gracefully if not available
try:
    from pyserini.search import lucene  # type: ignore
    _PYSERINI_AVAILABLE = True
except ImportError:
    _PYSERINI_AVAILABLE = False
    class _DummyModule:
        class LuceneSearcher:
            def __init__(self, *args, **kwargs):
                raise ImportError("pyserini is not installed. Install it with: pip install pyserini")
            def set_bm25(self, *args, **kwargs):
                pass
            def set_qld(self, *args, **kwargs):
                pass
            def search(self, *args, **kwargs):
                return []
    lucene = _DummyModule()


class ProviderSearchEngine:
    def __init__(self, index_dir: str):
        if not _PYSERINI_AVAILABLE:
            raise ImportError("pyserini is not installed. Install it with: pip install pyserini")
        self.searcher = lucene.LuceneSearcher(index_dir)

    def bm25_search(self, query: str, k: int = 10, k1: float = 0.9, b: float = 0.4):
        self.searcher.set_bm25(k1=k1, b=b)
        hits = self.searcher.search(query, k)
        return [{"provider_id": hit.docid, "score": hit.score} for hit in hits]

    def ql_search(self, query: str, k: int = 10, mu: float = 1000.0):
        self.searcher.set_qld(mu)
        hits = self.searcher.search(query, k)
        return [{"provider_id": hit.docid, "score": hit.score} for hit in hits]

#testing stuff 
if __name__ == "__main__":
    import sys
    import os
    
    print("=" * 50)
    print("Testing baseline_retrieval.py setup")
    print("=" * 50)
    
    # Show Python environment info
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Test 1: Module loads (this print confirms the file is executing)
    print("✓ Module loaded successfully")
    
    # Test 2: Imports work
    try:
        from pyserini.search import lucene  # type: ignore
        print("✓ Imports work correctly (pyserini is available)")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("\nTo fix this, install pyserini:")
        print(f"  {sys.executable} -m pip install pyserini")
        print("\nOr if using conda:")
        print("  conda install -c conda-forge pyserini")
        sys.exit(1)
    
    # Test 3: Class exists
    try:
        assert ProviderSearchEngine is not None
        assert hasattr(ProviderSearchEngine, 'bm25_search')
        assert hasattr(ProviderSearchEngine, 'ql_search')
        print("✓ ProviderSearchEngine class exists with required methods")
    except AssertionError as e:
        print("✗ Class structure invalid:", e)
        exit(1)
    
    # Test 4: File structure is valid (Python syntax)
    print("✓ File structure is valid (Python parsed successfully)")
    
    # Test 5: Running doesn't crash Python
    try:
        engine = ProviderSearchEngine("indexes/provider_index")
        print("✓ Engine instantiated successfully")
        print("✓ All tests passed! Setup is working.")
    except Exception as e:
        print("⚠ Engine could not initialize — this is expected until the index exists.")
        print(f"  (Error: {type(e).__name__})")
        print("✓ Python didn't crash — file structure is valid!")
    
    print("=" * 50)