# SparqMind: An Intelligent SPARQL Reasoning Engine

**SparqMind** is a modular, multi-provider **Text-to-SPARQL reasoning engine** designed to convert natural language questions into executable SPARQL queries over **DBpedia**. The system is optimized for research and experimentation using benchmark datasets such as **QALD-9 (100 queries)**, and provides a flexible, extensible architecture for prompt-driven SPARQL generation.

SparqMind integrates several core components:

* **Zero-Shot prompting** for baseline SPARQL generation
* **Multi-LLM routing** across OpenAI, DeepSeek, Gemini, and OpenRouter
* **Batch SPARQL generation** with a CLI interface for dataset-level experiments
* **A modern React chat interface** for conversational, ChatGPT-style querying
* **A configurable backend pipeline** built on FastAPI
* **Structured logging and reproducible evaluation workflows**

The backend exposes a clean `/generate` endpoint for interactive SPARQL generation, while the CLI mode enables rapid experimentation over datasets such as QALD-9. The frontend and backend run independently: React provides an aesthetic chat interface for users to ask questions naturally, and FastAPI handles prompt construction, model orchestration, SPARQL synthesis, and logging.

SparqMind is designed as a research oriented platform that makes it easy to explore how large language models interpret natural language intentions and map them to structured SPARQL queries in the context of DBpedia.

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
3. Environment variables from `.env` are loaded automatically by the backend.

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

An additional `POST /plan` endpoint is available to return the structured planner output (entities, relations, chain-of-thought) without generating SPARQL. This is used by the updated frontend so users can review and edit the reasoning steps before execution.

## CLI Batch Generation
Generate SPARQL for a dataset from the root directory:
```bash
python backend/main.py --generate-dataset ../data/qald_9_train_100.json --technique GoT --provider deepseek --model deepseek-chat --num_samples 1
```

- The dataset and output paths are resolved relative to the repository root, so the above command works as-is.
- Omit `--provider` or `--model` to fall back to `backend/config/config.json` defaults.
- Omit `--num_samples` to process the full dataset; pass a value to quickly test a subset.
- Use `--config path/to/override.json` to point to an alternate config file.
- Predictions are written to `outputs/predicted/predictions.json`; logs are written to `outputs/logs/backend.log`.

## Frontend Usage
You can open `frontend/index.html` directly in a browser, or serve it locally for friendlier CORS behavior:
```bash
./frontend/serve_frontend.sh 4173
```
then visit `http://127.0.0.1:4173`.

In the UI you can:
- Choose provider/model and toggle between **Zero-shot** (no planner) or **Chain-of-thought** (planner enabled).
- Click **Plan Question** to call `POST /plan` and populate editable fields for entities, relations, and reasoning steps.
- Refine the plan and press **Execute** to submit it to `POST /generate` and stream the resulting SPARQL back into the chat.

## Result and Evaluation
Run the dataset and predicted result and store the files in the executed folder. Then use both files from the executed folder to generate the gerbil standard evaluation of the sparql quries.

To execute the run_query file for the dataset:
```bash
python run_query.py --input ../data/qald_9_train_100.json --output executed/qald_9_train_100_executed.json
```

To execute the run_query file for the predicted query:
```bash
python run_query.py --input ../outputs/predicted/deepseek-chat_zero_shot.json --output executed/deepseek-chat_zero_shot_executed.json
```

To execute the gerbil evaluation use the following command:
```bash
python eval_gerbil.py qald_9_train_100 deepseek-chat_CoT
```

## Additional Documentation
See `backend/README.md` and `frontend/README.md` for component-specific notes.
