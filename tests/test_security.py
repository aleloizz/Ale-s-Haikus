"""Regressioni di sicurezza per la migrazione Heroku -> Docker/PostgreSQL.

I test coprono le catene XSS descritte nell'assessment, CSRF, header di
sicurezza, host fidati, limiti anti-DoS, status code corretti e like atomici.
"""
import re

import pytest

from models.poem import Poem, PoemLike, db
from services.poetry_analyzer import verifica_metrica
from utils import text_processing
from utils.text_processing import sanitize_user_text
from tests.conftest import seed_poem

XSS_TYPE_PAYLOAD = "<svg/onload=&#111;&#112;&#101;&#110;()>distico"
XSS_CONTENT_PAYLOAD = "<img src=x onerror=alert(1)>"


def _get_csrf_token(client):
    client.get("/")
    with client.session_transaction() as session:
        return session.get("_csrf_token")


# ---------------------------------------------------------------------------
# H-01: poem_type allowlist
# ---------------------------------------------------------------------------
def test_poem_type_xss_payload_is_rejected(client, app):
    response = client.post(
        "/api/poems",
        json={"text": "a\nb", "author": "tester", "poem_type": XSS_TYPE_PAYLOAD},
    )

    assert response.status_code == 400
    assert response.get_json()["error_type"] == "invalid_poem_type"
    with app.app_context():
        assert Poem.query.count() == 0


def test_verifica_metrica_has_no_distico_substring_bypass():
    assert verifica_metrica(XSS_TYPE_PAYLOAD, 2, [1, 1], "") is False


def test_recognized_legacy_type_is_normalized_to_allowlisted_slug(client, app):
    # "distico (rima baciata)" è un'etichetta legacy dell'analizzatore.
    with app.app_context():
        poem = Poem.create_from_analysis(
            "titolo",
            "primo\nsecondo",
            "autore",
            {
                "tipo_riconosciuto": "distico (rima baciata)",
                "num_versi": 2,
                "sillabe_per_verso": [11, 11],
                "schema_rime": "AA",
                "rispetta_metrica": True,
            },
        )
        assert poem.poem_type == "distico"


def test_model_rejects_untrusted_override():
    with pytest.raises(ValueError):
        Poem.create_from_analysis(
            "titolo",
            "a\nb",
            "autore",
            {"tipo_riconosciuto": "distico", "num_versi": 2},
            poem_type_override=XSS_TYPE_PAYLOAD,
        )


# ---------------------------------------------------------------------------
# H-02: fail-closed sanitizer and escaped rendering
# ---------------------------------------------------------------------------
def test_sanitizer_fails_closed_without_bleach(monkeypatch):
    monkeypatch.setattr(text_processing, "BLEACH_AVAILABLE", False)
    result = text_processing.sanitize_user_text(XSS_CONTENT_PAYLOAD)

    assert "<img" not in result
    assert "onerror" in result  # resta testo, non markup
    assert "&lt;img" in result


def test_sanitizer_strips_tags_when_bleach_is_available():
    assert sanitize_user_text("ciao <b>mondo</b>") == "ciao mondo"


def test_bacheca_escapes_stored_content_and_type(client, app):
    seed_poem(
        app,
        title="Payload",
        content=XSS_CONTENT_PAYLOAD + "\nsecondo",
        poem_type=XSS_TYPE_PAYLOAD,
    )

    response = client.get("/bacheca")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "&lt;img" in html
    assert "<img src=x" not in html
    assert "&lt;svg" in html
    assert "<svg/onload" not in html


