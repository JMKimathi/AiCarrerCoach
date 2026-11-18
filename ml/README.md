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

Open the repository root (`AICareerCoach`) in PyCharm, then create/select `ml/.venv` as the interpreter for ML run configurations. Set the working directory to the repository root for ML commands.

## Unified synthetic career dataset

Run `python ml/src/run_career_pipeline.py` from the repository root. It generates `ml/data/synthetic/career_feedback_dataset.jsonl`, indexes it alongside authored coaching guides, and saves a reusable embedding cache. The same JSONL powers the backend career assessment and `/career/predict`; downloaded O*NET, LinkedIn, and other source-derived tables are not used for career feedback. The 34 distinct pathways span 14 sectors, with two to four pathways per sector; every record has the same 24-field schema, including course aliases, skills, activities, preparation, projects, application-channel types, interview prompts, CV guidance, progression examples, and local-verification notes. Their examples are illustrative, not verified Kenyan qualification or licensing rules, live vacancies, or guaranteed application routes. Restart the API after rebuilding so it reloads `chunks.json`. Add `--train-retriever` to fine-tune a candidate using two synthetic question-passage pairs per pathway plus authored coaching-guide pairs; training uses two epochs and evaluates authored and generated queries separately. The backend selects the candidate when its files exist; set `USE_CANDIDATE_RETRIEVER=false` in `backend/.env` to use the previous retriever. The report separates authored guide ranking diagnostics from generated synthetic indexing checks. Neither set measures model accuracy, career-fit validity, employability, or student outcomes. Collect consented, de-identified student questions and obtain human relevance judgments before making real-world performance claims. No API key is needed for data preparation or model training.

The Android assessment asks for the student's course and optional career goal alongside skills, interests, and activities. The backend ranks pathways by visible answer overlap and returns role summaries, entry-level examples, qualification notes, application-channel ideas, interview prompts, CV guidance, progression examples, and preparation steps. The app keeps the extra guidance expandable so results stay readable. Scores are not probabilities or aptitude predictions. Students should verify current official requirements with the relevant Kenyan institutions and professional bodies.

To improve evaluation with real use, first collect voluntary, de-identified questions and have a reviewer select the expected resource. The local file template is [data/evaluation/student_queries_eval.template.csv](data/evaluation/student_queries_eval.template.csv); save eligible reviewed rows as `ml/data/evaluation/student_queries_eval.csv`. That private file is ignored by Git and used for evaluation only, never training. Without consent, de-identification, and human review, leave the file empty.

The Colab orchestrator is [notebooks/00_full_career_pipeline_colab.ipynb](notebooks/00_full_career_pipeline_colab.ipynb). Put the project folder in Google Drive, update the notebook path if necessary, then run its cells. Retriever training is optional and off by default. It improves retrieval of written guidance; it does not train or validate student career fit.

## Optional audit of external job postings

The `Downloads/Datasets/job_descriptions.csv` file is about 1.74 GB. To inspect aggregate coverage without copying raw records into the repository, run:

```powershell
python ml/src/audit_job_descriptions.py "C:\Users\Mwiti\Downloads\Datasets\job_descriptions.csv"
```

By default it scans up to 50,000 rows and reports role, country, work-type, date, and content-availability counts. For a complete scan, add `--all-rows`. It deliberately excludes contact, demographic preference, company, salary, and company-profile fields. Treat this dataset as dated global job-posting content; it needs a freshness, Kenya coverage, and role-taxonomy review before it can support local opportunity recommendations or training.

## Archived source-data exploration (not used by current career feedback)

The original download-based builder remains available for separate research only. It does not produce the active synthetic feedback dataset and its output is not indexed by the default career pipeline. To regenerate archived source tables manually, run:

```powershell
python ml/src/build_career_datasets.py --input-dir "C:\Users\Mwiti\Downloads\Datasets"
```

This archived builder joins LinkedIn skills/postings and derives O*NET profiles. Its outputs stay separate and are not consumed by `run_career_pipeline.py` or the active assessment endpoints. Keep those files only if needed for later source validation; the active synthetic dataset is generated by `ml/src/build_synthetic_career_dataset.py`.

The current LinkedIn export has 123,849 postings from 2024, with 122,096 joined to skills. Its 35-code skill dictionary is coarse, and a location-name scan found zero likely Kenya postings, so this export can help exercise the pipeline but should not be used for Kenya job-demand claims. The available O*NET files now include occupation descriptions and title aliases, skills, career and specific interests, work activities, and job zones. O*NET describes U.S. occupations, so use it as a career exploration reference and adapt local training details when Kenyan sources become available. Neither job postings nor O*NET occupational profiles are student-success labels, so they remain separate from student-fit training data.
