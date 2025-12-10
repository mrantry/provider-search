# Provider Search: Persona-Based Healthcare Provider Retrieval

A healthcare provider search system that combines baseline information retrieval methods (BM25, Query Likelihood) with persona-based re-ranking to personalize search results. Built for the UIUC CS410 Information Retrieval course.

## Overview

This project addresses the challenge of personalizing healthcare provider search by moving beyond pure text relevance to incorporate user preferences and priorities. While traditional search engines rank providers based solely on query-document similarity, different users have different priorities when selecting healthcare providers - some prioritize convenience and proximity, others focus on cost and insurance coverage, while others seek the highest quality care regardless of other factors.

Our system implements a two-stage retrieval architecture:

1. **Baseline Retrieval**: Uses BM25 or Query Likelihood with Dirichlet smoothing to retrieve the top 100 text-relevant providers from a corpus of 303,000+ Illinois healthcare providers
2. **Persona-Based Re-ranking**: Applies feature-based re-ranking using persona-specific weight vectors to personalize results according to user priorities

The system exposes a RESTful API with comprehensive Swagger/OpenAPI documentation, making it suitable for integration with web frontends or mobile applications.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
python src/api.py

# Access Swagger UI
open http://localhost:5000/apidocs/
```

The Swagger UI provides interactive API documentation where you can test all endpoints directly from your browser.

## System Architecture

### Retrieval Pipeline

```
User Query → Baseline Retrieval (BM25/QL) → Feature Extraction → Persona Re-ranking → Personalized Results
```

**Stage 1: Baseline Retrieval**
- Lucene-based inverted index (via Pyserini)
- BM25 with parameters k1=0.9, b=0.4
- Query Likelihood with Dirichlet smoothing (μ=1000)
- Retrieves top 100 candidates for re-ranking

**Stage 2: Feature Extraction**
- Extracts and normalizes 20+ provider features
- Features grouped into five dimensions: convenience, quality, cost, demographics, cultural/religious alignment
- All features normalized to [0,1] range for consistent weighting

**Stage 3: Re-ranking**
- Combines baseline score with persona-specific feature score
- Scoring function: `combined_score = α × baseline_score + (1-α) × persona_score`
- α parameter controls trade-off between text relevance and persona preferences
- Results sorted by combined score

### Data

**Provider Corpus**: 303,134 healthcare providers from Illinois

**Provider Features** (35 fields per document):
- **Identifiers**: NPI, provider name, specialty
- **Location**: City, state, ZIP code, distance from reference point
- **Quality Metrics**: Average rating (0-5), number of reviews, years of experience
- **Availability**: Wait time in days, appointment slots (7/14/30 day windows), availability score
- **Convenience**: Evening hours, weekend hours, telehealth availability
- **Insurance**: Network breadth, specific networks (BCBS, UHC), Medicare/Medicaid acceptance
- **Demographics**: Languages spoken (Spanish, Chinese), provider credentials, gender
- **Other**: Accepting new patients, contact information

## Personas

The system implements five distinct user personas, each with a unique preference ordering over the five core value dimensions.

### Core Value Dimensions

1. **Convenience**: Location proximity, appointment availability, scheduling flexibility
2. **Quality**: Ratings, credentials, experience, patient outcomes
3. **Cost**: Insurance coverage, network breadth, affordability
4. **Shared Demographics**: Language, cultural background, age similarity
5. **Shared Values/Religion**: Religious/spiritual alignment, values compatibility

### Persona Definitions

#### Sarah - Busy Professional
- **Priority**: Convenience → Quality → Cost → Demographics → Religious
- **Profile**: 35-year-old marketing executive, works 60+ hours/week, good insurance
- **Needs**: Providers close to office/home, evening/weekend availability, short wait times
- **Use Case**: Values time efficiency above all; willing to pay more for convenience

**Feature Weights (Top 5)**:
- Distance (negative weight): -0.30
- Availability score: 0.25
- Average rating: 0.25
- Wait days (negative weight): -0.15
- Appointments in 7 days: 0.10

#### Marcus - Budget-Conscious Parent
- **Priority**: Cost → Quality → Convenience → Demographics → Religious
- **Profile**: 42-year-old teacher, family of four, high-deductible health plan
- **Needs**: Affordable providers, in-network coverage, transparent pricing
- **Use Case**: Managing healthcare for entire family on tight budget; willing to travel for savings

**Feature Weights (Top 5)**:
- Network breadth: 0.30
- Average rating: 0.20
- In-network BCBS: 0.15
- In-network UHC: 0.15
- Medicare acceptance: 0.10

#### Fatima - Community-Oriented Patient
- **Priority**: Religious/Values → Demographics → Quality → Convenience → Cost
- **Profile**: 28-year-old graduate student, Muslim, recently relocated
- **Needs**: Providers who understand and respect religious practices and cultural background
- **Use Case**: Cultural fit and religious sensitivity are paramount; willing to travel and pay more

**Feature Weights (Top 5)**:
- Cultural sensitivity proxy: 0.20
- Language match (Spanish): 0.15
- Language match (Chinese): 0.15
- Average rating: 0.15
- Years of experience: 0.10

#### Robert - Quality-First Patient
- **Priority**: Quality → Demographics → Convenience → Cost → Religious
- **Profile**: 58-year-old retired executive, managing chronic condition, excellent insurance
- **Needs**: Best possible care, top credentials, extensive experience
- **Use Case**: Researches providers extensively; cost and location not limiting factors

**Feature Weights (Top 5)**:
- Average rating: 0.35
- Years of experience: 0.25
- Number of reviews: 0.15
- Has rating data: 0.10
- Age similarity proxy: 0.05

#### Jennifer - Balanced Seeker
- **Priority**: Quality → Convenience → Cost → Demographics → Religious
- **Profile**: 45-year-old freelancer, moderate income, values holistic care
- **Needs**: Good balance across all factors; willing to make trade-offs
- **Use Case**: No extreme priorities; seeks reasonable quality at reasonable convenience and cost

**Feature Weights (Top 5)**:
- Average rating: 0.20
- Years of experience: 0.12
- Distance (negative weight): -0.12
- Availability score: 0.10
- Network breadth: 0.08

### Persona Configuration

Personas are defined in JSON configuration files (`config/persona_*.json`) with the following structure:

```json
{
  "name": "Sarah - Busy Professional",
  "description": "Prioritizes convenience and quality over cost",
  "priority_order": ["convenience", "quality", "cost", "demographic", "religious"],
  "feature_weights": {
    "convenience": {
      "distance_miles": -0.30,
      "availability_score": 0.25,
      "evening_hours": 0.08
    },
    "quality": {
      "average_rating": 0.25,
      "years_experience": 0.12
    }
  }
}
```

New personas can be added by creating additional configuration files and specifying custom weight vectors.

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and available endpoints |
| GET | `/health` | Service health check (search engine, reranker status) |
| GET | `/personas` | List all available personas with descriptions |
| GET | `/personas/{id}` | Get detailed information for a specific persona |
| POST | `/search` | Search providers with optional persona-based re-ranking |

### Search Endpoint

**POST /search**

Performs provider search with optional persona-based re-ranking.

**Request Body**:
```json
{
  "query": "cardiologist in Chicago",
  "persona": "sarah",
  "method": "bm25",
  "k": 20,
  "alpha": 0.5,
  "include_features": false
}
```

**Parameters**:
- `query` (string, required): Search query text
- `persona` (string, optional): Persona ID (sarah, marcus, fatima, robert, jennifer)
- `method` (string, optional): Retrieval algorithm - "bm25" (default) or "ql_dirichlet"
- `k` (integer, optional): Number of results to return, 1-100 (default: 20)
- `alpha` (float, optional): Baseline score weight, 0.0-1.0 (default: 0.5)
- `include_features` (boolean, optional): Include feature details in response (default: false)

**Alpha Parameter**:
Controls the balance between text relevance and persona preferences:
- α = 1.0: Pure text relevance (baseline only, persona ignored)
- α = 0.7: Text-dominant with persona influence
- α = 0.5: Balanced (recommended default)
- α = 0.3: Persona-dominant with text influence
- α = 0.0: Pure persona preferences (text used only for filtering)

**Response**:
```json
{
  "query": "cardiologist in Chicago",
  "method": "bm25",
  "persona": "sarah",
  "alpha": 0.5,
  "num_results": 10,
  "results": [
    {
      "rank": 1,
      "provider_id": "1234567890",
      "provider_name": "Dr. Jane Smith",
      "specialty": "Cardiology",
      "combined_score": 0.856,
      "baseline_score": 15.24,
      "persona_score": 0.472,
      "provider_data": {
        "NPI": 1234567890,
        "City Name": "Chicago",
        "distance_miles": 5.2,
        "average_rating": 4.5,
        "num_reviews": 150,
        "years_experience": 15,
        "evening_hours": true,
        "network_breadth": 0.75
      }
    }
  ]
}
```

### Example API Calls

**List available personas**:
```bash
curl http://localhost:5000/personas
```

**Basic search without persona** (baseline only):
```bash
curl -X POST http://localhost:5000/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "cardiologist in Chicago", "k": 10}'
```

**Search with convenience-focused persona**:
```bash
curl -X POST http://localhost:5000/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "cardiologist in Chicago",
    "persona": "sarah",
    "k": 10,
    "alpha": 0.5
  }'
