"""
NPI Data Pipeline - State Filtering
Processes full 11GB dataset efficiently with state filtering
Uses taxonomy_reference.csv for specialty lookups
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import urllib.request
import zipfile
import io
import random

class ProductionNPIProcessor:
    """Pipeline with state filtering, chunk processing, and appointment/rating features"""
    
    def __init__(self, states=None, reference_location=(41.8781, -87.6298), 
                 taxonomy_file='data/processed/taxonomy_reference.csv', 
                 zip_centroids_file='data/processed/il_zip_centroids.csv'):
        """
        Initialize processor
        
        Args:
            states: List of state codes to include (e.g., ['IL', 'NY', 'CA'])
                   If None, includes all states
            reference_location: (lat, lon) for distance calculations. Default: Chicago downtown
            taxonomy_file: Path to taxonomy reference CSV
            zip_centroids_file: Path to ZIP code centroid lookup
        """
        self.states = [s.upper() for s in states] if states else None
        self.reference_location = reference_location
        
        # Load ZIP code centroids for distance calculation
        self.zip_centroids = {}
        try:
            zip_df = pd.read_csv(zip_centroids_file)
            self.zip_centroids = dict(zip(
                zip_df['zip_code'].astype(str).str[:5],
                zip(zip_df['latitude'], zip_df['longitude'])
            ))
            print(f"Loaded {len(self.zip_centroids)} ZIP code centroids from {zip_centroids_file}")
        except FileNotFoundError:
            print(f"Warning: ZIP centroid file not found: {zip_centroids_file}")
            print("Distance will be NULL unless auto creation succeeds.")
        except Exception as e:
            print(f"Warning: Error loading ZIP centroids: {e}")
        
        if not self.zip_centroids:
            print("Creating ZIP centroids file from US Census data...")
            url = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_zcta_national.zip"
            try:
                with urllib.request.urlopen(url) as response:
                    with zipfile.ZipFile(io.BytesIO(response.read())) as z:
                        txt_files = [name for name in z.namelist() if name.endswith('.txt')]
                        if not txt_files:
                            raise ValueError("No TXT file in ZIP")
                        with z.open(txt_files[0]) as f:
                            df = pd.read_csv(f, sep='|', usecols=['GEOID', 'INTPTLAT', 'INTPTLONG'], dtype={'GEOID': str, 'INTPTLAT': float, 'INTPTLONG': float})
                df.rename(columns={'GEOID': 'zip_code', 'INTPTLAT': 'latitude', 'INTPTLONG': 'longitude'}, inplace=True)
                # Filter to IL if states include 'IL'
                if self.states and 'IL' in self.states:
                    df = df[(df['zip_code'].astype(int) >= 60000) & (df['zip_code'].astype(int) <= 62999)]
                df.to_csv(zip_centroids_file, index=False)
                self.zip_centroids = dict(zip(
                    df['zip_code'],
                    zip(df['latitude'], df['longitude'])
                ))
                print(f"Created {zip_centroids_file} with {len(self.zip_centroids)} entries")
            except Exception as e:
                print(f"Error creating ZIP centroids: {e}")
                print("Continuing without distances")
        
        # Column names
        self.COL_NPI = 'NPI'
        self.COL_FIRST_NAME = 'Provider First Name'
        self.COL_LAST_NAME = 'Provider Last Name (Legal Name)'
        self.COL_ORG_NAME = 'Provider Organization Name (Legal Business Name)'
        self.COL_CREDENTIAL = 'Provider Credential Text'
        self.COL_ADDRESS_1 = 'Provider First Line Business Practice Location Address'
        self.COL_ADDRESS_2 = 'Provider Second Line Business Practice Location Address'
        self.COL_CITY = 'Provider Business Practice Location Address City Name'
        self.COL_STATE = 'Provider Business Practice Location Address State Name'
        self.COL_ZIP = 'Provider Business Practice Location Address Postal Code'
        self.COL_TAXONOMY = 'Healthcare Provider Taxonomy Code_1'
        self.COL_ENUM_DATE = 'Provider Enumeration Date'
        self.COL_GENDER = 'Provider Sex Code'
        self.COL_ENTITY_TYPE = 'Entity Type Code'
        
        # Insurance networks for synthetic data
        self.insurance_networks = [
            'Blue Cross Blue Shield',
            'UnitedHealthcare',
            'Aetna',
            'Cigna',
            'Humana',
            'Medicare',
            'Medicaid'
        ]
        
        # Load taxonomy reference
        self.load_taxonomy_reference(taxonomy_file)
    
    def load_taxonomy_reference(self, taxonomy_file):
        """Load taxonomy reference from CSV"""
        try:
            self.taxonomy_df = pd.read_csv(taxonomy_file)
            
            # Create lookup dictionary: Code -> Display Name
            self.taxonomy_map = dict(zip(
                self.taxonomy_df['Code'],
                self.taxonomy_df['Display Name']
            ))
            
            # Store full info for text search
            # Create searchable text: Classification + Specialization + Definition
            self.taxonomy_df['search_text'] = (
                self.taxonomy_df['Classification'].fillna('') + ' ' +
                self.taxonomy_df['Specialization'].fillna('') + ' ' +
                self.taxonomy_df['Definition'].fillna('')
            ).str.lower()
            
            print(f"Loaded {len(self.taxonomy_map)} taxonomy codes from {taxonomy_file}")
            
        except FileNotFoundError:
            print(f"Warning: Taxonomy file not found: {taxonomy_file}")
            print("Using empty taxonomy map. All specialties will show as 'Other Healthcare Provider'")
            self.taxonomy_map = {}
            self.taxonomy_df = pd.DataFrame()
    
    def get_specialty_info(self, code):
        """
        Get specialty information for a taxonomy code
        Returns: (display_name, grouping, classification, specialization)
        """
        if code in self.taxonomy_map:
            row = self.taxonomy_df[self.taxonomy_df['Code'] == code].iloc[0]
            return (
                row.get('Display Name', 'Other Healthcare Provider'),
                row.get('Grouping', ''),
                row.get('Classification', ''),
                row.get('Specialization', '')
            )
        return ('Other Healthcare Provider', '', '', '')
    
    def generate_rating_features(self, chunk):
        """
        Generate realistic rating and review features
        
        Features:
        - average_rating: 1.0-5.0 stars (beta distribution, skewed high)
        - num_reviews: Number of reviews (correlated with experience)
        - has_rating: Boolean flag for whether provider has been rated
        """
        n = len(chunk)
        
        # Beta distribution for ratings (skewed towards 4.0-4.5)
        alpha, beta = 8, 2
        raw_ratings = np.random.beta(alpha, beta, n)
        ratings = 1.0 + (raw_ratings * 4.0)
        ratings = np.round(ratings, 1)
        
        # ~5% of providers have no ratings (new providers)
        has_rating = np.random.random(n) > 0.05
        
        # Number of reviews (correlated with years of experience)
        if 'years_experience' in chunk.columns:
            base_reviews = chunk['years_experience'] * np.random.uniform(5, 20, n)
            num_reviews = base_reviews.astype(int)
        else:
            num_reviews = np.random.randint(0, 200, n)
        
        # Apply has_rating mask
        ratings[~has_rating] = np.nan
        num_reviews[~has_rating] = 0
        
        chunk['average_rating'] = ratings
        chunk['num_reviews'] = num_reviews
        chunk['has_rating'] = has_rating
        
        return chunk
    
    def generate_appointment_features(self, chunk):
        """
        Generate realistic appointment availability features
        
        Features:
        - wait_days: Days until soonest appointment
        - soonest_appointment_date: Actual date of soonest appointment
        - appointments_available_7days: Number of slots in next 7 days
        - appointments_available_14days: Number of slots in next 14 days
        - appointments_available_30days: Number of slots in next 30 days
        - availability_score: 0-1 score (inverse of wait time)
        
        Logic:
        - Higher-rated providers → longer wait times
        - New providers (no rating) → shorter wait times
        """
        n = len(chunk)
        today = datetime.now()
        
        def calculate_wait_days(rating, has_rating):
            """Calculate wait days based on rating"""
            if not has_rating or pd.isna(rating):
                # New providers: 1-7 days
                return random.randint(1, 7)
            
            if rating >= 4.5:
                # Highly rated: 7-30 days
                return random.randint(7, 30)
            elif rating >= 4.0:
                # Good rated: 3-14 days
                return random.randint(3, 14)
            elif rating >= 3.5:
                # Average: 1-10 days
                return random.randint(1, 10)
            else:
                # Lower rated: 1-5 days (more available)
                return random.randint(1, 5)
        
        # Calculate wait days for each provider
        wait_days = []
        for _, row in chunk.iterrows():
            rating = row.get('average_rating', np.nan)
            has_rating = row.get('has_rating', False)
            wait_days.append(calculate_wait_days(rating, has_rating))
        
        chunk['wait_days'] = wait_days
        
        # Calculate soonest appointment date
        chunk['soonest_appointment_date'] = [
            (today + timedelta(days=int(wd))).strftime('%Y-%m-%d')
            for wd in wait_days
        ]
        
        # Generate appointment slots for different time windows
        def generate_slots(wait_days, window_days):
            """Generate number of available slots in a time window"""
            if wait_days >= window_days:
                return 0
            
            available_days = window_days - wait_days
            slots_per_day = random.uniform(2, 8)
            capacity_factor = random.uniform(0.3, 0.8)
            total_slots = int(available_days * slots_per_day * capacity_factor)
            
            return max(0, total_slots)
        
        chunk['appointments_available_7days'] = [
            generate_slots(wd, 7) for wd in wait_days
        ]
        
        chunk['appointments_available_14days'] = [
            generate_slots(wd, 14) for wd in wait_days
        ]
        
        chunk['appointments_available_30days'] = [
            generate_slots(wd, 30) for wd in wait_days
        ]
        
        # Calculate availability score (0-1, inverse of wait time)
        max_wait = max(wait_days) if wait_days else 30
        chunk['availability_score'] = [
            1 - (wd / max_wait) for wd in wait_days
        ]
        
        return chunk
    
    def generate_insurance_features(self, chunk):
        """
        Generate insurance network features
        
        Features:
        - accepted_networks: List of accepted insurance networks
        - network_breadth: Percentage of major networks accepted (0-1)
        - in_network_bcbs: Boolean for Blue Cross Blue Shield
        - in_network_uhc: Boolean for UnitedHealthcare
        - accepts_medicare: Boolean for Medicare
        - accepts_medicaid: Boolean for Medicaid
        """
        n = len(chunk)
        
        # Each provider accepts 2-6 networks randomly
        accepted_networks = [
            random.sample(self.insurance_networks, k=random.randint(2, 6))
            for _ in range(n)
        ]
        
        chunk['accepted_networks'] = [
            ','.join(networks) for networks in accepted_networks
        ]
        
        # Calculate network breadth
        chunk['network_breadth'] = [
            len(networks) / len(self.insurance_networks)
            for networks in accepted_networks
        ]
        
        # Create boolean flags for major insurers
        chunk['in_network_bcbs'] = [
            'Blue Cross Blue Shield' in networks
            for networks in accepted_networks
        ]
        
        chunk['in_network_uhc'] = [
            'UnitedHealthcare' in networks
            for networks in accepted_networks
        ]
        
        chunk['accepts_medicare'] = [
            'Medicare' in networks
            for networks in accepted_networks
        ]
        
        chunk['accepts_medicaid'] = [
            'Medicaid' in networks
            for networks in accepted_networks
        ]
        
        return chunk
    
    def process_chunk(self, chunk):
        """Process a single chunk of data"""
        
        # Filter by state if specified
        if self.states:
            chunk = chunk[chunk[self.COL_STATE].isin(self.states)].copy()
        else:
            chunk = chunk.copy()
        
        if len(chunk) == 0:
            return None
        
        # Create provider name
        chunk['provider_name'] = ''
        mask_individual = chunk[self.COL_ENTITY_TYPE] == 1
        chunk.loc[mask_individual, 'provider_name'] = (
            chunk.loc[mask_individual, self.COL_FIRST_NAME].fillna('').str.strip() + ' ' +
            chunk.loc[mask_individual, self.COL_LAST_NAME].fillna('').str.strip()
        ).str.strip().str.title()
        
        mask_org = chunk[self.COL_ENTITY_TYPE] == 2
        chunk.loc[mask_org, 'provider_name'] = (
            chunk.loc[mask_org, self.COL_ORG_NAME].fillna('').str.strip().str.title()
        )
        
        # Normalize specialty using taxonomy reference
        chunk['specialty_code'] = chunk[self.COL_TAXONOMY].fillna('')
        chunk['specialty_readable'] = chunk['specialty_code'].map(self.taxonomy_map)
        chunk['specialty_readable'] = chunk['specialty_readable'].fillna('Other Healthcare Provider')
        
        # Get additional taxonomy info for better search
        def get_taxonomy_search_text(code):
            if code in self.taxonomy_map:
                row = self.taxonomy_df[self.taxonomy_df['Code'] == code]
                if len(row) > 0:
                    return row.iloc[0]['search_text']
            return ''
        
        chunk['specialty_search_text'] = chunk['specialty_code'].apply(get_taxonomy_search_text)
        
        # Create address
        chunk['full_address'] = (
            chunk[self.COL_ADDRESS_1].fillna('').astype(str).str.strip() + ', ' +
            chunk[self.COL_CITY].fillna('').astype(str).str.strip() + ', ' +
            chunk[self.COL_STATE].fillna('').astype(str).str.strip() + ' ' +
            chunk[self.COL_ZIP].fillna('').astype(str).str.strip()
        ).str.strip(', ')
        chunk['zip_5'] = chunk[self.COL_ZIP].astype(str).str[:5]
        
        # Calculate experience
        chunk['enumeration_date'] = pd.to_datetime(chunk[self.COL_ENUM_DATE], errors='coerce')
        current_year = datetime.now().year
        chunk['years_experience'] = current_year - chunk['enumeration_date'].dt.year
        chunk['years_experience'] = chunk['years_experience'].clip(lower=0, upper=50)
        
        # Calculate distance from reference location
        from geopy.distance import geodesic
        
        def calc_distance(zip_code):
            """Calculate distance from reference point using ZIP centroid"""
            if pd.isna(zip_code):
                return None
            
            zip_5 = str(zip_code)[:5]
            
            if zip_5 in self.zip_centroids:
                provider_coords = self.zip_centroids[zip_5]
                try:
                    return geodesic(self.reference_location, provider_coords).miles
                except:
                    return None
            return None
        
        chunk['distance_miles'] = chunk['zip_5'].apply(calc_distance)
        
        # =====================================================================
        # SYNTHETIC FEATURES
        # =====================================================================
        
        # Telehealth (specialty-dependent)
        specialty_telehealth = {
            'Family Medicine': 0.7,
            'Internal Medicine': 0.7,
            'Psychiatry': 0.8,
            'Psychologist': 0.9,
            'Pediatrics': 0.6
        }
        
        chunk['telehealth_available'] = chunk['specialty_readable'].map(
            lambda x: np.random.random() < specialty_telehealth.get(x, 0.4)
        )
        
        chunk['speaks_spanish'] = np.random.random(len(chunk)) < 0.15
        chunk['speaks_chinese'] = np.random.random(len(chunk)) < 0.05
        chunk['evening_hours'] = np.random.random(len(chunk)) < 0.3
        chunk['weekend_hours'] = np.random.random(len(chunk)) < 0.2
        chunk['accepting_new_patients'] = np.random.random(len(chunk)) < 0.7
        
        # Generate rating features (must come before appointment features)
        chunk = self.generate_rating_features(chunk)
        
        # Generate appointment features (depends on ratings)
        chunk = self.generate_appointment_features(chunk)
        
        # Generate insurance features
        chunk = self.generate_insurance_features(chunk)
        
        # =====================================================================
        # CREATE SEARCH TEXT
        # =====================================================================
        
        def build_text(row):
            parts = [
                row['provider_name'],
                row['specialty_readable'],
                row[self.COL_CITY] if pd.notna(row[self.COL_CITY]) else '',
                row[self.COL_STATE] if pd.notna(row[self.COL_STATE]) else ''
            ]
            
            if pd.notna(row[self.COL_CREDENTIAL]) and row[self.COL_CREDENTIAL]:
                parts.insert(1, row[self.COL_CREDENTIAL])
            
            # Add specialty search text (includes classification, specialization, definition)
            if row.get('specialty_search_text', ''):
                parts.append(row['specialty_search_text'])
            
            features = []
            if row.get('telehealth_available', False):
                features.append('telehealth')
            if row.get('speaks_spanish', False):
                features.append('Spanish')
            if row.get('evening_hours', False):
                features.append('evening hours')
            if row.get('accepts_medicare', False):
                features.append('Medicare')
            
            if features:
                parts.append(' '.join(features))
            
            return ' | '.join(filter(None, parts))
        
        chunk['search_text'] = chunk.apply(build_text, axis=1)
        
        # =====================================================================
        # SELECT FINAL COLUMNS
        # =====================================================================
        
        final_cols = [
            # Identity
            self.COL_NPI,
            'provider_name',
            'specialty_readable',
            'specialty_code',
            
            # Location
            'full_address',
            self.COL_CITY,
            self.COL_STATE,
            'zip_5',
            'distance_miles',
            
            # Experience
            'years_experience',
            
            # Rating & Reviews
            'average_rating',
            'num_reviews',
            'has_rating',
            
            # Appointment Availability
            'wait_days',
            'soonest_appointment_date',
            'appointments_available_7days',
            'appointments_available_14days',
            'appointments_available_30days',
            'availability_score',
            
            # Insurance Networks
            'accepted_networks',
            'network_breadth',
            'in_network_bcbs',
            'in_network_uhc',
            'accepts_medicare',
            'accepts_medicaid',
            
            # Other Features
            'telehealth_available',
            'speaks_spanish',
            'speaks_chinese',
            'evening_hours',
            'weekend_hours',
            'accepting_new_patients',
            
            # Search
            'search_text',
            
            # Metadata
            self.COL_CREDENTIAL,
            self.COL_GENDER
        ]
        
        final_cols = [col for col in final_cols if col in chunk.columns]
        result = chunk[final_cols].copy()
        
        # Remove empty names
        result = result[result['provider_name'].notna() & (result['provider_name'] != '')]
        
        return result
    
    def process_full_dataset(self, input_file, output_prefix, chunk_size=50000):
        """Process the full dataset in chunks"""
        
        # Show file size and estimate
        file_size_gb = os.path.getsize(input_file) / (1024**3)
        print(f"File size: {file_size_gb:.2f} GB")
        estimated_total_rows = int(file_size_gb * 730000)  # ~730k rows per GB
        print(f"Estimated rows: ~{estimated_total_rows:,}")
        
        print(f"Chunk size: {chunk_size:,} rows")
        if self.states:
            print(f"Filtering to states: {', '.join(self.states)}")
        else:
            print("Processing all states")
        print()
        
        # Create output directory
        output_dir = os.path.dirname(output_prefix) if os.path.dirname(output_prefix) else '.'
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize outputs
        csv_path = f"{output_prefix}.csv"
        jsonl_path = f"{output_prefix}.jsonl"
        
        total_processed = 0
        total_kept = 0
        chunk_num = 0
        
        # Open output files
        csv_file = open(csv_path, 'w', encoding='utf-8')
        jsonl_file = open(jsonl_path, 'w', encoding='utf-8')
        header_written = False
        
        import time
        start_time = time.time()
        
        try:
            # Process in chunks
            for chunk in pd.read_csv(input_file, chunksize=chunk_size, low_memory=False):
                chunk_num += 1
                total_processed += len(chunk)
                
                # Process chunk
                processed = self.process_chunk(chunk)
                
                if processed is not None and len(processed) > 0:
                    total_kept += len(processed)
                    
                    # Write CSV
                    processed.to_csv(csv_file, index=False, header=not header_written, lineterminator='\n')
                    if not header_written:
                        header_written = True
                    
                    # Write JSONL
                    processed.to_json(jsonl_file, orient='records', lines=True)
                
                # Calculate progress
                elapsed = time.time() - start_time
                pct_complete = (total_processed / estimated_total_rows * 100) if estimated_total_rows > 0 else 0
                rows_per_sec = total_processed / elapsed if elapsed > 0 else 0
                eta_seconds = (estimated_total_rows - total_processed) / rows_per_sec if rows_per_sec > 0 else 0
                eta_minutes = eta_seconds / 60
                
                kept_count = len(processed) if processed is not None else 0
                
                print(f"Chunk {chunk_num:4d} | Rows: {total_processed:8,} / ~{estimated_total_rows:,} ({pct_complete:5.1f}%) | "
                      f"Kept: {total_kept:8,} | ETA: {eta_minutes:5.1f} min", end='\r')
                
        finally:
            csv_file.close()
            jsonl_file.close()
        
        elapsed_total = time.time() - start_time
        
        print()
        print("-"*80)
        print(f"\nProcessing complete!")
        print(f"\nTotal time: {elapsed_total/60:.1f} minutes")
        print(f"Total rows processed: {total_processed:,}")
        print(f"Total rows kept: {total_kept:,}")
        print(f"Filter rate: {(total_kept/total_processed*100):.1f}%")
        
        # File sizes
        csv_size = os.path.getsize(csv_path) / (1024 * 1024)
        jsonl_size = os.path.getsize(jsonl_path) / (1024 * 1024)
        
        print(f"\nOutput files:")
        print(f"  CSV:   {csv_path} ({csv_size:.1f} MB)")
        print(f"  JSONL: {jsonl_path} ({jsonl_size:.1f} MB)")
        
        # Print summary
        self.print_summary(csv_path)
        
        return csv_path, jsonl_path
    
    def print_summary(self, csv_path):
        """Print summary statistics from output file"""
        
        # Read a sample for statistics
        df = pd.read_csv(csv_path, nrows=10000)
        
        print(f"\nSample size: {len(df):,} rows (showing stats from first 10k)")
        
        print(f"\nTop 10 Specialties:")
        print(df['specialty_readable'].value_counts().head(10))
        
        if self.COL_STATE in df.columns:
            print(f"\nStates:")
            print(df[self.COL_STATE].value_counts())
        
        if 'years_experience' in df.columns:
            print(f"\nExperience Distribution:")
            exp_stats = df['years_experience'].describe()
            print(f"  Mean: {exp_stats['mean']:.1f} years")
            print(f"  Median: {exp_stats['50%']:.1f} years")
            print(f"  Min: {exp_stats['min']:.0f} years")
            print(f"  Max: {exp_stats['max']:.0f} years")
        
        # Rating statistics
        if 'average_rating' in df.columns:
            print(f"\nRating Distribution:")
            rating_stats = df['average_rating'].describe()
            print(f"  Mean: {rating_stats['mean']:.2f} stars")
            print(f"  Median: {rating_stats['50%']:.2f} stars")
            print(f"  Providers with ratings: {df['has_rating'].sum()} ({df['has_rating'].sum()/len(df)*100:.1f}%)")
        
        # Appointment availability statistics
        if 'wait_days' in df.columns:
            print(f"\nAppointment Availability:")
            wait_stats = df['wait_days'].describe()
            print(f"  Mean wait time: {wait_stats['mean']:.1f} days")
            print(f"  Median wait time: {wait_stats['50%']:.1f} days")
            print(f"  Available within 7 days: {(df['appointments_available_7days'] > 0).sum()} ({(df['appointments_available_7days'] > 0).sum()/len(df)*100:.1f}%)")
        
        # Insurance network statistics
        if 'network_breadth' in df.columns:
            print(f"\nInsurance Network Coverage:")
            print(f"  Average networks accepted: {df['network_breadth'].mean()*7:.1f} / 7")
            print(f"  Accepts BCBS: {df['in_network_bcbs'].sum()} ({df['in_network_bcbs'].sum()/len(df)*100:.1f}%)")
            print(f"  Accepts Medicare: {df['accepts_medicare'].sum()} ({df['accepts_medicare'].sum()/len(df)*100:.1f}%)")
        
        print(f"\nFeature Coverage (from sample):")
        feature_cols = ['telehealth_available', 'speaks_spanish', 'evening_hours', 'weekend_hours', 
                       'accepting_new_patients']
        for col in feature_cols:
            if col in df.columns:
                pct = df[col].sum() / len(df) * 100
                print(f"  {col:30s}: {pct:5.1f}%")
        
        print("="*80)


def main():
    """Main execution with configuration"""
    
    # ============================================================================
    # CONFIGURATION - EDIT THESE VALUES
    # ============================================================================
    
    # Input file path
    INPUT_FILE = r"C:\Users\fletcherd\Documents\text-information-systems\Project\data\raw\npidata_pfile.csv"
    
    # States to include - Options:
    # Single state: ['IL']
    # Multiple states: ['IL', 'IN', 'WI']
    # All states: None
    STATES = ['IL']
    OUTPUT_PREFIX = "output/providers_illinois"
    CHUNK_SIZE = 50000
    TAXONOMY_FILE = "data/processed/taxonomy_reference.csv"
    ZIP_CENTROIDS_FILE = "data/processed/il_zip_centroids.csv"
    
    # Reference location for distance calculations (default: Chicago downtown)
    REFERENCE_LOCATION = (41.8781, -87.6298)
    
    # ============================================================================
    # END CONFIGURATION
    # ============================================================================
    
    print("Configuration:")
    print(f"  Input:  {INPUT_FILE}")
    print(f"  States: {STATES if STATES else 'ALL'}")
    print(f"  Output: {OUTPUT_PREFIX}")
    print(f"  Chunk:  {CHUNK_SIZE:,} rows")
    print(f"  Taxonomy: {TAXONOMY_FILE}")
    print(f"  ZIP Centroids: {ZIP_CENTROIDS_FILE}")
    print()
    
    # Check files
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Input file not found!")
        print(f"   {INPUT_FILE}")
        print()
        print("Update INPUT_FILE in this script.")
        return
    
    if not os.path.exists(TAXONOMY_FILE):
        print(f"Warning: Taxonomy file not found: {TAXONOMY_FILE}")
        print("   Run build_taxonomy_reference.py first to create it.")
        print("   Continuing anyway - all specialties will show as 'Other Healthcare Provider'")
        print()
    
    # Get file size
    file_size_gb = os.path.getsize(INPUT_FILE) / (1024**3)
    print(f"Input file size: {file_size_gb:.2f} GB")
    print()
    
    if file_size_gb > 5:
        estimated_minutes = file_size_gb * 2
        print(f"Estimated processing time: {estimated_minutes:.0f}-{estimated_minutes*1.5:.0f} minutes")
        print()
    
    input("Press Enter to start processing (or Ctrl+C to cancel)...")
    print()
    
    # Create processor
    processor = ProductionNPIProcessor(
        states=STATES, 
        reference_location=REFERENCE_LOCATION,
        taxonomy_file=TAXONOMY_FILE,
        zip_centroids_file=ZIP_CENTROIDS_FILE
    )
    
    # Run pipeline
    start_time = datetime.now()
    csv_path, jsonl_path = processor.process_full_dataset(
        input_file=INPUT_FILE,
        output_prefix=OUTPUT_PREFIX,
        chunk_size=CHUNK_SIZE
    )
    end_time = datetime.now()
    
    elapsed = (end_time - start_time).total_seconds() / 60
    print(f"\nTotal processing time: {elapsed:.1f} minutes")
    print("ALL DONE!")


if __name__ == "__main__":
    main()