def test_detail_page_escapes_stored_content(client, app):
    poem_id = seed_poem(app, content=XSS_CONTENT_PAYLOAD)
    response = client.get(f"/poesia/{poem_id}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "&lt;img" in html
    assert "<img src=x" not in html


# ---------------------------------------------------------------------------
# M-01: CSRF and Origin checks
# ---------------------------------------------------------------------------
def test_csrf_token_is_required_for_api_writes(client, app):
    app.config["CSRF_ENABLED"] = True
    token = _get_csrf_token(client)

    without_token = client.post(
        "/api/analyze", json={"text": "primo\nsecondo\nterzo"}
    )
    assert without_token.status_code == 403

    with_token = client.post(
        "/api/analyze",
        json={"text": "primo\nsecondo\nterzo"},
        headers={"X-CSRF-Token": token},
    )
    assert with_token.status_code != 403


def test_csrf_rejects_cross_origin_request(client, app):
    app.config["CSRF_ENABLED"] = True
    token = _get_csrf_token(client)

    response = client.post(
        "/api/analyze",
        json={"text": "primo\nsecondo\nterzo"},
        headers={"X-CSRF-Token": token, "Origin": "https://evil.example"},
    )
    assert response.status_code == 403
    assert "Origine" in response.get_data(as_text=True)


# ---------------------------------------------------------------------------
# M-03: pagination and publish limits
# ---------------------------------------------------------------------------
def test_bacheca_per_page_is_clamped(client, app):
    for index in range(55):
        seed_poem(app, title=f"Poesia {index}")

    response = client.get("/api/bacheca?per_page=1000000&page=1")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["per_page"] == 50
    assert len(payload["poesie"]) == 50


def test_bacheca_page_is_clamped(client):
    response = client.get("/api/bacheca?page=999999")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["current_page"] == 1000


def test_analyze_rejects_oversized_text(client):
    response = client.post("/api/analyze", json={"text": "a" * 2001})
    assert response.status_code == 400
    assert response.get_json()["error_type"] == "too_long"


def test_publish_rejects_oversized_text(client):
    response = client.post(
        "/api/poems",
        json={"text": "a" * 5001, "author": "tester", "poem_type": "versi_liberi"},
    )
    assert response.status_code == 400
    assert response.get_json()["error_type"] == "too_long"


def test_publish_rejects_too_many_lines(client):
    response = client.post(
        "/api/poems",
        json={
            "text": "\n".join(["verso"] * 201),
            "author": "tester",
            "poem_type": "versi_liberi",
        },
    )
    assert response.status_code == 400
    assert response.get_json()["error_type"] == "too_many_lines"


def test_publish_accepts_valid_free_verse_alias(client, app):
    response = client.post(
        "/api/poems",
        json={
            "text": "primo verso\nsecondo verso",
            "author": "tester",
            "poem_type": "verso libero",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["poem_type"] == "versi_liberi"
    with app.app_context():
        assert Poem.query.count() == 1


def test_api_requires_json_content_type(client):
    response = client.post("/api/analyze", data="text=ciao")
    assert response.status_code == 400


def test_oversized_request_body_returns_413(client):
    body = '{"text":"' + ("a" * (1024 * 1024 + 16)) + '"}'
    response = client.post(
        "/api/analyze", data=body, content_type="application/json"
    )
    assert response.status_code == 413


# ---------------------------------------------------------------------------
# M-05 / L-04: security headers and CSP nonce
# ---------------------------------------------------------------------------
def test_security_headers_and_csp_nonce(client):
    response = client.get("/")
    headers = response.headers
    csp = headers["Content-Security-Policy"]

    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp
    assert "script-src 'self' 'nonce-" in csp
    assert "script-src" in csp and "unsafe-inline" not in csp.split(";")[1]

    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-XSS-Protection"] == "0"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in headers
    assert headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert headers["X-Request-ID"]

    nonce = re.search(r"'nonce-([^']+)'", csp).group(1)
    assert f'nonce="{nonce}"' in response.get_data(as_text=True)


def test_hsts_is_sent_for_https_requests(client):
    response = client.get("/", base_url="https://localhost")
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")


# ---------------------------------------------------------------------------
# M-06: host header and canonical sitemap
# ---------------------------------------------------------------------------
def test_untrusted_host_is_rejected(client, app):
    app.config["TRUSTED_HOSTS"] = ["example.com"]
    response = client.get("/", headers={"Host": "evil.example"})
    assert response.status_code == 400


def test_sitemap_uses_configured_canonical_base(client, app):
    app.config["CANONICAL_BASE_URL"] = "https://canonical.example"
    response = client.get(
        "/sitemap-static.xml", headers={"Host": "evil.example"}
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "https://canonical.example/" in body
    assert "evil.example" not in body


# ---------------------------------------------------------------------------
# M-07: correct 404 handling and missing templates
# ---------------------------------------------------------------------------
def test_api_404_returns_json(client):
    response = client.get("/api/poesia/999999")
    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["error"] is True


def test_missing_poem_returns_404_html(client):
    response = client.get("/poesia/999999")
    assert response.status_code == 404
    assert "Pagina non trovata" in response.get_data(as_text=True)


def test_unknown_path_returns_404(client):
    response = client.get("/questa-pagina-non-esiste")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# M-02: server-side like uniqueness
# ---------------------------------------------------------------------------
def test_like_is_idempotent_per_voter(client, app):
    poem_id = seed_poem(app)

    first = client.post(f"/api/poems/{poem_id}/like", json={})
    second = client.post(f"/api/poems/{poem_id}/like", json={})

    assert first.status_code == 200
    assert first.get_json()["likes"] == 1
    assert second.status_code == 200
    assert second.get_json()["likes"] == 1
    assert second.get_json()["already_liked"] is True

    with app.app_context():
        assert PoemLike.query.count() == 1
        assert db.session.get(Poem, poem_id).likes == 1


def test_like_unlike_updates_counter_atomically(client, app):
    poem_id = seed_poem(app)

    client.post(f"/api/poems/{poem_id}/like", json={})
    response = client.post(f"/api/poems/{poem_id}/unlike", json={})

    assert response.status_code == 200
    assert response.get_json()["likes"] == 0
    assert response.get_json()["liked"] is False

    with app.app_context():
        assert PoemLike.query.count() == 0


def test_like_status_reflects_voter(client, app):
    poem_id = seed_poem(app)
    client.post(f"/api/poems/{poem_id}/like", json={})

    response = client.get(f"/api/poems/{poem_id}/like/status")
    assert response.status_code == 200
    assert response.get_json()["liked"] is True
    assert response.get_json()["likes"] == 1


def test_like_requires_json(client, app):
    poem_id = seed_poem(app)
    response = client.post(f"/api/poems/{poem_id}/like")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
def test_healthz_checks_database(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