```

**Search with cost-focused persona**:
```bash
curl -X POST http://localhost:5000/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "family medicine",
    "persona": "marcus",
    "k": 10,
    "alpha": 0.4
  }'
```

**Search with quality-focused persona**:
```bash
curl -X POST http://localhost:5000/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "pediatrician",
    "persona": "robert",
    "k": 10,
    "alpha": 0.3
  }'
```

## Swagger/OpenAPI Documentation

The API includes comprehensive Swagger documentation following the OpenAPI 3.0 specification.

### Accessing Swagger UI

When the server is running, navigate to **http://localhost:5000/apidocs/** to access the interactive Swagger UI.

The Swagger interface provides:
- Complete API documentation with request/response schemas
- Interactive "Try it out" functionality for all endpoints
- Pre-built example requests for different personas
- Parameter descriptions and validation rules
- Response schema documentation with example values

### OpenAPI Specification

The raw OpenAPI 3.0 specification is available at:
- **JSON format**: http://localhost:5000/apispec.json
- **YAML file**: `swagger.yaml` in the repository root

The specification can be:
- Imported into Postman or Insomnia for API testing
- Used with OpenAPI Generator or Swagger Codegen for client generation
- Shared with frontend developers for contract-based development
- Used for automated API testing and validation

### Example: Using Swagger UI

1. Start the server: `python src/api.py`
2. Open http://localhost:5000/apidocs/ in your browser
3. Expand the `POST /search` endpoint
4. Click "Try it out"
5. Select an example from the dropdown (e.g., "Persona Search - Sarah")
6. Click "Execute"
7. View the response with personalized results

## Installation

### Prerequisites

- **Python 3.8+**
- **Java 11+** (required for Pyserini/Lucene)

Verify Java installation:
```bash
java -version
```

If Java is not installed:
- **macOS**: `brew install openjdk@11`
- **Ubuntu/Debian**: `sudo apt-get install openjdk-11-jdk`
- **Windows**: Download from [Adoptium](https://adoptium.net/)

### Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd provider-search
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

This installs:
- `pyserini>=0.22.0` - Search engine (Lucene interface)
- `flask>=2.3.0` - Web framework
- `flasgger>=0.9.7` - Swagger/OpenAPI integration

3. **Verify data files**:
```bash
ls data/providers_illinois.jsonl
ls data/providers_illinois.csv
```

The provider data is managed with Git LFS. If files are missing:
```bash
git lfs pull
```

4. **Start the API server**:
```bash
python src/api.py
```

On first run, the system will automatically build the Lucene search index (takes 2-3 minutes for 300K documents).

## Testing

**Test baseline search** (command-line):
```bash
python src/baseline_retrieval.py "cardiologist in Chicago"
python src/baseline_retrieval.py "pediatrician" --method ql_dirichlet --k 50
```

Results are written to `output.json`.

**Test API endpoints**:
```bash
# Health check
curl http://localhost:5000/health

