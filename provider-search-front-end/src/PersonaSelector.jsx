import { useState, useEffect } from "react";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import CircularProgress from "@mui/material/CircularProgress";
import { getPersonas } from "./provider-search-controller";
import "./PersonaSelector.css";

function PersonaSelector({ value, onPersonaChange }) {
  const [personas, setPersonas] = useState([]);
  const [selectedPersona, setSelectedPersona] = useState(value || "");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPersonas = async () => {
      try {
        setLoading(true);
        const personasData = await getPersonas();
        setPersonas(personasData);
        if (personasData.length > 0) {
          const initialPersona = value || personasData[0].id;
          setSelectedPersona(initialPersona);
          onPersonaChange?.(initialPersona);
        }
        setError(null);
      } catch (err) {
        console.error("Failed to load personas:", err);
        setError("Failed to load personas");
        setPersonas([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPersonas();
  }, [onPersonaChange]);

  useEffect(() => {
    if (value !== undefined && value !== selectedPersona) {
      setSelectedPersona(value);
    }
  }, [value, selectedPersona]);

  const handleChange = (event) => {
    const value = event.target.value;
    setSelectedPersona(value);
    onPersonaChange?.(value);
  };

  const selectStyles = {
    minWidth: 180,
    ".MuiInputLabel-root": { color: "#cde4ff" },
    ".MuiInputLabel-root.Mui-focused": { color: "#90c6ff" },
    ".MuiOutlinedInput-root": {
      backgroundColor: "rgba(255, 255, 255, 0.08)",
      borderRadius: "12px",
      color: "#f7f8fb",
      "& fieldset": { borderColor: "rgba(255, 255, 255, 0.28)" },
      "&:hover fieldset": { borderColor: "#5ab0ff" },
      "&.Mui-focused fieldset": { borderColor: "#5ab0ff", boxShadow: "0 0 0 3px rgba(90, 176, 255, 0.25)" },
    },
    ".MuiSelect-icon": { color: "#e2eeff" },
  };

  if (loading) {
    return (
      <div className="persona-selector">
        <CircularProgress size={24} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="persona-selector error">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <FormControl className="persona-selector" size="small">
      <InputLabel id="persona-select-label">Persona</InputLabel>
      <Select
        labelId="persona-select-label"
        id="persona-select"
        value={selectedPersona}
        label="Persona"
        onChange={handleChange}
        sx={selectStyles}
      >
        {personas.map((persona) => (
          <MenuItem key={persona.id} value={persona.id}>
            {persona.name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export default PersonaSelector;
