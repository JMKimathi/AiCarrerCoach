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

Open the repository root in Android Studio, allow Gradle to sync, and run the `app` configuration on an emulator or device. The Android emulator uses `http://10.0.2.2:8000/api` to reach the API on the host computer.

For a physical phone, configure the app to use the computer's local network IP address, such as `http://192.168.x.x:8000/api`. Keep the phone and computer on the same Wi-Fi or hotspot network, and allow the API through the computer's firewall if prompted.

Students can register through the app. To create the first administrator locally, stop the API and run:

```powershell
& .\backend\.venv\Scripts\python.exe -m backend.create_admin
```

See [backend/README.md](backend/README.md) for backend setup and troubleshooting.

## Machine-learning pipeline

The ML tools are separate from API startup. In PyCharm, use `ml/.venv` for ML scripts and `backend/.venv` for the API. See [ml/README.md](ml/README.md) for environment setup, dataset preparation, model training, evaluation, and the Colab notebooks.

The training and retrieval workflows do not run automatically when the app starts. Keep downloaded datasets, model artifacts, and API keys out of Git unless a specific project need and license permit sharing them.

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
