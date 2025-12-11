Project Title: Personalized Provider Search

Team Members:

Michael Antry (antry2@illinois.edu) 
Dean Fletcher (deanhf2@illinois.edu) 
Jordan Alwan (jzalwan2@illinois.edu) 
Janani Jayanth (jananij2@illinois.edu)

Project Coordinator: Michael Antry (antry2@illinois.edu)

**Project Description: **

What is the new tool or new function that you'd like to develop?
We’re developing a Provider Search Relevance & Persona Optimization system — a miniature healthcare provider search engine that personalizes ranking results based on user “personas.”

Unlike traditional provider searches that show the same ranked list for everyone, this system introduces a new function: the ability to dynamically re-rank providers according to user goals or identities (e.g., “Convenience-first,” “Quality-seeking,” “Cost-sensitive,” or “Identity-affirming care”).

Why do we need it? What pain point does it address?
Current healthcare provider search tools — such as those from insurance networks or public registries — typically return the same ranked list of providers for every user, regardless of their personal goals or context.

This creates a mismatch between search intent and ranking logic. For example:

A patient who prioritizes convenience (e.g., nearby, available soon) gets the same results as someone who values quality (e.g., board certification, years of experience).

Marginalized users looking for identity-affirming care (e.g., LGBTQ+-friendly, multilingual, culturally competent) receive no tailored relevance ranking.

The result is lower user satisfaction, inefficient provider discovery, and potential inequities in access to care.

Our tool addresses this by enabling persona-based search optimization, so each user type receives results ranked according to what matters most to them. This improves the perceived relevance of results and demonstrates how retrieval systems can model diverse notions of “relevance” — a key theme in information retrieval research.

How is this different from existing tools?
Most existing provider search tools — including insurance portals and public registries like CMS Care Compare — use static ranking criteria, such as alphabetical order or simple proximity. They treat “relevance” as universal and do not adapt to individual user goals.

Our system introduces a dynamic, persona-based re-ranking layer that personalizes results according to user intent. Instead of one fixed ranking, it generates multiple relevance models (e.g., Convenience-first, Quality-seeking, Cost-sensitive, Identity-affirming) by applying different feature weightings over structured provider attributes.

This is a novel extension of traditional retrieval models (BM25, Query Likelihood) — turning them into context-aware, user-specific ranking systems that demonstrate how search relevance can vary across personas.

How do you plan to build your tool?
Data pipeline
Sources: NPI Registry (core provider roster), optional CMS Care Compare/Physician Compare fields (affiliations, quality signals), plus synthetic augmentation for gaps (telehealth flag, basic availability buckets). ETL: Clean and normalize names, specialties (map to a controlled taxonomy), addresses → lat/long, languages, and enumeration date (experience proxy). Feature table: One row per provider with text fields (name, specialty, practice description) and structured fields (distance, telehealth, experience, languages, etc.).

Indexing & retrieval baseline
Build an inverted index over text fields. Implement BM25 and Query Likelihood (Dirichlet / JM) for the initial candidate set (e.g., top 100 per query). Support queries like “cardiologist near 60601” or “primary care spanish”.

Persona-aware re-ranking
Define 3–4 personas (e.g., Convenience-first, Quality-seeking, Cost-sensitive, Identity-affirming). Engineer structured features per provider-query pair: distance, telehealth availability, experience years (from enumeration date), language match, evening/weekend availability (augmented), hospital affiliation flag, etc.

Implement a weighted linear re-ranker: final_score = alpha * text_score + Σ (w_i(persona) * feature_i)

Store persona weight vectors and expose them via a config. Optionally add (simulated) relevance feedback to tune weights per persona.

Interface & UX
Minimal web UI: search box + persona selector; result list shows explanations (why a provider ranks: distance, language match, experience). Controls to toggle personas and see rank changes live (good demo value).

Engineering stack (proposed)
Python for ETL + evaluation; Pyserini/Lucene or Whoosh for indexing & BM25/QL. Pandas for preprocessing; scipy/statsmodels for tests; FastAPI/Flask for a simple API; lightweight React or templated HTML for the demo UI. Reproducible repo with data/, index/, rerank/, eval/, ui/, and notebooks/ for analysis.

Quality, bias, and ethics checkpoints
Log which features drive ranking; ensure sensitive attributes aren’t used improperly. Provide an opt-in “Identity-affirming care” persona using neutral signals (e.g., explicit provider self-descriptions, language services) and avoid protected-class inference.

Deliverables
Reproducible dataset & index, persona configs, and evaluation scripts. Report with metrics tables, significance tests, and case studies. Demo UI showing how rankings change by persona, with per-result explanations.

How do you plan to evaluate your tool?
Cranfield-style

Create a qrels set: for each query and persona, label the top N candidates (using heuristics + small manual annotations). Metrics: Precision@k, MAP, MRR, nDCG; run significance tests (paired t-test or randomization) comparing baseline vs persona re-ranker. Report both overall and per-persona results to show targeted gains.

How do you plan to divide the work among team members?
(Person A) Data & Feature Engineering

Responsibilities:

Acquire and preprocess NPI and CMS datasets (Python + Pandas).

Normalize text fields (provider names, specialties, addresses).

Engineer structured features:

Distance (geopy), telehealth flag, experience proxy, etc.

Build final provider table for indexing (JSONL or CSV).

Why: This requires solid data wrangling and schema design experience — ideal for someone comfortable with real-world messy data.

(Person B) Indexing & Baseline Retrieval

Responsibilities:

Implement and tune BM25 and Query Likelihood using Pyserini/Lucene or Whoosh.

Build the inverted index over provider text fields.

Expose a Python or REST API endpoint to retrieve top-k results for a query.

Output rankings for evaluation (TREC-style run files).

Why: This is a hands-on IR systems task — perfect for someone who’s comfortable working close to search libraries and evaluation pipelines.

(Person C) Persona Modeling & Re-ranking

Responsibilities:

Define personas and weight schemas for re-ranking (feature importance vectors).

Implement the weighted linear re-ranker combining text score + persona features.

Design and run evaluation experiments comparing baseline vs persona models.

Lead statistical testing (paired t-test, randomization) and interpret results.

Coordinate integration across modules and final write-up structure.

Why: This leverages your strong system design and analytical background, while ensuring the project stays coherent and meets IR research standards.

(Person D) Evaluation, UX & Reporting

Responsibilities:

Help label qrels (relevance judgments) — possibly using heuristics or guidance from others.

Build the demo UI (Flask/FastAPI + simple HTML/React) that lets users pick a persona and see rank changes.

Prepare visualizations for metrics (Precision@k, nDCG) and final presentation slides.

Assist with documentation and code readability.

Why: This provides hands-on exposure across data labeling, evaluation, and UI — a great learning opportunity with clear, guided deliverables.

Progress Report:

11/21/2025 Completed

GitHub Created
Data gathered from multiple data sources for provider information (Dean)
FE Development has begun (Jordan)
BE API Development has begun (Michael)
BM25 Implementation has begun on gathered data (Janani)