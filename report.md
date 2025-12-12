# Provider Search System: Technical Report

**Course**: CS 410 - Text Information Systems
**Project**: Personalized Healthcare Provider Search Engine
**Date**: December 2025

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Data Collection and Processing](#data-collection-and-processing)
3. [Search Index and Baseline Retrieval](#search-index-and-baseline-retrieval)
4. [Feature Engineering](#feature-engineering)
5. [Persona-Based Reranker](#persona-based-reranker)
6. [Front-End Implementation](#front-end-implementation)
7. [System Architecture](#system-architecture)
8. [Evaluation and Results](#evaluation-and-results)
9. [Conclusion](#conclusion)

---

## Project Overview

This project implements a personalized healthcare provider search engine that combines classical information retrieval techniques with modern feature-based reranking. The system addresses the challenge that different users have different priorities when searching for healthcare providers: some prioritize convenience, others focus on quality, and some need specific insurance coverage or language support.

Our solution implements a two-stage retrieval pipeline:
1. **Baseline Retrieval**: Fast candidate selection using BM25 or Query Likelihood
2. **Persona-Based Reranking**: Feature-driven personalization based on user profiles

---

## Data Collection and Processing

### Data Source and Scale

Our provider corpus consists of **303,134 healthcare providers** from Illinois, gathered from multiple authoritative sources:

- **NPI Registry**: Primary source for provider identifiers and basic information
- **CMS Care Compare/Physician Compare**: Quality metrics, ratings, and institutional affiliations
- **Synthetic Augmentation**: To fill gaps in coverage for newer features like telehealth availability

### Data Schema

Each provider record contains 35 fields across five categories:

**1. Identifiers and Basic Information**
- National Provider Identifier (NPI)
- Provider name
- Specialty
- Credentials
- Gender

**2. Location Data**
- Full address (street, city, state, ZIP)
- Geocoded coordinates (latitude/longitude)
- Distance from reference point (miles)

**3. Quality Metrics**
- Average rating (0-5 scale)
- Number of reviews
- Years of experience (calculated from NPI enumeration date)

**4. Availability and Convenience**
- Wait time in days
- Appointment slots available (7-day, 14-day, 30-day windows)
- Availability score (composite metric)
- Evening hours available (boolean)
- Weekend hours available (boolean)
- Telehealth availability (boolean)
- Accepting new patients (boolean)

**5. Insurance and Coverage**
- Network breadth (percentage of major networks)
- Blue Cross Blue Shield (BCBS) participation
- UnitedHealthcare (UHC) participation
- Medicare acceptance
- Medicaid acceptance

**6. Demographics and Accessibility**
- Languages spoken (Spanish, Chinese)
- Cultural sensitivity indicators

### ETL Pipeline

The data underwent extensive processing to create a search-ready corpus:

1. **Name Normalization**: Standardized provider names and removed special characters
2. **Specialty Mapping**: Mapped provider types to controlled taxonomy
3. **Geocoding**: Converted addresses to latitude/longitude coordinates
4. **Language Detection**: Enumerated supported languages from free-text fields
5. **Experience Calculation**: Computed years of experience from NPI enumeration date
6. **Search Field Creation**: Combined name, specialty, city, and state into searchable `search_text` field

### Data Management

- Stored in both JSONL (JSON Lines) and CSV formats
- Managed via Git LFS (Large File Storage) due to size
- 303K+ documents totaling ~150MB compressed

---

## Search Index and Baseline Retrieval

### Index Construction

We built a search index from the provider data using **Pyserini** (Python wrapper) and **Lucene** (Java-based search library). The index enables fast retrieval over the provider dataset.

**Indexing Parameters**:
- **Threads**: 4 parallel indexing threads
- **Batch Size**: 1,000 documents per batch
- **Index Type**: Inverted index with position information
- **Indexed Fields**: `search_text` (concatenation of name, specialty, city, state)

### Baseline Retrieval Methods

We implemented two baseline retrieval methods:

#### 1. BM25 (Primary Method)

BM25 is a probabilistic ranking function that scores documents based on query term frequency and inverse document frequency, with saturation and length normalization.

**Parameters**:
- `k1 = 0.9`: Controls term frequency saturation (lower than default 1.2, reducing impact of repeated terms)
- `b = 0.4`: Controls document length normalization (lower than default 0.75, since provider records are uniformly short)

**Retrieval**: Top 100 candidates per query

The BM25 scoring formula is:

```
score(D,Q) = Σ IDF(qi) × (f(qi,D) × (k1 + 1)) / (f(qi,D) + k1 × (1 - b + b × |D|/avgdl))
```

Where:
- `f(qi,D)` = term frequency of query term qi in document D
- `|D|` = length of document D
- `avgdl` = average document length in collection
- `IDF(qi)` = inverse document frequency of term qi

#### 2. Query Likelihood with Dirichlet Smoothing (Secondary Method)

Query Likelihood is a language modeling approach that estimates the probability that a document's language model would generate the query.

**Parameters**:
- `μ = 1000.0`: Dirichlet prior parameter (controls smoothing strength)

**Retrieval**: Top 100 candidates per query

The Dirichlet-smoothed scoring formula is:

```
score(D,Q) = Σ log((c(qi,D) + μ × P(qi|C)) / (|D| + μ))
```

Where:
- `c(qi,D)` = count of term qi in document D
- `P(qi|C)` = collection probability of term qi
- `|D|` = document length
- `μ` = smoothing parameter

### Retrieval Performance

Both methods retrieve candidates in **under 100ms** per query from the 303K document collection, enabling real-time search. The top 100 candidates provide sufficient recall for downstream reranking while keeping computational costs manageable.

---

## Feature Engineering

### Feature Extraction Architecture

The `FeatureExtractor` class (`src/feature_extractor.py`) normalizes 20+ provider attributes to a [0,1] scale, enabling fair comparison across heterogeneous feature types.

### Feature Categories and Normalization

#### 1. Convenience Features (7 features)

| Feature | Normalization Strategy | Rationale |
|---------|----------------------|-----------|
| `distance_miles` | Inverted, capped at 100 miles | Closer providers score higher |
| `availability_score` | Direct pass-through | Pre-normalized composite metric |
| `wait_days` | Inverted, capped at 30 days | Shorter waits score higher |
| `appointments_available_7days` | Linear, max 100 slots | Direct indicator of availability |
| `appointments_available_14days` | Linear, max 100 slots | Medium-term availability |
| `appointments_available_30days` | Linear, max 100 slots | Long-term availability |
| `evening_hours` | Boolean → {0, 1} | Supports working hours constraints |
| `weekend_hours` | Boolean → {0, 1} | Supports weekend-only availability |
| `telehealth_available` | Boolean → {0, 1} | Remote care option |

#### 2. Quality Features (4 features)

| Feature | Normalization Strategy | Rationale |
|---------|----------------------|-----------|
| `average_rating` | Linear, 0-5 → 0-1 | Standard rating scale |
| `num_reviews` | Log-scale, log(1+x)/log(1+max) | Handles wide range (1-1000+) |
| `years_experience` | Linear, capped at 50 years | Experience proxy |
| `has_rating` | Boolean → {0, 1} | Indicates verified quality data |

**Note**: We use log-scale normalization for `num_reviews` because the distribution is highly skewed (many providers have 1-10 reviews, few have 100+). Log scaling prevents providers with thousands of reviews from dominating the score.

#### 3. Cost Features (5 features)

| Feature | Normalization Strategy | Rationale |
|---------|----------------------|-----------|
| `network_breadth` | Percentage → 0-1 | Proportion of major networks |
| `in_network_bcbs` | Boolean → {0, 1} | Blue Cross Blue Shield coverage |
| `in_network_uhc` | Boolean → {0, 1} | UnitedHealthcare coverage |
| `accepts_medicare` | Boolean → {0, 1} | Medicare coverage |
| `accepts_medicaid` | Boolean → {0, 1} | Medicaid coverage |

#### 4. Demographic Features (3 features)

| Feature | Normalization Strategy | Rationale |
|---------|----------------------|-----------|
| `speaks_spanish` | Boolean → {0, 1} | Language accessibility |
| `speaks_chinese` | Boolean → {0, 1} | Language accessibility |
| `accepting_new_patients` | Boolean → {0, 1} | Immediate availability |

### Handling Missing Values

The feature extractor implements graceful fallbacks:
- **Missing numeric values**: Default to 0.5 (neutral score)
- **Missing boolean values**: Default to False (0)
- **NaN detection**: Explicit checks prevent propagation of invalid values
- **Outlier capping**: Distance and wait time capped to prevent extreme values

---

## Persona-Based Reranker

### Reranking Architecture

The `PersonaReranker` class (`src/reranker.py`) implements a feature-based linear scoring model with persona-specific weights.

### Scoring Formula

The combined score blends baseline retrieval relevance with persona-driven preferences:

```
combined_score = α × normalized_baseline_score + (1 - α) × persona_score

persona_score = Σ (feature_value × feature_weight)
```

Where:
- **α** (alpha) ∈ [0, 1]: Controls text relevance vs. persona preference tradeoff
  - α = 1.0: Pure baseline retrieval (no personalization)
  - α = 0.5: Equal weight to relevance and persona (default)
  - α = 0.0: Pure persona ranking (ignores query relevance)
- **normalized_baseline_score**: Min-max normalized BM25/QL score
- **persona_score**: Weighted sum of normalized features

### Persona Definitions

We designed five distinct personas representing common healthcare seeker archetypes:

#### 1. Sarah - Busy Professional

**Profile**: 35-year-old executive with limited time
**Priority Order**: Convenience → Quality → Cost → Demographics

**Top Feature Weights**:
- `distance_miles`: -0.30 (strong proximity preference)
- `availability_score`: 0.25 (high availability crucial)
- `average_rating`: 0.25 (still values quality)
- `wait_days`: -0.15 (minimizes waiting)
- `evening_hours`: 0.15 (accommodates work schedule)
- `telehealth_available`: 0.15 (remote convenience)

**Use Case**: Needs same-day or next-day appointments near her office, prefers telehealth when possible.

#### 2. Marcus - Budget-Conscious Parent

**Profile**: 42-year-old teacher managing family healthcare
**Priority Order**: Cost → Quality → Convenience → Demographics

**Top Feature Weights**:
- `network_breadth`: 0.30 (maximizes insurance coverage)
- `average_rating`: 0.20 (quality within budget)
- `in_network_bcbs`: 0.15 (specific insurance)
- `in_network_uhc`: 0.15 (alternative insurance)
- `accepts_medicaid`: 0.10 (cost factor)

**Use Case**: Family of four needs affordable in-network care, willing to travel or wait for lower costs.

#### 3. Fatima - Community-Oriented Patient

**Profile**: 28-year-old graduate student seeking culturally affirming care
**Priority Order**: Demographics → Quality → Convenience → Cost

**Top Feature Weights**:
- `speaks_spanish`: 0.15 (language concordance critical)
- `speaks_chinese`: 0.15 (alternative language support)
- `average_rating`: 0.15 (community-validated quality)
- `network_breadth`: 0.10 (practical coverage)
- `telehealth_available`: 0.10 (accessibility)

**Use Case**: Values providers who understand her cultural background and speak her language, even if less convenient.

#### 4. Robert - Quality-First Patient

**Profile**: 58-year-old managing chronic condition, cost-insensitive
**Priority Order**: Quality → Experience → Convenience → Cost

**Top Feature Weights**:
- `average_rating`: 0.35 (quality paramount)
- `years_experience`: 0.25 (expertise critical for complex care)
- `num_reviews`: 0.15 (validation through volume)
- `has_rating`: 0.10 (verified quality data)

**Use Case**: Managing diabetes and hypertension, willing to travel far and wait months for top-rated specialists.

#### 5. Jennifer - Balanced Seeker

**Profile**: 45-year-old seeking well-rounded care
**Priority Order**: Quality → Convenience → Cost → Demographics

**Top Feature Weights**:
- `average_rating`: 0.20 (moderate quality focus)
- `distance_miles`: -0.15 (reasonable proximity)
- `network_breadth`: 0.15 (coverage important)
- `availability_score`: 0.15 (reasonable access)
- Moderate weights across all dimensions

**Use Case**: General health maintenance, wants good-enough care across all dimensions without extreme preferences.

### Persona Configuration

Personas are stored as JSON configuration files in `config/`:
- `persona_sarah.json`
- `persona_marcus.json`
- `persona_fatima.json`
- `persona_robert.json`
- `persona_jennifer.json`

This design allows easy modification of weights without code changes, enabling rapid experimentation and A/B testing.

### Explainability

The reranker includes an `explain_ranking()` method that returns:
- Top-K feature contributions for each result
- Feature name, value, weight, and contribution to final score
- Enables transparency and debugging of ranking decisions

---

## Front-End Implementation

### Technology Stack

- **Framework**: React 19.2.0 (latest) with functional components and hooks
- **Build Tool**: Vite 7.2.2 (fast HMR and optimized production builds)
- **UI Library**: Material-UI (@mui/material 7.3.6) for professional components
- **Icons**: Material Icons (@mui/icons-material)
- **Styling**: CSS-in-JS with Emotion (@emotion/react, @emotion/styled)
- **Linting**: ESLint with React-specific rules

### Component Architecture

#### 1. App Component (`App.jsx`)

**Responsibilities**:
- Application state management (results, search status, errors)
- API integration with Flask backend
- Results rendering as responsive grid
- Error handling and user feedback

**State Variables**:
```javascript
const [results, setResults] = useState([])
const [status, setStatus] = useState('idle')  // 'idle' | 'loading' | 'success' | 'error'
const [error, setError] = useState(null)
const [lastQuery, setLastQuery] = useState('')
const [lastPersona, setLastPersona] = useState('')
```

**Search Flow**:
1. User enters query and selects persona
2. App calls `POST http://localhost:5001/search` with `{query, persona}`
3. Status updates: idle → loading → success/error
4. Results rendered as provider cards or error message displayed

#### 2. SearchBar Component (`SearchBar.jsx`)

**Responsibilities**:
- Search query input field
- Persona selector integration
- Enter-key and button-click search triggers
- User input validation

**Features**:
- Material-UI InputBase for clean styling
- Integrated search icon
- Keyboard accessibility (Enter to search)
- Responsive layout

#### 3. PersonaSelector Component (`PersonaSelector.jsx`)

**Responsibilities**:
- Fetch personas from backend (`GET /personas`)
- Dropdown selection with Material-UI Select
- Loading and error states
- Visual feedback for selected persona

**Features**:
- Async persona loading on component mount
- Loading spinner during fetch
- Error handling with fallback message
- Custom styling with blue theme

**Data Flow**:
```
Component Mount → Fetch /personas → Update state → Render dropdown
User Selection → Callback to parent → Update App state → Ready for search
```

#### 4. API Client (`provider-search-controller.js`)

**Functions**:
- `getPersonas()`: Fetches available personas from backend
- Error handling and response parsing
- Transforms persona objects to frontend format

### User Interface Design

#### Visual Styling

**Color Scheme** (Dark theme with blue accents):
- **Primary**: `#e8f0fa` (light blue text)
- **Secondary**: `#9fb4c8` (muted blue)
- **Accent**: `#6fc1ff` (bright blue highlights)
- **Background**: Dark gradients with rgba transparency

**Layout**:
- **Hero Section**: Title, description, search interface
- **Results Grid**: Auto-fit responsive columns
  - Min width: 280px per card
  - Max 3 columns on large screens
  - Single column on mobile
  - 20px gap between cards

**Provider Cards**:
- Gradient background (`linear-gradient(135deg, rgba(...)`)
- Rounded corners (14px border-radius)
- Subtle elevation (box-shadow)
- Top-to-bottom layout:
  1. Provider name (bold, 1.2rem)
  2. Location (city, state)
  3. Specialty
  4. Rating (stars) and review count
  5. Badge row (accepting patients, telehealth)

**Visual Polish**:
- Smooth transitions (300ms ease-in-out)
- Glassmorphism effects (rgba backgrounds with blur)
- Pill-shaped badges with semantic colors
  - Green (`#4caf50`) for positive attributes
  - Blue (`#2196f3`) for informational attributes
- Hover effects on interactive elements

#### Responsive Design

- **Mobile (< 768px)**: Single column, full-width cards, stacked search controls
- **Tablet (768-1024px)**: 2-column grid, side-by-side search controls
- **Desktop (> 1024px)**: 3-column grid, horizontal search bar

### API Integration

#### Search Endpoint

**Request**:
```javascript
POST http://localhost:5001/search
Content-Type: application/json

{
  "query": "cardiologist in Chicago",
  "persona": "robert"  // optional
}
```

**Response**:
```json
{
  "results": [
    {
      "doc_id": "1234567890",
      "name": "Dr. Jane Smith",
      "specialty": "Cardiology",
      "city": "Chicago",
      "state": "IL",
      "average_rating": 4.8,
      "num_reviews": 127,
      "accepting_new_patients": true,
      "telehealth_available": true,
      "score": 0.847
    },
    ...
  ],
  "total": 20,
  "query": "cardiologist in Chicago",
  "persona": "robert"
}
```

#### Personas Endpoint

**Request**:
```javascript
GET http://localhost:5001/personas
```

**Response**:
```json
[
  {
    "id": "sarah",
    "name": "Sarah - Busy Professional",
    "description": "Prioritizes convenience and availability"
  },
  ...
]
```

### User Experience Flow

1. **Landing**: User sees search interface with title "Find Your Ideal Healthcare Provider"
2. **Persona Selection**: Optional dropdown to select persona (defaults to none)
3. **Query Entry**: Type search query (e.g., "pediatrician near me")
4. **Search**: Click button or press Enter
5. **Loading**: Loading message displayed
6. **Results**: Grid of provider cards with relevant information
7. **No Results**: Friendly message if no matches found
8. **Error Handling**: Clear error messages for API failures

---

## System Architecture

### Overall Architecture Diagram

```
┌─────────────────┐
│   React App     │
│  (Port 5173)    │
│                 │
│  - SearchBar    │
│  - Persona      │
│    Selector     │
│  - Results Grid │
└────────┬────────┘
         │ HTTP POST /search
         │ {query, persona}
         ▼
┌─────────────────┐
│   Flask API     │
│  (Port 5001)    │
│                 │
│  - CORS enabled │
│  - Swagger docs │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Baseline        │
│ Retrieval       │
│                 │
│ - BM25 (k1=0.9) │
│ - QL (μ=1000)   │
│ - Top 100 docs  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Feature         │
│ Extractor       │
│                 │
│ - Normalize 20+ │
│   features      │
│ - Handle NaN    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Persona         │
│ Reranker        │
│                 │
│ - Load weights  │
│ - Compute score │
│ - α blending    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Top K Results   │
│ (JSON)          │
└─────────────────┘
```

### Technology Stack Summary

**Backend**:
- Python 3.8+
- Pyserini 0.22.0 (Lucene wrapper)
- Flask 2.3.0 (Web framework)
- Flasgger 0.9.7 (Swagger/OpenAPI)
- Flask-CORS 4.0.0 (Cross-origin support)

**Frontend**:
- React 19.2.0
- Vite 7.2.2
- Material-UI 7.3.6
- Emotion (CSS-in-JS)

**Data**:
- JSONL/CSV formats
- Git LFS for version control
- Lucene inverted index

### API Specification

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API information and version |
| GET | `/health` | Health check endpoint |
| GET | `/personas` | List all available personas |
| GET | `/personas/{id}` | Get specific persona details |
| POST | `/search` | Search with optional persona |

#### Search Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query text |
| `persona` | string | No | null | Persona ID (sarah, marcus, etc.) |
| `method` | string | No | "bm25" | Retrieval method ("bm25" or "ql_dirichlet") |
| `k` | integer | No | 20 | Number of results (1-100) |
| `alpha` | float | No | 0.5 | Baseline weight (0.0-1.0) |
| `include_features` | boolean | No | false | Include feature details in response |

### Scalability Considerations

**Current Performance**:
- **Index Size**: ~150MB (303K documents)
- **Query Latency**: < 100ms for baseline retrieval
- **Reranking Latency**: < 50ms for 100 candidates
- **Total Latency**: < 200ms end-to-end

**Scalability Strategies**:
1. **Two-stage pipeline**: Only rerank top 100 candidates, not full corpus
2. **Efficient indexing**: Lucene inverted index with 4-thread parallelism
3. **Normalized features**: Pre-computed where possible, normalized on-the-fly
4. **Stateless API**: Enables horizontal scaling with load balancer
5. **Caching**: Pyserini caches index in memory after first load

**Future Optimizations**:
- **Feature caching**: Pre-compute and cache normalized features
- **Batch reranking**: Process multiple queries in parallel
- **GPU acceleration**: Use neural rerankers (BERT, T5) with GPU
- **Distributed index**: Shard Lucene index across multiple nodes

---

## Evaluation and Results

### Evaluation Metrics

We evaluated the system using standard information retrieval metrics:

1. **Precision@K**: Proportion of relevant results in top K
2. **Recall@K**: Proportion of total relevant results found in top K
3. **Mean Reciprocal Rank (MRR)**: Average inverse rank of first relevant result
4. **NDCG@K**: Normalized Discounted Cumulative Gain (accounts for ranking position)

### Baseline Performance

**BM25 (k1=0.9, b=0.4)**:
- Optimized for short, uniform-length provider records
- Lower `b` value reduces length normalization impact
- Lower `k1` value reduces term frequency saturation

**Query Likelihood (μ=1000)**:
- Moderate smoothing balances document and collection probabilities
- Performs comparably to BM25 on this dataset

### Persona Impact Analysis

To assess persona impact, we compared rankings for the same query across different personas:

**Example Query**: "cardiologist in Chicago"

| Rank | Baseline (BM25) | Sarah (Convenience) | Robert (Quality) | Marcus (Cost) |
|------|----------------|---------------------|------------------|---------------|
| 1 | Dr. A (3.5★, 5mi) | Dr. B (4.0★, 1mi) | Dr. C (4.9★, 15mi) | Dr. D (4.2★, in-network) |
| 2 | Dr. E (4.1★, 8mi) | Dr. F (3.8★, 2mi) | Dr. G (4.8★, 20mi) | Dr. H (4.0★, in-network) |
| 3 | Dr. I (4.4★, 12mi) | Dr. J (4.2★, 3mi) | Dr. K (4.7★, 18mi) | Dr. L (3.9★, in-network) |

**Observations**:
- **Sarah**: Prioritizes proximity (1-3 miles) over rating
- **Robert**: Willing to travel 15-20 miles for top ratings (4.7-4.9★)
- **Marcus**: Focuses on in-network providers regardless of distance
- **Baseline**: Balances text relevance with no personalization

### Alpha Parameter Sensitivity

We tested different α values to understand the relevance-personalization tradeoff:

| α | Behavior | Use Case |
|---|----------|----------|
| 0.0 | Pure persona ranking, ignores query | User has strong preferences, willing to sacrifice relevance |
| 0.3 | Persona-heavy, minimal text relevance | User wants heavy personalization |
| 0.5 | Balanced (default) | Reasonable tradeoff for most users |
| 0.7 | Relevance-heavy, light personalization | User wants subtle personalization |
| 1.0 | Pure baseline, no personalization | Traditional search, no preferences |

**Recommendation**: α = 0.5 provides good balance for most use cases.

### User Study Results

We conducted informal user testing with 12 participants (mix of students and staff):

**Key Findings**:
1. **Persona Selection**: 83% of users selected a persona for their search
2. **Most Popular Personas**:
   - Jennifer (Balanced): 42%
   - Sarah (Convenience): 25%
   - Marcus (Cost): 17%
   - Robert (Quality): 8%
   - Fatima (Demographics): 8%
3. **Satisfaction**: Users rated personalized results 4.2/5 vs. baseline 3.1/5
4. **Feature Requests**:
   - More personas (e.g., "parents seeking pediatricians")
   - Ability to customize persona weights
   - Save favorite providers

---

## Conclusion

### Project Summary

We successfully built a personalized healthcare provider search engine that demonstrates how feature-based reranking can significantly improve search results for different user types. The system combines:

1. **Classical IR**: BM25 and Query Likelihood for efficient baseline retrieval
2. **Feature Engineering**: 20+ normalized features across convenience, quality, cost, and demographics
3. **Persona Modeling**: Five distinct user archetypes with interpretable feature weights
4. **Modern Web Stack**: React frontend with Material-UI and Flask backend

### Key Achievements

1. **Scalable Architecture**: Handles 303K providers with sub-200ms latency
2. **Interpretable Personalization**: Transparent feature weights and explainable rankings
3. **Flexible Configuration**: JSON-based persona definitions enable rapid iteration
4. **Production-Ready API**: Swagger documentation, CORS support, health checks
5. **Polished UI**: Responsive design with professional Material-UI components

### Lessons Learned

1. **Feature Normalization is Critical**: Without [0,1] normalization, features with different scales dominate the ranking
2. **Log-Scale for Skewed Distributions**: Review counts and similar features need log normalization to prevent outliers from dominating
3. **Two-Stage Retrieval Works**: Reranking only 100 candidates balances accuracy and performance
4. **Personas Need Testing**: Initial persona weights required tuning based on qualitative result inspection
5. **User Interface Matters**: Clean, responsive UI significantly improved perceived system quality

### Future Work

1. **Neural Rerankers**: Replace linear scoring with BERT or T5 cross-encoders for better semantic matching
2. **Learning to Rank**: Learn persona weights from user click data instead of hand-tuning
3. **Query Expansion**: Add synonyms and medical term mappings (e.g., "heart doctor" → "cardiologist")
4. **Geolocation**: Use browser geolocation API for automatic distance calculation
5. **More Personas**: Add personas for specific use cases (parents, seniors, chronic conditions)
6. **A/B Testing Framework**: Systematically test different α values and persona configurations
7. **Multi-Factor Filtering**: Add UI controls for hard filters (insurance, languages, distance range)
8. **Provider Details Page**: Click through to see full provider profile with maps and reviews

### Conclusion

This project demonstrates that personalized search can be achieved without complex machine learning by thoughtfully engineering features and modeling user preferences. The combination of efficient baseline retrieval, feature-based reranking, and user-friendly interface creates a system that provides measurably better results for different user types while maintaining the interpretability and control that healthcare searchers need.

The modular architecture separates concerns cleanly (data processing, indexing, reranking, presentation) and enables future enhancements without major refactoring. The system is ready for deployment and can serve as a foundation for more advanced personalization techniques.

---

## References

1. Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333-389.

2. Zhai, C., & Lafferty, J. (2004). A Study of Smoothing Methods for Language Models Applied to Information Retrieval. *ACM Transactions on Information Systems*, 22(2), 179-214.

3. Pyserini Documentation: https://github.com/castorini/pyserini

4. Lucene Documentation: https://lucene.apache.org/

5. Material-UI Documentation: https://mui.com/

6. React Documentation: https://react.dev/

---

**Team Members**:
- Michael Antry - Service Architecture and API Integration
- Dean Fletcher - Data Engineering and Collection
- Jordan Alwan - UI/Frontend Development
- Janani Jayanth - Feature Engineering and QL Implementation
