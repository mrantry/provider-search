# Provider Search

A search application for finding healthcare providers using baseline retrieval methods (BM25 and Query Likelihood).

## Overview

This project provides baseline retrieval functionality to find healthcare providers from Illinois provider data. It uses Pyserini (a Python interface to Anserini) for efficient full-text search with multiple retrieval methods. The system retrieves top 100 candidates per query for use in evaluation and downstream re-ranking tasks.

## Features

- **BM25 Retrieval**: Fast and accurate retrieval using the BM25 ranking algorithm
- **Query Likelihood (Dirichlet)**: Language modeling retrieval with Dirichlet smoothing
- **Top 100 Candidates**: Retrieves top 100 results per query (configurable)
- **JSON Output**: Writes complete results to `output.json` for evaluation
- **Automatic Indexing**: Index is built automatically on first run
- **Multiple Retrieval Methods**: Support for BM25 and Query Likelihood with Dirichlet smoothing

## Prerequisites

- **Python 3.8+**
- **Java 11+** (required for Pyserini/Anserini)
  - Check your Java version: `java -version`
  - Install Java if needed:
    - macOS: `brew install openjdk@11`
    - Linux: `sudo apt-get install openjdk-11-jdk` (Ubuntu/Debian)
    - Windows: Download from [Oracle](https://www.oracle.com/java/technologies/downloads/) or use [Adoptium](https://adoptium.net/)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd provider-search
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

Or if using conda:

```bash
conda install -c conda-forge pyserini
```

### 3. Download and prepare the data

1. Download the cleaned provider data zip file (from releases or data source)
2. Unzip the data file into the `data/` directory:

```bash
# Create data directory if it doesn't exist
mkdir -p data

# Unzip the data file (adjust filename as needed)
unzip providers_illinois.zip -d data/

# Verify the data file exists
ls data/providers_illinois.jsonl
```

The expected data structure:
```
data/
  └── providers_illinois.jsonl
```

**Note**: The `providers_illinois.jsonl` file should be in JSONL format (one JSON object per line) with the following key fields:
- `NPI`: Provider National Provider Identifier (used as document ID)
- `search_text`: Searchable text content for the provider
- Other provider metadata fields

## Usage

### Basic Search

Run the search script with a query string:

```bash
cd src
python baseline_retrieval.py "cardiologist in Chicago"
```

By default, this uses BM25 retrieval and returns top 100 results.

### Command-Line Options

```bash
# Use BM25 (default)
python baseline_retrieval.py "cardiologist" --method bm25

# Use Query Likelihood with Dirichlet smoothing
python baseline_retrieval.py "cardiologist" --method ql_dirichlet

# Custom number of results
python baseline_retrieval.py "pediatrician" --k 50

# Combine options
python baseline_retrieval.py "dermatologist" --method ql_dirichlet --k 100
```

**Options:**
- `--method`: Retrieval method (`bm25` or `ql_dirichlet`, default: `bm25`)
- `--k`: Number of results to retrieve (default: 100)

### Example Queries

```bash
# Search by specialty and location (BM25, top 100)
python baseline_retrieval.py "pediatrician in Springfield"

# Search by specialty and service (QL-Dirichlet, top 100)
python baseline_retrieval.py "cardiologist telehealth" --method ql_dirichlet

# Search by specialty only (BM25, top 50)
python baseline_retrieval.py "dermatologist" --k 50
```

### Output

The script provides two types of output:

1. **Console Output**: Displays top 5 results with:
   - Provider ID (NPI)
   - Relevance score
   - Full search text content

2. **JSON Output**: Complete results written to `output.json` in the repository root:
   - All retrieved results (up to k)
   - Query, method, and result count
   - Ranked list with provider IDs and scores

**Console Example:**
```
Searching for: 'cardiologist in Chicago'
Method: BM25, Retrieving top 100 results
==================================================

✓ Results written to /path/to/output.json
  Method: bm25, Results: 100

Top 5 results (showing 5 of 100):

1. Provider ID: 1053362004, Score: 5.2382
   Search Text: Michael Earing | Pediatric Cardiology Physician | CHICAGO | IL | ...

2. Provider ID: 1043535503, Score: 5.2208
   Search Text: Stephanie Chandler | MD | Pediatric Cardiology Physician | CHICAGO | IL | ...
```

**JSON Output Format (`output.json`):**
```json
{
  "query": "cardiologist in Chicago",
  "method": "bm25",
  "num_results": 100,
  "results": [
    {
      "rank": 1,
      "provider_id": "1053362004",
      "score": 5.2382
    },
    {
      "rank": 2,
      "provider_id": "1043535503",
      "score": 5.2208
    },
    ...
  ]
}
```

### First Run

On the first run, the script will automatically build the search index from the JSONL data file. This process:
- Reads all documents from `data/providers_illinois.jsonl`
- Creates a Lucene index in `indexes/provider_index/`
- May take a few minutes for large datasets (~300k documents)

Subsequent runs will use the existing index for fast searches.

## Project Structure

```
provider-search/
├── data/
│   └── providers_illinois.jsonl    # Provider data (not in git, user must provide)
├── indexes/
│   └── provider_index/              # Auto-generated search index
├── src/
│   └── baseline_retrieval.py       # Main search script
├── output.json                      # Results output (not in git, overwritten on each run)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Configuration

### Custom Index Location

You can specify a custom index directory using an environment variable:

```bash
export PROVIDER_INDEX_DIR="/path/to/custom/index"
python baseline_retrieval.py "your query"
```

### Retrieval Method Parameters

**BM25 Parameters:**
- `k1=0.9` (term frequency saturation)
- `b=0.4` (length normalization)
- Default `k=100` (number of results)

**Query Likelihood (Dirichlet) Parameters:**
- `mu=1000.0` (Dirichlet smoothing parameter)
- Default `k=100` (number of results)

These can be modified in the `ProviderSearchEngine` class methods if needed.

### Output File

Results are written to `output.json` in the repository root. The file is overwritten on each run. To preserve results, rename or copy the file before running a new query.

## Development

### Running Tests

Running the script without arguments shows usage information:

```bash
python baseline_retrieval.py
```

This displays:
- Usage instructions
- Available methods
- Command-line options
- Example commands

### Retrieval Methods

The system supports two baseline retrieval methods:

1. **BM25**: Best Match 25 ranking function
   - Default parameters: `k1=0.9`, `b=0.4`
   - Good for general-purpose retrieval

2. **Query Likelihood (Dirichlet)**: Language modeling approach with Dirichlet smoothing
   - Default parameter: `mu=1000.0`
   - Alternative ranking approach for comparison

Both methods retrieve top 100 candidates by default, suitable for evaluation and downstream re-ranking tasks.

## Troubleshooting

### Java Not Found

If you see Java-related errors:
```bash
# Check Java installation
java -version

# Set JAVA_HOME if needed (macOS example)
export JAVA_HOME=$(/usr/libexec/java_home)
```

### Index Build Fails

If index building fails:
- Ensure the data file exists at `data/providers_illinois.jsonl`
- Check file permissions
- Verify the JSONL format is valid (one JSON object per line)

### Import Errors

If pyserini import fails:
```bash
# Reinstall pyserini
pip uninstall pyserini
pip install pyserini
```

