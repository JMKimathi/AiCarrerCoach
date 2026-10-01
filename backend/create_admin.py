"""Create an administrator account from the local command line."""

import getpass
import sys

from backend.app.database import Base, SessionLocal, User, engine
from backend.app.security import hash_password


def main() -> int:
    Base.metadata.create_all(bind=engine)
    name = input("Administrator full name: ").strip()
    email = input("Administrator email: ").strip().lower()
    password = getpass.getpass("Password (minimum 8 characters): ")
    confirm = getpass.getpass("Confirm password: ")
    if len(name) < 2 or "@" not in email or len(password) < 8 or password != confirm:
        print("Invalid details. Check the name, email, password length, and confirmation.")
        return 1
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            print("An account with that email already exists. No changes were made.")
            return 1
        db.add(User(
            user_id=__import__("uuid").uuid4().hex,
            full_name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            course="Staff",
            career_goal="Career advisory administration",
        ))
        db.commit()
        print("Administrator account created.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
