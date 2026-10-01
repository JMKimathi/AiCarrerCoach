"""Reset a local account password without exposing it in terminal history."""

import getpass
import sys

from backend.app.database import SessionLocal, User
from backend.app.security import hash_password


def main() -> int:
    email = input("Account email: ").strip().lower()
    password = getpass.getpass("New password (minimum 8 characters): ")
    confirm = getpass.getpass("Confirm new password: ")
    if "@" not in email or len(password) < 8 or password != confirm:
        print("Invalid email or password. No changes were made.")
        return 1
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            print("No account exists with that email.")
            return 1
        user.password_hash = hash_password(password)
        user.is_active = True
        db.commit()
        print("Password updated. The account is active.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
