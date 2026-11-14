"""Estensioni Flask condivise.

Il limiter è definito qui (e non dentro ``create_app``) perché i decoratori
``@limiter.limit(...)`` devono poter essere importati dai blueprint.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    headers_enabled=True,
)