# List personas
curl http://localhost:5000/personas | jq

# Search with persona
curl -X POST http://localhost:5000/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "cardiologist", "persona": "sarah", "k": 5}' | jq
```

## Project Structure

```
provider-search/
├── config/                          # Persona weight configurations
│   ├── persona_sarah.json          # Convenience-focused persona
│   ├── persona_marcus.json         # Cost-focused persona
│   ├── persona_fatima.json         # Cultural-focused persona
│   ├── persona_robert.json         # Quality-focused persona
│   └── persona_jennifer.json       # Balanced persona
├── data/
│   ├── providers_illinois.jsonl    # Provider corpus (303,134 documents)
│   └── providers_illinois.csv      # Same data in CSV format
├── indexes/
│   └── provider_index/             # Lucene index (auto-generated)
├── src/
│   ├── baseline_retrieval.py       # BM25/QL search engine
│   ├── feature_extractor.py        # Feature extraction and normalization
│   ├── reranker.py                 # Persona-based re-ranking logic
│   └── api.py                      # Flask REST API with Swagger
├── swagger.yaml                    # OpenAPI 3.0 specification
├── project_proposal.md             # Project overview and objectives
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Implementation Details

### Feature Extraction

The `FeatureExtractor` class normalizes provider attributes to a consistent [0,1] scale:

