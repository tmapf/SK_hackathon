#!/usr/bin/env python3
"""Create or update an administrator account."""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal, Base, engine
from app.services.seed import ensure_admin, seed_defaults


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an administrator account")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_defaults(db)
        admin = ensure_admin(db, args.username, args.password)
        # Always refresh password when script is used intentionally
        from app.security.passwords import hash_password

        admin.password_hash = hash_password(args.password)
        admin.is_active = True
        db.commit()
        print(f"Administrator ready: {admin.username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
