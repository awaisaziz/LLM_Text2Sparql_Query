# Text-to-SPARQL System

A modular Text-to-SPARQL generation scaffold that supports FastAPI serving, CLI batch generation, and flexible model routing across multiple providers.

## Repository Layout
- **backend/** – FastAPI app, batch generator, prompt builders, and model routing code.
  - **main.py** – FastAPI entrypoint and CLI interface for batch runs.
  - **config/** – JSON configuration and loader utilities.
  - **generation/** – Batch SPARQL generation logic.
  - **models/** – Provider router and provider client implementations.
  - **prompts/** – Prompt construction helpers.
  - **utils/** – Dataset loading and logging helpers.
- **frontend/** – Static HTML/JS/CSS client for submitting questions to the backend.
- **data/** – Datasets used for batch generation (e.g., `qald_9_train_100.json`).
- **outputs/** – Run artifacts.
  - **predicted/** – Generated SPARQL predictions.
  - **logs/** – Application logs (e.g., `backend.log`).
- **requirements.txt** – Python dependencies.

## Architecture Flow
```mermaid
flowchart TD
    A[User Question (Frontend or CLI)]
    --> B[FastAPI API / CLI Entry<br/>backend/main.py]
    B --> C[Prompt Builder<br/>backend/prompts]
    C --> D[Model Router<br/>backend/models/model_router.py]
    D --> E[Provider Clients<br/>OpenAI, DeepSeek, Gemini, OpenRouter]
    E --> F[LLM Response]
    F --> G[SPARQL Assembly<br/>backend/generation/generate_sparql.py]
    G --> H[Outputs<br/>predictions & logs]
    B --> I[Dataset Loader<br/>backend/utils/dataset_loader.py]
    I --> G
```

## Environment Setup (run from repo root)
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Provide provider API keys as environment variables (or place them in a `.env` file at the repo root):
   <!-- ```bash
   export OPENAI_API_KEY="your-key"
   export DEEPSEEK_API_KEY="your-key"
   export GEMINI_API_KEY="your-key"
   export OPENROUTER_API_KEY="your-key"
   ``` -->
   Environment variables from `.env` are loaded automatically by the backend.

## Running the Backend API Server
From the repository root:
```bash
python backend/main.py
```
The script adjusts `PYTHONPATH` automatically so it works when called directly from the root. Alternatively:
```bash
python -m backend.main
uvicorn backend.main:app --reload
```
The server listens on `http://127.0.0.1:8000` and exposes `POST /generate`.

## CLI Batch Generation
Generate SPARQL for a dataset from the root directory:
```bash
python backend/main.py --generate-dataset ../data/qald_9_train_100.json --technique zero_shot --provider gemini --model gemini-2.0-flash-lite --num_samples 1
```
- The dataset and output paths are resolved relative to the repository root, so the above command works as-is.
- Omit `--provider` or `--model` to fall back to `backend/config/config.json` defaults.
- Omit `--num_samples` to process the full dataset; pass a value to quickly test a subset.
- Use `--config path/to/override.json` to point to an alternate config file.
- Predictions are written to `outputs/predicted/predictions.json`; logs are written to `outputs/logs/backend.log`.

## Frontend Usage
Open `frontend/index.html` in a browser. Ensure the backend server is running at `http://127.0.0.1:8000` so the UI can call the `/generate` endpoint.

## Result and Evaluation
Run the dataset and predicted result and store the files in the executed folder. Then use both files from the executed folder to generate the gerbil standard evaluation of the sparql quries.

To execute the run_query file for the dataset:
```bash
python run_query.py --input ../data/qald_9_train_100.json --output executed/qald_9_train_100_executed.json
```

To execute the run_query file for the predicted query:
```bash
python run_query.py --input ../outputs/predicted/predictions.json --output executed/predicted_zero_shot.json
```

## Extending the System
- Add new prompt strategies in `backend/prompts/prompt_builder.py`.
- Register new providers in `backend/models/providers/` and wire them in `backend/models/model_router.py`.
- Update `backend/config/config.json` to point to new datasets or change defaults.

## Additional Documentation
See `backend/README.md` and `frontend/README.md` for component-specific notes.
