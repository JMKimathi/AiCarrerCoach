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

Log in to the app using the **Log In** tab and the same email and password entered in the command. There is no separate admin sign-in screen. The account must have `role = admin`; signing up in the app always creates a student account. The admin creation command refuses to overwrite an account that already uses the email, and resetting a password does not change its role. Use a different email for the admin account if that address was already registered as a student.

The command uses the same database configured for the API through `DATABASE_URL` in `backend/.env`. If the login is rejected, first check that the API and admin command are using the expected database and inspect the account's role and active status. For the Docker PostgreSQL setup, run:

```powershell
docker exec -it postgres-db psql -U postgres -d career_coach -c "SELECT email, role, is_active FROM users ORDER BY created_at;"
```

For the default local SQLite database, run this from the repository root:

```powershell
& .\backend\.venv\Scripts\python.exe -c "from backend.app.database import SessionLocal, User; db=SessionLocal(); print([(u.email, u.role, u.is_active) for u in db.query(User).order_by(User.created_at)]); db.close()"
```

An inactive account cannot sign in. Keep the account query output private because account email addresses are personal information. Do not share passwords, password hashes, or the contents of `.env` when troubleshooting.

To reset an existing account password locally, run `& .\backend\.venv\Scripts\python.exe -m backend.reset_password` and follow the prompts. The password is not echoed or saved in shell history.

## Troubleshooting

- `GET /api/health` checks whether the API is responding.
- `GET /docs` shows the available API routes.
- Chat can use the authored resource database while local RAG model files are unavailable. Gemini responses require a valid `GEMINI_API_KEY` in `backend/.env`.
- If PostgreSQL is configured through `DATABASE_URL` but unavailable, startup fails clearly; it will not silently switch databases.
- Password recovery email is not configured; reset an account with the local command above.

Do not commit `backend/.env` or `backend/career_coach.db`.
