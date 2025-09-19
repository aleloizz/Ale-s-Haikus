import argparse
import sys
from sqlalchemy import text


def main():
    parser = argparse.ArgumentParser(description="Delete poems from the database")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", type=int, help="Poem id to delete")
    group.add_argument("--author_title", nargs=2, metavar=("AUTHOR", "TITLE"), help="Delete by author and exact title")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without committing")

    args = parser.parse_args()

    # Importi dentro al contesto app per usare la stessa config DB dell'istanza
    try:
        from app import app
        from models.poem import db
    except Exception as e:
        print(f"Errore: impossibile importare app/db: {e}")
        return 2

    with app.app_context():
        if args.id is not None:
            # Mostra prima cosa elimineresti
            row = db.session.execute(text("SELECT id, title, author FROM poems WHERE id = :id"), {"id": args.id}).fetchone()
            if not row:
                print(f"Nessuna poesia con id={args.id}")
                return 0
            print(f"Trovata poesia: id={row.id}, title={row.title}, author={row.author}")

            if args.dry_run:
                print("Dry-run: nessuna cancellazione eseguita")
                return 0

            res = db.session.execute(text("DELETE FROM poems WHERE id = :id"), {"id": args.id})
            db.session.commit()
            print(f"Rimosse {res.rowcount or 0} righe")
            return 0

        # Autore + Titolo
        author, title = args.author_title
        rows = db.session.execute(
            text("SELECT id, title, author FROM poems WHERE author = :author AND title = :title"),
            {"author": author, "title": title}
        ).fetchall()

        if not rows:
            print(f"Nessuna poesia trovata per author='{author}' e title='{title}'")
            return 0

        print("Poesie corrispondenti:")
        for r in rows:
            print(f" - id={r.id} | {r.title} by {r.author}")

        if args.dry_run:
            print("Dry-run: nessuna cancellazione eseguita")
            return 0

        res = db.session.execute(
            text("DELETE FROM poems WHERE author = :author AND title = :title"),
            {"author": author, "title": title}
        )
        db.session.commit()
        print(f"Rimosse {res.rowcount or 0} righe")
        return 0


if __name__ == "__main__":
    sys.exit(main())
