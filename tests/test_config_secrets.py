"""Test per il caricamento dei segreti tramite file Docker."""
import pytest

from config import app_config


def test_env_value_reads_file(tmp_path, monkeypatch):
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("valore-da-file\n", encoding="utf-8")
    monkeypatch.delenv("MY_SECRET", raising=False)
    monkeypatch.setenv("MY_SECRET_FILE", str(secret_file))

    assert app_config.env_value("MY_SECRET") == "valore-da-file"


def test_env_value_file_wins_over_environment(tmp_path, monkeypatch):
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("da-file", encoding="utf-8")
    monkeypatch.setenv("MY_SECRET", "da-env")
    monkeypatch.setenv("MY_SECRET_FILE", str(secret_file))

    assert app_config.env_value("MY_SECRET") == "da-file"


def test_env_value_missing_file_fails_fast(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_SECRET_FILE", str(tmp_path / "missing.txt"))

    with pytest.raises(RuntimeError, match="MY_SECRET_FILE"):
        app_config.env_value("MY_SECRET")


def test_env_list_can_read_file(tmp_path, monkeypatch):
    hosts_file = tmp_path / "hosts.txt"
    hosts_file.write_text("example.com, www.example.com\n", encoding="utf-8")
    monkeypatch.setenv("TRUSTED_HOSTS_FILE", str(hosts_file))

    assert app_config.env_list("TRUSTED_HOSTS") == [
        "example.com",
        "www.example.com",
    ]


def test_database_url_forces_psycopg2_driver(monkeypatch):
    monkeypatch.delenv("DATABASE_URL_FILE", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@db:5432/app")

    assert (
        app_config._database_url()
        == "postgresql+psycopg2://user:pass@db:5432/app"
    )


def test_postgresql_url_forces_psycopg2_driver(monkeypatch):
    monkeypatch.delenv("DATABASE_URL_FILE", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/app")

    assert (
        app_config._database_url()
        == "postgresql+psycopg2://user:pass@db:5432/app"
    )
