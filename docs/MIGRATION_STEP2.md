# Step 2 — Deployment Docker/PostgreSQL

Questo step introduce i file di deployment. La scelta di collocazione è:

- **Nel repository** (`Ale-s-Haikus/`): `Dockerfile` e `.dockerignore`.
  Sono parte della build dell'immagine, devono essere versionati e scansionati
  dalla CI.
- **Fuori dal repository** (`aleshaikus-deploy/`): `docker-compose.yml`,
  `.env`, `.env.example`, `secrets/` e la documentazione operativa. Contengono
  configurazione specifica del server e segreti, quindi non vanno nel branch
  della webapp.

## Immagine

- Base multi-arch `python:3.12-slim-trixie` pinnata per digest; supporta
  `linux/arm/v7`, verificato per il Tinker Board a 32 bit.
- Build multi-stage: compilazione di `psycopg2` nel builder, runtime con sola
  `libpq5`.
- Base `slim` invece di distroless: su ARMv7 e con `psycopg2`/`libpq5` è la
  scelta più affidabile; il runtime è comunque non-root, read-only, senza
  capability e con soli pacchetti necessari.
- Utente non-root `10001:10001`, root filesystem read-only nel compose,
  `cap_drop: ALL`, `no-new-privileges`, tmpfs per `/tmp`.
- Healthcheck su `/healthz`, Gunicorn con 2 worker e 4 thread.
- `psycopg2` compilato contro la libpq di runtime (I-01).

## Compose

- `web`: app + Gunicorn, reti `public_net` e `internal_net`, porta solo su
  `127.0.0.1`.
- `db`: PostgreSQL 17 Alpine pinnato, solo `internal_net`, volume nominato,
  password da Docker secret.
- `redis`: Redis 7 Alpine pinnato, solo `internal_net`, password e configurazione
  da Docker secret, persistenza disabilitata per non consumare la microSD.
- `db-init`: servizio one-shot nel profilo `tools` per creare lo schema
  iniziale.
- Limiti: web 384 MB / 1.5 CPU, DB 512 MB / 1 CPU, Redis 128 MB / 0.5 CPU.
- Log Docker ruotati (`10 MB × 3`).

## Segreti

Il compose monta file da `aleshaikus-deploy/secrets/` e l'app li legge tramite:

- `SECRET_KEY_FILE`
- `DATABASE_URL_FILE`
- `RATELIMIT_STORAGE_URI_FILE`

PostgreSQL usa `POSTGRES_PASSWORD_FILE`; Redis usa `redis.conf` e
`redis_password`. Lo script `scripts/generate_secrets.py` crea i file con
permessi `0600` e la directory `0700`, senza stampare i valori.

## Validazione eseguita

Senza Docker Engine nell'ambiente di creazione:

```bash
docker compose config --quiet
docker compose --profile tools config --quiet
hadolint ../Ale-s-Haikus/Dockerfile
trivy config Ale-s-Haikus/Dockerfile
trivy fs Ale-s-Haikus
```

Risultati:

- Compose valido, anche con profilo `tools`.
- Hadolint: nessun warning/errore.
- Trivy config: 0 misconfigurazioni HIGH/CRITICAL sul Dockerfile.
- Trivy fs: 0 vulnerabilità HIGH/CRITICAL su `requirements.txt`.
- Factory di produzione avviata con i segreti letti da file.
- Test applicativi: 41 passed.

La build e l'avvio effettivi vanno eseguiti sul Tinker Board.

Nota: Trivy segnala CVE HIGH non corrette nelle immagini base Debian/Alpine
(per lo più senza patch). Il Dockerfile applica `apt-get upgrade` per le patch
Debian disponibili; la CI usa `ignore-unfixed: true`. Ricostruire e scansionare
periodicamente l'immagine.

## Passi successivi

1. Step 3: aggiungere `cloudflared` su `public_net` con token secret.
2. Step 4: verificare `request.remote_addr` e regolare `TRUSTED_PROXY_COUNT`.
3. Step 5: backup cifrato del volume PostgreSQL e di `secrets/`.
4. Sostituire `db-init` con Alembic/Flask-Migrate.
