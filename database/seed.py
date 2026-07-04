"""Database seeding script."""

import argparse

from database.connection import get_db_session, init_db
from utils.data_generator import seed_database


def main():
    parser = argparse.ArgumentParser(description="Seed Instagram Analytics database")
    parser.add_argument("--force", action="store_true", help="Regenerate data even if exists")
    args = parser.parse_args()

    init_db()
    with get_db_session() as session:
        result = seed_database(session, force=args.force)
        print("\n=== Seed Complete ===")
        for k, v in result.items():
            print(f"  {k}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")


if __name__ == "__main__":
    main()
