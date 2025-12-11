# Backend

The backend exposes a FastAPI server for single-question SPARQL generation and a CLI for batch processing datasets.

## Key Files
- `main.py` – FastAPI entrypoint and CLI argument parser.
- `config/config.json` – Default dataset paths, provider/model defaults, max tokens, and output location.
- `generation/generate_sparql.py` – Batch generation loop and prediction writing.
- `models/model_router.py` + `models/providers/` – Provider routing and client implementations.
- `prompts/prompt_builder.py` – Prompt templates for different prompting techniques.
- `utils/dataset_loader.py` – Utilities for loading the QALD-9 dataset format.
- `utils/logger.py` – Rotating file logger writing to `outputs/logs/backend.log`.

## Running the API Server
From the repository root:
```bash
python backend/main.py
```
Or with uvicorn directly:
```bash
uvicorn backend.main:app --reload
```
The API exposes `POST /generate` with fields:
- `question` (string, required)
- `provider` (string, optional; defaults to `config.json`)
- `model` (string, optional; defaults to `config.json`)
- `technique` (string, optional; `zero_shot`, `graph_of_thought`, `dynamic_prompt`)

## Batch Generation via CLI
From the repository root:
```bash
python backend/main.py --generate-dataset ../data/qald_9_train_100.json --technique zero_shot --provider gemini --model gemini-2.0-flash-lite --num_samples 1
```
For using deepseek you can use the following command:
```bash
python backend/main.py --generate-dataset ../data/qald_9_train_100.json --technique GoT --provider deepseek --model deepseek-chat --num_samples 1
```

Arguments:
- `--generate-dataset` – Path to the dataset JSON file.
- `--technique` – Prompting technique (defaults to `zero_shot`).
- `--provider` / `--model` – Override defaults from `config.json`.
- `--num_samples` – Limit how many samples to run (omit to process the full dataset).
- `--config` – Path to an alternate config file.

Predictions are written to the path in `config.json` (default: `outputs/predicted/predictions.json`).

## Configuration Notes
`config/config.json` ships with a `dataset_paths.qald_9_dbpedia` entry pointing at `data/qald_9_train_100.json` relative to the repository root. Adjust these paths if you add datasets. `output_file` should remain inside the repo (e.g., the `outputs/predicted/` directory).
