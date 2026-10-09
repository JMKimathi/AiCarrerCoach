# Training the career retriever (Jupyter)

You were asked to “train the model.” For this FYP that means **fine-tune a small retriever**, not train ChatGPT.

| You train | You do **not** train |
|-----------|----------------------|
| `all-MiniLM-L6-v2` embeddings so career questions find the right article | A full LLM (GPT, Llama, Gemini) |
| Jupyter notebooks 01 → 02 → 03 | A second database |

The Android app still **generates** answers with a hosted LLM later. The **trained** piece is retrieval (RAG).

## Setup (once)

In PowerShell:

```powershell
cd C:\Users\Mwiti\Downloads\AICareerCoach\ml
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m ipykernel install --user --name aicareer --display-name "AI Career Coach"
jupyter notebook
```

### Use PyCharm

Open the repository root (`AICareerCoach`) in PyCharm, then create/select `ml/.venv` as the interpreter for ML run configurations. Set the working directory to the repository root for commands such as `python ml/src/run_career_pipeline.py ...`. Keep the backend interpreter at `backend/.venv`; do not install the ML requirements into that environment.

Open the `notebooks` folder. In the kernel menu pick **AI Career Coach**.

## Run in this order

1. `01_prepare_knowledge_base.ipynb` — split articles and generated O*NET profiles into searchable chunks  
2. `02_train_retriever.ipynb` — fine-tune MiniLM (first run downloads the model)  
3. `03_evaluate_retrieval.ipynb` — Recall@1 / Recall@3 vs baseline, saves a chart  

Screenshot the training cell and the bar chart for the report.

## What to tell a supervisor

“I trained a sentence-transformer retriever on career question–passage pairs using Multiple Negatives Ranking Loss, then measured Recall@K against a frozen MiniLM baseline. Answer text still comes from an LLM grounded on those retrieved chunks.”

## Career pathway assessment API

The backend also exposes a separate, explainable pathway exploration flow:

- `GET /api/career/assessment-options` returns suggested skill, interest, and activity tags. Students can also provide their own wording.
- `POST /api/career/assess` accepts lists of `skills`, `interests`, and `preferred_activities`.
- The response ranks career families and shows matched answers, skills to explore, next steps, and (when the retriever is available) related resources.

This is a versioned, rule-based match guide (`career-paths-v1`) designed to work before model training or retrieval setup. Its `fit_score` is relative alignment with the student's answers; it is **not** a probability of success, employability, or admission to a role. It does not save the assessment profile.

## Career classifier training notes

Run `python ml/src/train_career_model.py` from any working directory. The script removes exact duplicate profiles before splitting, keeps validation/test membership stable as new examples are appended, selects a model using validation macro-F1, and evaluates the selected model once on a separate held-out test set. Every run saves versioned metrics, plots, and a model artifact under `ml/metrics/career-model/` and `ml/models/career-model/`. It does **not** replace the backend model unless run with `--promote`.

The current `tech_career_dataset.csv` has 26,000 rows, 13 labels, and 4,053 exact duplicate feature rows (no conflicting labels were found). It includes 13,000 `student_skill_permutation` rows as well as job-posting-derived rows, so scores should be described as performance on this dataset—not evidence that the model measures student aptitude. Review source composition and deduplication effects before making outcome claims. Model probabilities are not calibrated and must not be presented as a student's probability of succeeding in a career.

## One-run pipeline and Colab

`python ml/src/run_career_pipeline.py --input-dir "C:\Users\Mwiti\Downloads\Datasets"` rebuilds the normalized market and occupation tables, indexes O*NET profiles with the career guides, and saves a reusable embedding cache for faster API startup. Restart the API after rebuilding so it reloads `chunks.json`. Add `--train-classifier` to train a new versioned classifier from the separately labeled project dataset; add `--promote-model` only after reviewing that run's test metrics. `--train-retriever` runs the separate retrieval training/evaluation workflow. No API key is needed for data preparation or model training.

The Colab orchestrator is [notebooks/00_full_career_pipeline_colab.ipynb](notebooks/00_full_career_pipeline_colab.ipynb). Put the project folder and `Datasets` folder in Google Drive, update the notebook paths if necessary, then run its cells. Classifier and retriever training are off by default.

## Optional audit of external job postings

The `Downloads/Datasets/job_descriptions.csv` file is about 1.74 GB. To inspect aggregate coverage without copying raw records into the repository, run:

```powershell
python ml/src/audit_job_descriptions.py "C:\Users\Mwiti\Downloads\Datasets\job_descriptions.csv"
```

By default it scans up to 50,000 rows and reports role, country, work-type, date, and content-availability counts. For a complete scan, add `--all-rows`. It deliberately excludes contact, demographic preference, company, salary, and company-profile fields. Treat this dataset as dated global job-posting content; it needs a freshness, Kenya coverage, and role-taxonomy review before it can support local opportunity recommendations or training.

## Build derived career data tables

After downloading the LinkedIn and O*NET CSVs into `C:\Users\Mwiti\Downloads\Datasets`, run:

```powershell
python ml/src/build_career_datasets.py --input-dir "C:\Users\Mwiti\Downloads\Datasets"
```

The builder joins `postings.csv` to `job_skills.csv` and `skills.csv`, aggregates posting counts by location, title, and skill, and creates O*NET occupation profiles from `essential_skills.csv` and `software_skills.csv`. It also reads the O*NET Excel files `Occupation Data.xlsx`, `Job Titles.xlsx`, `Job Zones.xlsx`, and `Work Activities.xlsx`, plus Career Interest Types and Specific Interest Areas CSVs when present. These add readable occupation descriptions, title aliases, typical work, interest profiles, and preparation levels. Install `openpyxl` with the ML requirements for Excel support. It does not merge in the separate `job_descriptions.csv` source or copy LinkedIn posting descriptions, company data, salary, or personal/contact fields. Outputs are under `ml/data/processed/derived/` with a source/interpretation manifest.

The current LinkedIn export has 123,849 postings from 2024, with 122,096 joined to skills. Its 35-code skill dictionary is coarse, and a location-name scan found zero likely Kenya postings, so this export can help exercise the pipeline but should not be used for Kenya job-demand claims. The available O*NET files now include occupation descriptions and title aliases, skills, career and specific interests, work activities, and job zones. O*NET describes U.S. occupations, so use it as a career exploration reference and adapt local training details when Kenyan sources become available. Neither job postings nor O*NET occupational profiles are student-success labels, so they remain separate from student-fit training data.
