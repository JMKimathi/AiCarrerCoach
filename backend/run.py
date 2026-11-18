"""Start the backend with `python run.py` (runs uvicorn on port 8000)."""

import sys
from pathlib import Path
import uvicorn

# Ensure project root is in Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

if __name__ == "__main__":
    print("Starting the AI Career Coach backend on http://0.0.0.0:8000 ...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
