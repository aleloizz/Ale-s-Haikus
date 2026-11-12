"""Guardrail statici su template e asset vendorizzati.

Questi test impediscono di reintrodurre ``|safe``, handler inline (bloccati
dalla CSP) o dipendenze CDN per gli asset critici.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


def _template_files():
    return sorted(TEMPLATES.glob("*.html"))


def test_templates_do_not_use_safe_filter():
    for template in _template_files():
        text = template.read_text(encoding="utf-8")
        assert "|safe" not in text, f"{template.name} usa ancora |safe"


def test_templates_have_no_inline_event_handlers():
    pattern = re.compile(r"\son(?:click|load|submit|error|change|input)\s*=", re.I)
    for template in _template_files():
        text = template.read_text(encoding="utf-8")
        assert not pattern.search(text), f"{template.name} contiene handler inline"


def test_inline_scripts_have_a_csp_nonce():
    script_pattern = re.compile(r"<script\b[^>]*>", re.I)
    for template in _template_files():
        for tag in script_pattern.findall(template.read_text(encoding="utf-8")):
            if re.search(r"\bsrc\s*=", tag, re.I):
                continue
            assert "nonce=" in tag, (
                f"{template.name}: script inline senza nonce -> {tag}"
            )


def test_templates_do_not_load_jsdelivr_assets():
    for template in _template_files():
        text = template.read_text(encoding="utf-8")
        assert "cdn.jsdelivr.net" not in text, f"{template.name} usa jsDelivr"


def test_critical_vendor_assets_exist():
    assert (ROOT / "static/vendor/bootstrap/bootstrap.bundle.min.js").is_file()
    assert (
        ROOT / "static/vendor/bootstrap-icons/bootstrap-icons.min.css"
    ).is_file()
    assert (
        ROOT / "static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2"
    ).is_file()


def test_bacheca_renders_poem_content_without_safe_filter():
    text = (TEMPLATES / "bacheca.html").read_text(encoding="utf-8")
    assert "{{ poem.content }}" in text
    assert "poem.content|replace" not in text
