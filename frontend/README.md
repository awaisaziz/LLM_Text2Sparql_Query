# Frontend

A two-column chat + planner client for submitting natural language questions to the backend API and displaying the generated SPARQL query.

## Files
- `index.html` – HTML shell with chat, planner, and provider/model controls.
- `app.js` – Fetch logic for `POST /plan` (planner) and `POST /generate` (query execution).
- `style.css` – Updated styling for the dual-pane chat + planner view.
- `serve_frontend.sh` – Convenience script to serve the static files locally via `python -m http.server`.

## Usage
1. Start the backend server from the repository root:
   ```bash
   python backend/main.py
   ```
2. Open `frontend/index.html` in your browser, or start a static server for friendlier CORS defaults:
   ```bash
   ./serve_frontend.sh 4173
   ```
   then browse to `http://127.0.0.1:4173`.
3. Choose zero-shot (no plan) or chain-of-thought (planner on). In chain-of-thought mode, click **Plan Question** to populate entities, relations, and reasoning steps. Edit them if needed, then click **Execute** to generate SPARQL. The page expects the backend at `http://127.0.0.1:8000`; update `app.js` if you need a different host/port.

## Customization
- Adjust styling in `style.css`.
- Modify request handling or validation logic in `app.js`.
