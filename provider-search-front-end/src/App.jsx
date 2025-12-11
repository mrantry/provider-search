import { useState } from 'react'

import './App.css'
import SearchBar from './SearchBar'

function App() {
  const [results, setResults] = useState(null);

  const handleSearch = async (query) => {
    console.log("Making API request for:", query);

    try {
      const response = await fetch(
        `https://api.example.com/search?q=${encodeURIComponent(query)}`
      );

      if (!response.ok) throw new Error(`Request failed: ${response.status}`);

      const data = await response.json();
      setResults(data);
      console.log("API results:", data);

    } catch (error) {
      console.error("API error:", error);
    }
  };

  return (
    <>
      <h1>Provider Search</h1>
      <SearchBar onSearch={handleSearch} />
      <p className="description">Search powered by what matters to you</p>
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