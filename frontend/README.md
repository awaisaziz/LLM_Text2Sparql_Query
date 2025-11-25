# Frontend

A lightweight static client for submitting natural language questions to the backend API and displaying the generated SPARQL query.

## Files
- `index.html` – HTML shell and form for user input.
- `app.js` – Fetch logic that calls `POST /generate` on the backend.
- `style.css` – Minimal styling for the form and results view.

## Usage
1. Start the backend server from the repository root:
   ```bash
   python backend/main.py
   ```
2. Open `frontend/index.html` in your browser (directly from the filesystem or via a static server).
3. Enter a question and submit. The page expects the backend at `http://127.0.0.1:8000`; update `app.js` if you need a different host/port.

## Customization
- Adjust styling in `style.css`.
- Modify request handling or validation logic in `app.js`.
