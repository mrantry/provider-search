import { useState } from "react";

import InputBase from "@mui/material/InputBase";
import SearchIcon from "@mui/icons-material/Search";
import PersonaSelector from "./PersonaSelector";
import "./SearchBar.css";

function SearchBar({ onSearch }) {
  const [query, setQuery] = useState("");
  const [selectedPersona, setSelectedPersona] = useState("");

  const submitSearch = () => {
    const trimmed = query.trim();
    if (!trimmed) return;
    onSearch(trimmed, selectedPersona);
  };
  
  const handleChange = (event) => {
    setQuery(event.target.value);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      submitSearch();
    }
  };

  const handlePersonaChange = (persona) => {
    setSelectedPersona(persona);
  };

  return (
    <div className="search-shell">
      <div className="search-input">
        <div className="search-icon">
          <SearchIcon />
        </div>
        <InputBase
          className="search-text"
          placeholder="Search providers, specialties, or locations"
          sx={{ color: "white" }}
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
        />
      </div>
      <PersonaSelector value={selectedPersona} onPersonaChange={handlePersonaChange} />
      <button className="search-button" type="button" onClick={submitSearch}>
        Search
      </button>
    </div>
  );
}

export default SearchBar
