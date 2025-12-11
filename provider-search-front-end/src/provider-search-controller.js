/**
 * Fetch available personas from the backend API and return an array of persona objects.
 * Each object has { id, name }.
 *
 * @returns {Promise<Array>} Array of persona objects with id and name properties.
 */
export const getPersonas = async () => {
	const endpoint = 'http://localhost:5001/personas';

	const resp = await fetch(endpoint, { headers: { 'Accept': 'application/json' } });
	if (!resp.ok) {
		throw new Error(`Failed to fetch personas: ${resp.status} ${resp.statusText}`);
	}

	const body = await resp.json();
	const personas = Array.isArray(body.personas) ? body.personas : [];

	return personas.map((p) => ({
		id: p.id,
		name: p.name || p.id
	}));
};