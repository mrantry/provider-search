import { useState } from 'react'

import './App.css'
import SearchBar from './SearchBar'

function App() {
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState('idle'); // idle | loading | success | error
  const [error, setError] = useState(null);
  const [lastQuery, setLastQuery] = useState('');
  const [lastPersona, setLastPersona] = useState('');

  const handleSearch = async (query, persona) => {
    console.log("Making API request for:", query, "with persona:", persona);

    setStatus('loading');
    setError(null);
    setResults([]);
    setLastQuery(query);
    setLastPersona(persona);

    try {
      const response = await fetch(
        'http://localhost:5001/search',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, persona })
        }
      );

      if (!response.ok) throw new Error(`Request failed: ${response.status}`);

      const data = await response.json();
      const parsedResults = Array.isArray(data.results) ? data.results : [];
      setResults(parsedResults);
      setStatus('success');
      console.log("API results:", parsedResults);

    } catch (error) {
      console.error("API error:", error);
      setError('Unable to fetch results right now. Please try again.');
      setStatus('error');
    }
  };

  const renderResults = () => {
    if (status === 'idle') {
      return <p className="muted">Start by searching for a provider.</p>;
    }

    if (status === 'loading') {
      return <p className="muted">Searching…</p>;
    }

    if (status === 'error') {
      return <p className="error">{error}</p>;
    }

    if (results.length === 0) {
      return <p className="muted">No providers found. Try a different search or persona.</p>;
    }

    return (
      <div className="results-grid">
        {results.map((result) => {
          const providerData = result.provider_data || {};
          const name = result.provider_name || providerData.provider_name || 'Unknown provider';
          const specialty = result.specialty || providerData.specialty_readable || 'Specialty not listed';
          const city = providerData['Provider Business Practice Location Address City Name'] || providerData.city;
          const state = providerData['Provider Business Practice Location Address State Name'] || providerData.state;
          const location = providerData.full_address || [city, state].filter(Boolean).join(', ');
          const rating = providerData.average_rating;
          const reviews = providerData.num_reviews;
          const accepting = providerData.accepting_new_patients;
          const telehealth = providerData.telehealth_available;

          return (
            <article key={`${result.provider_id || name}-${result.rank}`} className="result-card">
              <div className="result-top">
                <h3>{name}</h3>
                {location && <p className="result-location">{location}</p>}
              </div>
              <p className="result-specialty">{specialty}</p>
              <div className="result-meta">
                {typeof rating === 'number' && (
                  <span className="pill">
                    Rating {Number(rating).toFixed(1)}{reviews ? ` (${reviews})` : ''}
                  </span>
                )}
                {accepting && <span className="pill success">Accepting new patients</span>}
                {telehealth && <span className="pill">Telehealth</span>}
              </div>
            </article>
          );
        })}
      </div>
    );
  };

  return (
    <>
      <header className="hero">
        <h1>Provider Search</h1>
        <p className="description">Search powered by what matters to you</p>
        <SearchBar onSearch={handleSearch} />
      </header>

      <section className="results-section">
        <div className="results-header">
          <h2>Results</h2>
          {lastQuery && status === 'success' && (
            <p className="muted">
              Showing matches for "{lastQuery}"
              {lastPersona ? ` | Persona: ${lastPersona}` : ''}
            </p>
          )}
        </div>
        {renderResults()}
      </section>
    </>
  );
}

export default App;









// import { useState } from "react";
// import "./App.css";
// import SearchBar from "./SearchBar";

// const MOCK_RESULTS = [
//   {
//     id: 1,
//     name: "Dr. Jane Smith",
//     specialty: "Cardiology",
//     location: "Chicago, IL",
//   },
//   {
//     id: 2,
//     name: "Dr. John Doe",
//     specialty: "Dermatology",
//     location: "New York, NY",
//   },
//   {
//     id: 3,
//     name: "Dr. Emily Johnson",
//     specialty: "Pediatrics",
//     location: "Austin, TX",
//   },
// ];

// function App() {
//   const [results, setResults] = useState([]);
//   const [hasSearched, setHasSearched] = useState(false);

//   const handleSearch = (query) => {
//     console.log("Searching for:", query);

//     const normalizedQuery = query.toLowerCase().trim();

//     const filtered = MOCK_RESULTS.filter((item) => {
//       return (
//         item.name.toLowerCase().includes(normalizedQuery) ||
//         item.specialty.toLowerCase().includes(normalizedQuery) ||
//         item.location.toLowerCase().includes(normalizedQuery)
//       );
//     });

//     setResults(filtered);
//     setHasSearched(true);
//   };

//   return (
//     <>
//       <h1>Provider Search</h1>

//       <SearchBar onSearch={handleSearch} />

//       <p className="description">Search powered by what matters to you</p>

//       <div className="results-container">
//         {hasSearched && results.length === 0 && (
//           <p>No providers found. Try another search.</p>
//         )}

//         {results.length > 0 && (
//           <div className="results-list">
//             {results.map((provider) => (
//               <div key={provider.id} className="result-card">
//                 <h2>{provider.name}</h2>
//                 <p>{provider.specialty}</p>
//                 <p>{provider.location}</p>
//               </div>
//             ))}
//           </div>
//         )}
//       </div>
//     </>
//   );
// }

// export default App;
