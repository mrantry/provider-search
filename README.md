# Provider Search

A search application for finding healthcare providers using BM25 retrieval.

## Overview

This project provides BM25-based search functionality to find healthcare providers from Illinois provider data. It uses Pyserini (a Python interface to Anserini) for efficient full-text search.

## Features

- **BM25 Search**: Fast and accurate retrieval using the BM25 ranking algorithm
- **Automatic Indexing**: Index is built automatically on first run
- **Top-K Results**: Returns top 5 most relevant providers for each query
- **Full Document Retrieval**: Displays complete provider information including search text

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

### Example Queries

```bash
# Search by specialty and location
python baseline_retrieval.py "pediatrician in Springfield"

# Search by specialty and service
python baseline_retrieval.py "cardiologist telehealth"

# Search by specialty only
python baseline_retrieval.py "dermatologist"
```

### Output

The script returns the top 5 results with:
- Provider ID (NPI)
- BM25 relevance score
- Full search text content

Example output:
```
Searching for: 'cardiologist in Chicago'
==================================================
Top 5 results:

1. Provider ID: 1053362004, Score: 5.2382
   Search Text: Michael Earing | Pediatric Cardiology Physician | CHICAGO | IL | ...

2. Provider ID: 1043535503, Score: 5.2208
   Search Text: Stephanie Chandler | MD | Pediatric Cardiology Physician | CHICAGO | IL | ...
...
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

### BM25 Parameters

The default BM25 parameters are:
- `k1=0.9` (term frequency saturation)
- `b=0.4` (length normalization)

These can be modified in the `ProviderSearchEngine.bm25_search()` method if needed.

## Development

### Running Tests

Currently, running the script without arguments shows setup verification:

```bash
python baseline_retrieval.py
```

This will:
- Verify Python environment
- Check pyserini installation
- Validate class structure
- Test index initialization (if index exists)

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

