"""Test del comportamento dietro Cloudflare Tunnel.

`ProxyFix` deve usare un solo hop fidato per `X-Forwarded-For` e
`X-Forwarded-Proto`, senza permettere a `X-Forwarded-Host` di riscrivere
l'Host. L'Host resta validato da `TRUSTED_HOSTS`.
"""
from flask import request

from app import create_app
from config.app_config import TestingConfig, config


class ProxyTestingConfig(TestingConfig):
    TRUSTED_PROXY_COUNT = 1
    TRUSTED_HOSTS = ["www.aleshaikus.me", "localhost", "127.0.0.1"]
    CANONICAL_BASE_URL = "https://www.aleshaikus.me"
    PREFERRED_URL_SCHEME = "https"
    SESSION_COOKIE_SECURE = True
    CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    AUTO_CREATE_DB = False


config["proxy_testing"] = ProxyTestingConfig


def _proxy_app():
    app = create_app("proxy_testing")

    @app.route("/_proxy_probe")
    def proxy_probe():
        return {
            "remote_addr": request.remote_addr,
            "scheme": request.scheme,
            "is_secure": request.is_secure,
            "host": request.host,
        }

    return app


def test_proxy_fix_uses_forwarded_for_and_proto():
    client = _proxy_app().test_client()

    response = client.get(
        "/_proxy_probe",
        base_url="https://www.aleshaikus.me",
        headers={
            "X-Forwarded-For": "203.0.113.10",
            "X-Forwarded-Proto": "https",
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "remote_addr": "203.0.113.10",
        "scheme": "https",
        "is_secure": True,
        "host": "www.aleshaikus.me",
    }


def test_proxy_fix_uses_rightmost_forwarded_for_value():
    client = _proxy_app().test_client()

    response = client.get(
        "/_proxy_probe",
        base_url="https://www.aleshaikus.me",
        headers={
            # Il client può inviare un valore spoofato; Cloudflare accoda
            # l'IP reale. Con un solo hop fidato vale il valore più a destra.
            "X-Forwarded-For": "198.51.100.99, 203.0.113.10",
            "X-Forwarded-Proto": "https",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["remote_addr"] == "203.0.113.10"


def test_forwarded_host_cannot_rewrite_host():
    client = _proxy_app().test_client()

    response = client.get(
        "/_proxy_probe",
        base_url="https://www.aleshaikus.me",
        headers={
            "X-Forwarded-Host": "evil.example",
            "X-Forwarded-Proto": "https",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["host"] == "www.aleshaikus.me"


def test_untrusted_host_is_rejected():
    client = _proxy_app().test_client()

    response = client.get(
        "/_proxy_probe",
        base_url="https://evil.example",
        headers={"X-Forwarded-Proto": "https"},
    )

    assert response.status_code == 400
