from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = ROOT / "notebooks"

notebook_files = [
    "01_prepare_knowledge_base.ipynb",
    "02_train_retriever.ipynb",
    "03_evaluate_retrieval.ipynb",
]

for nb_name in notebook_files:
    nb_path = NOTEBOOKS_DIR / nb_name
    print(f"Executing and populating: {nb_name}...")
    nb = nbformat.read(str(nb_path), as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(NOTEBOOKS_DIR)}})
    client.execute()
    nbformat.write(nb, str(nb_path))
    print(f"Successfully executed and saved outputs for {nb_name}!")

print("\nAll notebooks have been executed and saved with outputs!")
