# Text-to-SPARQL System

A modular Text-to-SPARQL generation scaffold that supports FastAPI serving, CLI batch generation, and flexible model routing across multiple providers.

## Project Structure

```
backend/
    main.py
    config/
        config.json
        config_loader.py
    models/
        model_router.py
        providers/
            openai_client.py
            deepseek_client.py
            gemini_client.py
            openrouter_client.py
    utils/
        dataset_loader.py
        logger.py
    prompts/
        prompt_builder.py
    generation/
        generate_sparql.py
frontend/
    index.html
    app.js
    style.css
outputs/
    predicted/
    logs/
README.md
requirements.txt
```

## Environment Setup

Create and activate a Python virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set provider API keys as environment variables (examples):

   ```bash
   export OPENAI_API_KEY="your-key"
   export DEEPSEEK_API_KEY="your-key"
   export GEMINI_API_KEY="your-key"
   export OPENROUTER_API_KEY="your-key"
   ```

## Running the Backend (API Server)

```bash
python backend/main.py
```

or using uvicorn directly:

```bash
uvicorn backend.main:app --reload
```

## CLI Batch Generation Mode

Run batch generation on a dataset:

```bash
python backend/main.py --generate-dataset data/qald_9_train_100.json
```

Specify a prompting technique:

```bash
python backend/main.py --generate-dataset data/qald_9_train_100.json --technique zero_shot
```

## Direct Generator Invocation

```bash
python backend/generation/generate_sparql.py --dataset data/qald_9_train_100.json
```

## Frontend Usage

Open `frontend/index.html` in a browser. Ensure the FastAPI server is running on `http://127.0.0.1:8000` to generate SPARQL queries.

## Extending the System

- **Graph-of-Thought Prompting:** Implement logic in `backend/prompts/prompt_builder.py` and wire into generation routes.
- **Dynamic Prompting:** Extend prompt builder placeholders and optionally add runtime selection logic.
- **Additional Providers:** Add new provider clients under `backend/models/providers/` and register them in `backend/models/model_router.py`.

## Logging

Logs are written to `outputs/logs/backend.log` using a rotating file handler.

