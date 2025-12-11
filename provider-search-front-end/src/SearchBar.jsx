import { useState } from "react";

import InputBase from "@mui/material/InputBase";
import SearchIcon from "@mui/icons-material/Search";
import "./SearchBar.css";

function SearchBar({onSearch}) {
  const [query, setQuery] = useState("");
  
  const handleChange = (event) => {
    setQuery(event.target.value);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") onSearch(query);
  };

  return (
    <div className="search">
      <div className="search-icon">
        <SearchIcon />
      </div>
      <InputBase className="search-input"
        placeholder="Search…"
        sx={{ color: "white"}}
        value={query}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
      />
    </div>
  );
}

export default SearchBar