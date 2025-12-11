"""Feature extraction and normalization for provider re-ranking."""

import math
from typing import Dict, Any


class FeatureExtractor:
    """Extracts and normalizes provider features to [0,1] scale."""

    def __init__(self):
        # Normalization constants
        self.MAX_DISTANCE = 100.0
        self.MAX_WAIT_DAYS = 30.0
        self.MAX_EXPERIENCE = 50.0
        self.MAX_REVIEWS = 1000.0
        self.MAX_APPOINTMENTS = 100.0

    def extract_features(self, provider: Dict[str, Any]) -> Dict[str, float]:
        """Extract and normalize all features from provider record."""
        features = {}

        # Convenience
        features['distance_miles'] = self._normalize_distance(provider.get('distance_miles', 50.0))
        features['availability_score'] = float(provider.get('availability_score', 0.5))
        features['wait_days'] = self._normalize_wait_days(provider.get('wait_days', 14))
        features['appointments_available_7days'] = self._normalize_appointments(
            provider.get('appointments_available_7days', 0))
        features['appointments_available_14days'] = self._normalize_appointments(
            provider.get('appointments_available_14days', 0))
        features['appointments_available_30days'] = self._normalize_appointments(
            provider.get('appointments_available_30days', 0))
        features['evening_hours'] = 1.0 if provider.get('evening_hours') else 0.0
        features['weekend_hours'] = 1.0 if provider.get('weekend_hours') else 0.0
        features['telehealth_available'] = 1.0 if provider.get('telehealth_available') else 0.0

        # Quality
        features['average_rating'] = self._normalize_rating(provider.get('average_rating', 0.0))
        features['num_reviews'] = self._normalize_reviews(provider.get('num_reviews', 0))
        features['years_experience'] = self._normalize_experience(provider.get('years_experience', 0))
        features['has_rating'] = 1.0 if provider.get('has_rating') else 0.0

        # Cost
        features['network_breadth'] = float(provider.get('network_breadth', 0.0))
        features['in_network_bcbs'] = 1.0 if provider.get('in_network_bcbs') else 0.0
        features['in_network_uhc'] = 1.0 if provider.get('in_network_uhc') else 0.0
        features['accepts_medicare'] = 1.0 if provider.get('accepts_medicare') else 0.0
        features['accepts_medicaid'] = 1.0 if provider.get('accepts_medicaid') else 0.0

        # Demographics
        features['speaks_spanish'] = 1.0 if provider.get('speaks_spanish') else 0.0
        features['speaks_chinese'] = 1.0 if provider.get('speaks_chinese') else 0.0
        features['accepting_new_patients'] = 1.0 if provider.get('accepting_new_patients') else 0.0

        return features

    def _normalize_distance(self, distance: float) -> float:
        """Invert distance so closer = higher value."""
        if distance is None or math.isnan(distance):
            return 0.5
        return 1.0 - min(distance / self.MAX_DISTANCE, 1.0)

    def _normalize_wait_days(self, wait_days: int) -> float:
        """Invert wait time so shorter = higher value."""
        if wait_days is None:
            return 0.5
        return 1.0 - min(wait_days / self.MAX_WAIT_DAYS, 1.0)

    def _normalize_rating(self, rating: float) -> float:
        """Convert 0-5 rating scale to 0-1."""
        if rating is None or rating == 0.0:
            return 0.0
        return min(rating / 5.0, 1.0)

    def _normalize_reviews(self, num_reviews: int) -> float:
        """Log-scale normalization for review counts."""
        if num_reviews is None or num_reviews <= 0:
            return 0.0
        return min(math.log10(num_reviews + 1) / math.log10(self.MAX_REVIEWS + 1), 1.0)

    def _normalize_experience(self, years: int) -> float:
        """Linear normalization of years of experience."""
        if years is None or years <= 0:
            return 0.0
        return min(years / self.MAX_EXPERIENCE, 1.0)

    def _normalize_appointments(self, num_appointments: int) -> float:
        """Linear normalization of appointment availability."""
        if num_appointments is None or num_appointments <= 0:
            return 0.0
        return min(num_appointments / self.MAX_APPOINTMENTS, 1.0)


def compute_feature_score(features: Dict[str, float], weights: Dict[str, float]) -> float:
    """Compute weighted sum of features."""
    score = 0.0
    for feature_name, weight in weights.items():
        if feature_name in features:
            score += features[feature_name] * weight
    return score


def flatten_weights(persona_weights: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """Flatten nested persona config to simple feature->weight mapping."""
    flat_weights = {}
    feature_weights = persona_weights.get('feature_weights', {})

    for category, features in feature_weights.items():
        for feature_name, weight in features.items():
            if isinstance(weight, (int, float)):
                flat_weights[feature_name] = float(weight)

    return flat_weights
