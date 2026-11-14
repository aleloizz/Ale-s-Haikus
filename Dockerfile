#
# Immagine di produzione per Ale's Haikus.
# Build multi-stage: il compilatore e libpq-dev restano nel builder, il runtime
# contiene solo Python, libpq5 e l'applicazione.
#
# Digest multi-arch verificato per linux/arm/v7 e linux/arm64.
ARG PYTHON_IMAGE=python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

FROM ${PYTHON_IMAGE} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# Dipendenze di compilazione solo nello stage builder.
# hadolint ignore=DL3008
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /build/requirements.txt

# I-01: in produzione usiamo psycopg2 compilato contro la libpq del runtime,
# non la variante -binary con libpq/OpenSSL bundled.
RUN sed 's/^psycopg2-binary==/psycopg2==/' /build/requirements.txt \
        > /build/requirements-prod.txt \
    && python -m pip wheel \
        --no-cache-dir \
        --wheel-dir /wheels \
        -r /build/requirements-prod.txt

FROM ${PYTHON_IMAGE} AS runtime

ARG APP_VERSION=dev

LABEL org.opencontainers.image.title="Ale's Haikus" \
      org.opencontainers.image.description="Analizzatore metrico e bacheca poetica" \
      org.opencontainers.image.source="https://github.com/aleloizz/Ale-s-Haikus" \
      org.opencontainers.image.version="${APP_VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/tmp

# Runtime minimale: solo libpq5 (psycopg2 compilato) e l'utente non-root.
# Applichiamo gli aggiornamenti Debian disponibili al momento della build:
# il digest della base pinna la distribuzione, non le patch di sicurezza.
# hadolint ignore=DL3005,DL3008
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app \
        --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements-prod.txt /tmp/requirements-prod.txt

RUN python -m pip install \
        --no-cache-dir \
        --no-index \
        --find-links=/wheels \
        -r /tmp/requirements-prod.txt \
    && rm -rf /wheels /tmp/requirements-prod.txt

COPY --chown=app:app . /app

USER 10001:10001

EXPOSE 8000
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]

CMD ["gunicorn", "app:create_app()", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--worker-tmp-dir", "/tmp", \
     "--max-requests", "2000", \
     "--max-requests-jitter", "200", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
