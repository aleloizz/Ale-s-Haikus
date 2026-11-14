import os
import sys
from pathlib import Path

os.environ.setdefault("APP_CONFIG", "testing")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from models.poem import Poem, db  # noqa: E402


@pytest.fixture()
def app():
    application = create_app("testing")
    application.config.update(TESTING=True)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def seed_poem(
    app,
    *,
    title="Poesia di prova",
    content="primo verso\nsecondo verso\nterzo verso",
    author="Tester",
    poem_type="haiku",
    is_valid=True,
    likes=0,
):
    with app.app_context():
        poem = Poem(
            title=title,
            content=content,
            author=author,
            verse_count=3,
            syllable_counts="5,7,5",
            rhyme_scheme="",
            poem_type=poem_type,
            is_valid=is_valid,
            likes=likes,
        )
        db.session.add(poem)
        db.session.commit()
        return poem.id
