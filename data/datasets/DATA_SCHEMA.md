# Data Schema Documentation

## Provider Data Schema

This document describes the schema for the provider dataset.

---

## Input Data Sources

### 1. NPI Registry (Primary Source)

**Source:** CMS National Plan and Provider Enumeration System (NPPES)  
**URL:** https://download.cms.gov/nppes/NPI_Files.html  
**Format:** CSV (tab-delimited or comma-delimited)  
**Size:** ~7-8 GB uncompressed, 8M+ records

#### Key Input Columns

| Column Name | Type | Description | Example |
|------------|------|-------------|---------|
| `NPI` | String | 10-digit unique provider identifier | "1234567890" |
| `Provider Last Name (Legal Name)` | String | Provider's legal last name | "Smith" |
| `Provider First Name` | String | Provider's first name | "John" |
| `Provider Credential Text` | String | Medical credentials | "MD", "DO", "NP" |
| `Healthcare Provider Taxonomy Code_1` | String | Primary specialty code | "207R00000X" |
| `Provider Enumeration Date` | Date | Date NPI was issued | "2010-05-15" |
| `Provider Business Practice Location Address` | String | Street address | "123 Main St" |
| `Provider Business Practice Location Address City Name` | String | City | "Chicago" |
| `Provider Business Practice Location Address State Name` | String | State code | "IL" |
| `Provider Business Practice Location Address Postal Code` | String | ZIP code | "60601" |

#### NPI Taxonomy Codes
The Healthcare Provider Taxonomy Code follows the NUCC (National Uniform Claim Committee) standard:
- Format: 10 alphanumeric characters (e.g., `207R00000X`)
- First section: Provider type
- Complete list: http://www.nucc.org/index.php/code-sets-mainmenu-41/provider-taxonomy-mainmenu-40

---

## Output Data Schema

### Provider Table Specification

This is the final schema for indexing and re-ranking.

#### Core Identifiers

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `NPI` | string | No | Unique 10-digit provider identifier (primary key) |
| `provider_name_normalized` | string | No | Full name, cleaned and title-cased |

#### Text Fields (For Indexing)

| Field | Type | Nullable | Description | Indexed? |
|-------|------|----------|-------------|----------|
| `specialty_normalized` | string | No | Lowercase specialty string | Yes |
| `specialty_category` | string | No | Mapped specialty category (e.g., "Primary Care") | Yes |
| `text_description` | string | No | Concatenated searchable text | Yes (primary) |

**text_description format:**
```
[provider_name] | [specialty] | [address] | [additional info]
Example: "John Smith | cardiology | 123 Main St, Chicago, IL 60601 | Languages: Spanish | Telehealth available"
```

#### Location Features

| Field | Type | Nullable | Range | Description |
|-------|------|----------|-------|-------------|
| `full_address` | string | Yes | - | Complete formatted address |
| `zip_code` | string | Yes | 5 digits | 5-digit ZIP code |
| `distance_miles` | float | Yes | 0-5000 | Distance from reference location (miles) |

#### Experience & Qualifications

| Field | Type | Nullable | Range | Description |
|-------|------|----------|-------|-------------|
| `years_since_enumeration` | integer | Yes | 0-50 | Years since NPI enumeration (experience proxy) |

**Rationale:** NPI enumeration date ≈ start of practice. Capped at 50 years as a reasonable maximum.

#### Service Availability Features

| Field | Type | Nullable | Values | Description |
|-------|------|----------|--------|-------------|
| `telehealth_available` | boolean | No | True/False | Offers virtual visits |
| `evening_hours` | boolean | No | True/False | Available after 5 PM |
| `weekend_hours` | boolean | No | True/False | Available Saturday/Sunday |
| `accepting_new_patients` | boolean | No | True/False | Currently accepting new patients |

**Note:** For MVP, these are synthetic (probabilistically generated). Replace with real data when available.

#### Language Features

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `speaks_spanish` | boolean | No | Provides services in Spanish |
| `speaks_chinese` | boolean | No | Provides services in Chinese |

**Note:** Additional language columns can be added as needed.

---

## File Formats

### 1. CSV Format

**Filename:** `providers_illinois.csv`  
**Encoding:** UTF-8  
**Delimiter:** Comma (`,`)  
**Header:** Yes (first row)  
**Quote character:** Double quotes (`"`)

**Example:**
```csv
NPI,provider_name_normalized,specialty_normalized,text_description,distance_miles,telehealth_available
1234567890,John Smith,cardiology,"John Smith | cardiology | Chicago, IL",5.3,True
```

### 2. JSONL Format (Indexing)

**Filename:** `providers_illinois.jsonl`  
**Format:** One JSON object per line  
**Encoding:** UTF-8

**Example:**
```json
{"NPI": "1234567890", "provider_name_normalized": "John Smith", "specialty_normalized": "cardiology", "text_description": "John Smith | cardiology | Chicago, IL", "distance_miles": 5.3, "telehealth_available": true}
{"NPI": "0987654321", "provider_name_normalized": "Jane Doe", "specialty_normalized": "pediatrics", "text_description": "Jane Doe | pediatrics | Evanston, IL", "distance_miles": 12.1, "telehealth_available": false}
```

---

## References

- [NPI Registry Data Dictionary](https://download.cms.gov/nppes/NPI_Files.html)
- [NUCC Taxonomy Codes](http://www.nucc.org/index.php/code-sets-mainmenu-41/provider-taxonomy-mainmenu-40)
- [Geopy Documentation](https://geopy.readthedocs.io/)
- [pandas Data Types](https://pandas.pydata.org/docs/user_guide/basics.html#dtypes)
