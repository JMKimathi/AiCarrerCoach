# Local backend

## Start the API

From PowerShell, run `./backend/start.ps1` at the project root. The first run creates a private Python environment and a random `backend/.env` signing key, installs the backend requirements, and starts the API on port 8000. The default database is the local SQLite file `backend/career_coach.db`; startup creates the tables and imports the authored Markdown resources from `ml/data/resources`. It does not create demo users.

The Android emulator connects to `http://10.0.2.2:8000/api`. A physical phone must use the PC's LAN address and both devices must be on the same network.

## Create the first administrator

Stop the API, then run:

```powershell
& .\backend\.venv\Scripts\python.exe -m backend.create_admin
```

The command asks for the admin's name, email, and password without echoing the password. Admin privileges are never granted during public registration.

To reset an existing account password locally, run `& .\backend\.venv\Scripts\python.exe -m backend.reset_password` and follow the prompts. The password is not echoed or saved in shell history.

## Troubleshooting

- `GET /api/health` checks whether the API is responding.
- `GET /docs` shows the available API routes.
- Chat can use the authored resource database while local RAG model files are unavailable. Gemini responses require a valid `GEMINI_API_KEY` in `backend/.env`.
- If PostgreSQL is configured through `DATABASE_URL` but unavailable, startup fails clearly; it will not silently switch databases.
- Password recovery email is not configured; reset an account with the local command above.

Do not commit `backend/.env` or `backend/career_coach.db`.
