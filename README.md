# AI Career Coach

AI Career Coach is a student career-guidance project with an Android app, a local Python API, and a separate machine-learning and retrieval pipeline.

## Project areas

| Folder | Purpose | Main tools |
|---|---|---|
| `app/` | Android client built with Kotlin, Jetpack Compose, and Material 3 | Android Studio and Gradle |
| `backend/` | FastAPI service, authentication, career assessments, resources, feedback, and chat | Python and PyCharm |
| `ml/` | Dataset preparation, career-model training, retrieval, and Colab/Jupyter notebooks | Python, PyCharm, Jupyter, or Google Colab |

The backend and ML pipeline use separate Python environments because their dependencies differ. Open the repository root in Android Studio or PyCharm to work with the full project.

## Run the app locally

### 1. Start the API

From PowerShell at the repository root:

```powershell
.\backend\start.ps1
```

On first run, the script prepares the backend Python environment, installs its requirements, initializes the local database, and starts the API on port `8000`. The default database is SQLite at `backend/career_coach.db`. The API does not create demo accounts.

Check that the API is running at `http://127.0.0.1:8000/api/health`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

### 2. Run Android

Open the repository root in Android Studio, allow Gradle to sync, and run the `app` configuration on an emulator or device. From the landing or sign-in screen, open **Backend connection settings** to save one or more reachable API addresses. For an Android emulator, use `http://10.0.2.2:8000/api`.

For a physical phone, save the laptop's IPv4 address once for each network you use (for example, home Wi-Fi and phone hotspot) as `http://<laptop-ip>:8000/api`. Find each address with `ipconfig` while the laptop is connected to that network. Keep the phone and laptop on the same network and allow the API through the computer's firewall if prompted. The app checks the saved addresses after network changes and uses the one whose health endpoint responds.

Students can register through the app. To create the first administrator locally, stop the API and run:

```powershell
& .\backend\.venv\Scripts\python.exe -m backend.create_admin
```

See [backend/README.md](backend/README.md) for backend setup and troubleshooting.

## Machine-learning pipeline

The ML tools are separate from API startup. In PyCharm, use `ml/.venv` for ML scripts and `backend/.venv` for the API. See [ml/README.md](ml/README.md) for environment setup, dataset preparation, model training, evaluation, and the Colab notebooks.

The training and retrieval workflows do not run automatically when the app starts. Keep downloaded datasets, model artifacts, and API keys out of Git unless a specific project need and license permit sharing them.

## Career catalogue

`ml/data/careers/` holds a synthetic career catalogue covering 452 roles in 15 categories, for Kenya and international markets. Every table shares a `career_id` key.

| File | Contents |
| --- | --- |
| `career_catalog.csv` | One row per role, with category, focus area and a draft description |
| `career_skills.csv` | Core, preferred and transferable skills |
| `career_education.csv` | Study areas, qualification levels, certifications and the body to verify with |
| `career_pathways.csv` | Five stages per role, from attachment to senior practice |
| `career_resources.csv`, `trusted_sources.csv` | Official sources linked to each role |
| `interview_questions.csv` | Practice questions in eight styles, with follow-up probes |
| `opportunity_templates.csv` | What attachments, internships, graduate programmes and jobs usually look like |
| `cv_templates.jsonl` | A CV layout, skills and bullet starters per role |
| `career_training_data.csv` | Synthetic student profiles labelled with a target career |

Rebuild everything and refresh the search index with the `ml` environment:

```powershell
.\ml\.venv\Scripts\python.exe ml/src/run_career_pipeline.py
```

What the catalogue is and is not:

- All rows are synthetic and illustrative. They are not verified Kenyan requirements, live vacancies or guaranteed routes.
- Opportunity templates never name an employer and are never marked as live vacancies.
- Official source links were confirmed by web search on the date in `trusted_sources.csv`; the pages were not reviewed in full.
- Real student profiles belong in `ml/data/careers/real/student_profiles.csv`, which Git ignores. Only rows with `consent_given = yes` are used, and the file must not contain names, emails or phone numbers.
- `ml/src/train_catalogue_model.py` trains a classifier on the training table. Its scores on synthetic rows show how well it recovered the generator's rules, not real-world accuracy. The backend does not load this model.

## Career features in the API and app

| Endpoint | Purpose |
| --- | --- |
| `GET /api/careers/categories`, `GET /api/careers`, `GET /api/careers/{career_id}` | Browse, search and read the catalogue |
| `POST /api/careers/{career_id}/cv` | Build a Markdown CV from the student's own details |
| `POST /api/interviews`, `POST /api/interviews/{id}/answer`, `POST /api/interviews/{id}/finish` | Run a practice interview and get feedback |
| `PUT /api/resources/{resource_id}`, `DELETE /api/resources/{resource_id}` | Administrator edits and deletes knowledge-base resources |
| `PUT /api/admin/students/{user_id}/status` | Administrator activates or deactivates a student account |

In the app, students reach these from **Explore Careers** on the dashboard: search the catalogue, open a career, then build a CV or start a mock interview. Administrators edit and delete resources from **Knowledge** and manage accounts from **Students**.

The mock interview uses Gemini to react to each answer. Without a `GEMINI_API_KEY` it still runs from the question bank. Its feedback is practice coaching, not a hiring prediction.

## Android source layout

```text
app/src/main/java/com/aicareercoach/mobile/
├── MainActivity.kt
├── data/                  # App models and API client
└── ui/
    ├── components/
    ├── navigation/
    ├── screens/
    │   ├── admin/
    │   ├── auth/
    │   ├── shared/
    │   └── student/
    └── theme/
```

## Keep credentials and local files private

- Put `GEMINI_API_KEY` and other secrets in `backend/.env`; never commit the real `.env` file.
- Keep the local database, virtual environments, generated model files, and build output out of commits.
- Use `.env.example` files only for variable names and placeholder values.
