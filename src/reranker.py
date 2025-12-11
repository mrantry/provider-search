"""Persona-based re-ranking using feature weights."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from feature_extractor import FeatureExtractor, compute_feature_score, flatten_weights


class PersonaReranker:
    """Re-ranks baseline results using persona-specific feature weights."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.personas = {}
        self.feature_extractor = FeatureExtractor()
        self._load_personas()

    def _load_personas(self):
        """Load persona configurations from JSON files."""
        config_files = {
            'sarah': 'persona_sarah.json',
            'marcus': 'persona_marcus.json',
            'fatima': 'persona_fatima.json',
            'robert': 'persona_robert.json',
            'jennifer': 'persona_jennifer.json'
        }

        for persona_id, filename in config_files.items():
            config_path = self.config_dir / filename
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.personas[persona_id] = {
                        'config': config,
                        'weights': flatten_weights(config)
                    }
            else:
                print(f"Warning: Persona config not found: {config_path}")

    def get_available_personas(self) -> List[str]:
        """Return list of loaded persona IDs."""
        return list(self.personas.keys())

    def get_persona_info(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Return persona metadata (name, description, priority order)."""
        if persona_id not in self.personas:
            return None

        config = self.personas[persona_id]['config']
        return {
            'id': persona_id,
            'name': config.get('name'),
            'description': config.get('description'),
            'priority_order': config.get('priority_order')
        }

    def rerank(
        self,
        baseline_results: List[Dict[str, Any]],
        provider_data: Dict[str, Dict[str, Any]],
        persona_id: str,
        alpha: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results using: combined_score = α × baseline + (1-α) × persona_score

        Args:
            baseline_results: List of {'provider_id', 'score'} from BM25/QL
            provider_data: Map of provider_id -> full provider record
            persona_id: Persona to use for re-ranking
            alpha: Weight for baseline score (higher = more text relevance)
        """
        if persona_id not in self.personas:
            raise ValueError(f"Unknown persona: {persona_id}. Available: {self.get_available_personas()}")

        weights = self.personas[persona_id]['weights']
        reranked_results = []

        # Normalize baseline scores to [0,1]
        baseline_scores = [r['score'] for r in baseline_results]
        max_baseline = max(baseline_scores) if baseline_scores else 1.0
        min_baseline = min(baseline_scores) if baseline_scores else 0.0
        baseline_range = max_baseline - min_baseline if max_baseline > min_baseline else 1.0

        for result in baseline_results:
            provider_id = str(result['provider_id'])

            if provider_id not in provider_data:
                continue

            provider = provider_data[provider_id]
            features = self.feature_extractor.extract_features(provider)
            persona_score = compute_feature_score(features, weights)
            normalized_baseline = (result['score'] - min_baseline) / baseline_range
            combined_score = alpha * normalized_baseline + (1 - alpha) * persona_score

            reranked_results.append({
                'provider_id': provider_id,
                'provider_name': provider.get('provider_name', 'Unknown'),
                'specialty': provider.get('specialty_readable', 'Unknown'),
                'baseline_score': result['score'],
                'normalized_baseline': normalized_baseline,
                'persona_score': persona_score,
                'combined_score': combined_score,
                'features': features,
                'provider_data': provider
            })

        reranked_results.sort(key=lambda x: x['combined_score'], reverse=True)

        for i, result in enumerate(reranked_results):
            result['rank'] = i + 1

        return reranked_results

    def explain_ranking(self, result: Dict[str, Any], persona_id: str, top_k: int = 5) -> Dict[str, Any]:
        """Return top contributing features for a ranking decision."""
        if persona_id not in self.personas:
            return {}

        weights = self.personas[persona_id]['weights']
        features = result.get('features', {})

        contributions = []
        for feature_name, weight in weights.items():
            if feature_name in features:
                contribution = features[feature_name] * weight
                contributions.append({
                    'feature': feature_name,
                    'value': features[feature_name],
                    'weight': weight,
                    'contribution': contribution
                })

        contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)

        return {
            'provider_id': result['provider_id'],
            'provider_name': result['provider_name'],
            'rank': result['rank'],
            'combined_score': result['combined_score'],
            'baseline_score': result['baseline_score'],
            'persona_score': result['persona_score'],
            'top_features': contributions[:top_k],
            'persona': self.get_persona_info(persona_id)
        }


def load_provider_data(jsonl_path: str, provider_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Load provider records for specified NPIs from JSONL file."""
    provider_ids_set = set(str(pid) for pid in provider_ids)
    providers = {}

    with open(jsonl_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue

            provider = json.loads(line)
            provider_id = str(provider.get('NPI'))

            if provider_id in provider_ids_set:
                providers[provider_id] = provider
                if len(providers) == len(provider_ids_set):
                    break

    return providers
