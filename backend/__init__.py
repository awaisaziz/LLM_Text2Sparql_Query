from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from a root-level .env file (if present) so provider
# clients can pick up API keys during imports.
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT.parent / ".env", override=False)
load_dotenv(override=False)
