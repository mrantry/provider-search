"""Flask API for persona-based provider search."""

from pathlib import Path
import sys

# Configure Java classpath before importing pyserini
import jnius_config
if not jnius_config.vm_running:
    possible_paths = [
        Path(__file__).parent.parent / "provider-search" / "lib" / "python3.13" / "site-packages" / "pyserini" / "resources" / "jars",
        Path.home() / ".local" / "lib" / "python3.13" / "site-packages" / "pyserini" / "resources" / "jars",
        Path("/opt/anaconda3/lib/python3.13/site-packages/pyserini/resources/jars"),
    ]

    for jar_dir in possible_paths:
        if jar_dir.exists():
            jar_files = list(jar_dir.glob("anserini-*.jar"))
            if jar_files:
                jnius_config.add_classpath(str(jar_files[0]))
                break

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
from baseline_retrieval import ProviderSearchEngine, ensure_index_exists
from reranker import PersonaReranker, load_provider_data

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INDEX_DIR = PROJECT_ROOT / "indexes" / "provider_index"
CONFIG_DIR = PROJECT_ROOT / "config"
JSONL_PATH = DATA_DIR / "providers_illinois.jsonl"
SWAGGER_FILE = PROJECT_ROOT / "swagger.yaml"

swagger_config = {
    "headers": [],
    "specs": [{
        "endpoint": 'apispec',
        "route": '/apispec.json',
        "rule_filter": lambda rule: True,
        "model_filter": lambda tag: True,
    }],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger = Swagger(app, config=swagger_config, template_file=str(SWAGGER_FILE))

search_engine = None
reranker = None


def init_services():
    """Initialize search engine and reranker."""
    global search_engine, reranker

    print("Initializing provider search service...")
    ensure_index_exists(str(INDEX_DIR), str(DATA_DIR))
    search_engine = ProviderSearchEngine(str(INDEX_DIR))
    reranker = PersonaReranker(config_dir=str(CONFIG_DIR))
    print(f"Service ready with {len(reranker.get_available_personas())} personas\n")


@app.route('/', methods=['GET'])
def home():
    """API information endpoint."""
    return jsonify({
        'service': 'Provider Search API',
        'version': '1.0.0',
        'endpoints': {
            'GET /': 'API information',
            'GET /health': 'Health check',
            'GET /personas': 'List available personas',
            'GET /personas/<persona_id>': 'Get persona details',
            'POST /search': 'Search providers with persona re-ranking'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'search_engine': search_engine is not None,
        'reranker': reranker is not None,
        'personas_available': len(reranker.get_available_personas()) if reranker else 0
    })


@app.route('/personas', methods=['GET'])
def list_personas():
    """List all available personas."""
    if not reranker:
        return jsonify({'error': 'Reranker not initialized'}), 500

    personas_info = [reranker.get_persona_info(pid)
                     for pid in reranker.get_available_personas()]

    return jsonify({
        'personas': personas_info,
        'count': len(personas_info)
    })


@app.route('/personas/<persona_id>', methods=['GET'])
def get_persona(persona_id):
    """Get details about a specific persona."""
    if not reranker:
        return jsonify({'error': 'Reranker not initialized'}), 500

    info = reranker.get_persona_info(persona_id)
    if not info:
        return jsonify({'error': f'Persona not found: {persona_id}'}), 404

    return jsonify(info)


@app.route('/search', methods=['POST'])
def search():
    """
    Search for providers with optional persona-based re-ranking.
    See swagger.yaml for full API documentation.
    """
    if not search_engine:
        return jsonify({'error': 'Search engine not initialized'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    query = data.get('query')
    if not query:
        return jsonify({'error': 'Missing required field: query'}), 400

    persona_id = data.get('persona')
    method = data.get('method', 'bm25')
    k = data.get('k', 20)
    alpha = data.get('alpha', 0.5)
    include_features = data.get('include_features', False)

    # Validate parameters
    if method not in ['bm25', 'ql_dirichlet']:
        return jsonify({'error': 'Invalid method. Must be "bm25" or "ql_dirichlet"'}), 400

    if not isinstance(k, int) or k < 1 or k > 100:
        return jsonify({'error': 'k must be an integer between 1 and 100'}), 400

    if not isinstance(alpha, (int, float)) or alpha < 0 or alpha > 1:
        return jsonify({'error': 'alpha must be a number between 0 and 1'}), 400

    if persona_id and persona_id not in reranker.get_available_personas():
        return jsonify({
            'error': f'Invalid persona: {persona_id}',
            'available_personas': reranker.get_available_personas()
        }), 400

    try:
        # Baseline search
        if method == 'bm25':
            baseline_results = search_engine.bm25_search(query, k=100)
        else:
            baseline_results = search_engine.ql_dirichlet_search(query, k=100)

        if not baseline_results:
            return jsonify({
                'query': query,
                'method': method,
                'persona': persona_id,
                'num_results': 0,
                'results': []
            })

        provider_ids = [r['provider_id'] for r in baseline_results]
        provider_data = load_provider_data(str(JSONL_PATH), provider_ids)

        # Apply persona re-ranking if requested
        if persona_id and reranker:
            results = reranker.rerank(baseline_results, provider_data, persona_id, alpha=alpha)
        else:
            results = []
            for i, baseline_result in enumerate(baseline_results):
                provider_id = str(baseline_result['provider_id'])
                if provider_id in provider_data:
                    results.append({
                        'rank': i + 1,
                        'provider_id': provider_id,
                        'provider_name': provider_data[provider_id].get('provider_name', 'Unknown'),
                        'specialty': provider_data[provider_id].get('specialty_readable', 'Unknown'),
                        'combined_score': baseline_result['score'],
                        'baseline_score': baseline_result['score'],
                        'provider_data': provider_data[provider_id]
                    })

        results = results[:k]

        if not include_features:
            for result in results:
                result.pop('features', None)

        return jsonify({
            'query': query,
            'method': method,
            'persona': persona_id,
            'alpha': alpha if persona_id else None,
            'num_results': len(results),
            'results': results
        })

    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500


if __name__ == '__main__':
    init_services()

    port = 5001
    print(f"Server running at http://localhost:{port}")
    print(f"Swagger UI: http://localhost:{port}/apidocs/\n")

    app.run(host='0.0.0.0', port=port, debug=True)