- **Distance**: Inverted and capped at 100 miles (closer = higher value)
- **Wait time**: Inverted and capped at 30 days (shorter = higher value)
- **Ratings**: Linear normalization from 0-5 to 0-1
- **Reviews**: Log-scale normalization (handles wide range)
- **Experience**: Linear normalization, capped at 50 years
- **Boolean features**: 1.0 if true, 0.0 if false

### Re-ranking Algorithm

```python
def rerank(baseline_results, provider_data, persona_id, alpha=0.5):
    for result in baseline_results:
        # Extract normalized features
        features = feature_extractor.extract(provider)

        # Compute persona score
        persona_score = sum(features[f] * weights[f]
                          for f in weights)

        # Normalize baseline score to [0,1]
        normalized_baseline = normalize(result.score)

        # Combine scores
        combined = alpha * normalized_baseline + (1-alpha) * persona_score

    # Sort by combined score
    return sorted(results, key=lambda x: x.combined_score, reverse=True)
```

### Baseline Retrieval

**BM25 Configuration**:
- k1 = 0.9 (term frequency saturation parameter)
- b = 0.4 (length normalization parameter)
- Top-100 retrieval for re-ranking candidate set

**Query Likelihood Configuration**:
- Dirichlet smoothing with μ = 1000
- Alternative ranking method for comparison

Both methods index the `search_text` field, which concatenates:
- Provider name
- Specialty (readable format)
- City and state
- Additional searchable attributes

## Troubleshooting

### Common Issues

**Port already in use**:
```bash
lsof -i :5000
# Kill the process or change port in api.py
```

**Java not found**:
```bash
# macOS
export JAVA_HOME=$(/usr/libexec/java_home)

# Linux
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

**Index corruption**:
```bash
rm -rf indexes/provider_index/
python src/api.py  # Rebuilds on startup
```

**Missing data files**:
```bash
git lfs pull
```

**Invalid persona error**:
Valid persona IDs are: `sarah`, `marcus`, `fatima`, `robert`, `jennifer` (case-sensitive, lowercase)

## Team

**UIUC CS410 - Information Retrieval**

- **Michael Antry** - Service architecture, API integration
- **Dean Fletcher** - Data Engineering and Processing, Data Collection
- **Jordan Alwan** - UI/demo development
- **Janani Jayanth** - Feature engineering, QL baseline

## References

- **Pyserini Documentation**: https://github.com/castorini/pyserini
- **BM25 Algorithm**: Robertson & Zaragoza (2009)
- **Query Likelihood**: Zhai & Lafferty (2004)
- **OpenAPI Specification**: https://swagger.io/specification/

## Future Work

- Implement learning-to-rank for persona weight optimization
- Add user feedback loop to refine persona weights
- Expand persona set based on user clustering
- Implement A/B testing framework for ranking evaluation
- Add real-time personalization based on click behavior
- Extend to additional geographic regions
- Implement hybrid retrieval (dense + sparse)

---

**License**: Academic use only - UIUC CS410 course project
