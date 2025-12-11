import { useState, useEffect } from "react";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
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
  }, []);

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
    minWidth: 200,
    ".MuiOutlinedInput-root": {
      height: 48,
      background: "rgba(255, 255, 255, 0.06)",
      borderRadius: "14px",
      color: "#f7f8fb",
      paddingRight: "6px",
      "& fieldset": { borderColor: "rgba(255, 255, 255, 0.12)" },
      "&:hover fieldset": { borderColor: "rgba(255, 255, 255, 0.2)" },
      "&.Mui-focused fieldset": { borderColor: "#6fc1ff", boxShadow: "0 0 0 3px rgba(111, 193, 255, 0.2)" },
      ".MuiOutlinedInput-notchedOutline": { borderRadius: "14px" },
      ".MuiSelect-select": {
        display: "flex",
        alignItems: "center",
        height: "48px",
        padding: "0 14px",
        fontWeight: 600,
        letterSpacing: "0.01em",
      },
      ".MuiSelect-select.MuiInputBase-input": {
        paddingRight: "26px",
      },
    },
    ".MuiSelect-icon": { color: "#dbe9f8", fontSize: "1.15rem" },
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
      <Select
        id="persona-select"
        value={selectedPersona}
        displayEmpty
        renderValue={(val) => {
          const persona = personas.find((p) => p.id === val);
          if (persona) {
            return <span className="persona-value">{persona.name}</span>;
          }
          return <span className="persona-placeholder">Persona</span>;
        }}
        onChange={handleChange}
        sx={selectStyles}
        inputProps={{ "aria-label": "Persona" }}
        MenuProps={{
          PaperProps: {
            sx: {
              background: "rgba(14, 22, 35, 0.96)",
              color: "#e8f0fa",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              boxShadow: "0 18px 38px rgba(0, 0, 0, 0.55)",
              "& .MuiMenuItem-root.Mui-selected": {
                backgroundColor: "rgba(79, 139, 255, 0.18)",
              },
              "& .MuiMenuItem-root:hover": {
                backgroundColor: "rgba(111, 193, 255, 0.14)",
              },
            },
          },
        }}
      >
        {!selectedPersona && (
          <MenuItem disabled value="">
            Persona
          </MenuItem>
        )}
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
