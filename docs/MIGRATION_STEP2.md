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
  password da Docker secret. L'healthcheck usa TCP (`127.0.0.1:5432`) per non
  confondere il server temporaneo di `initdb` con il database pronto.
- `redis`: Redis 7 Alpine pinnato, solo `internal_net`, password e configurazione
  da Docker secret, persistenza disabilitata per non consumare la microSD.
  `maxmemory` è 64 MB, sotto il limite container di 128 MB.
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
`redis_password`. I file secret di Compose sono bind mount e conservano owner
e mode dell'host: lo script `scripts/generate_secrets.py`, eseguito come root,
crea la directory `0700` e assegna `10001:10001 0440` ai segreti di web/db-init,
`999:1000 0440` a quelli di Redis e `root:root 0400` alla password PostgreSQL.
Non stampa mai i valori.

## Validazione eseguita

Senza Docker Engine nell'ambiente di creazione:

```bash
# dalla cartella aleshaikus-deploy
docker compose config --quiet
docker compose --profile tools config --quiet
hadolint ../Ale-s-Haikus/Dockerfile   # solo x86_64/arm64, non ARMv7
trivy config ../Ale-s-Haikus/Dockerfile
trivy fs ../Ale-s-Haikus
```

Risultati:

- Compose valido, anche con profilo `tools`.
- Hadolint: nessun warning/errore.
- Trivy config: 0 misconfigurazioni HIGH/CRITICAL sul Dockerfile.
- Trivy fs: 0 vulnerabilità HIGH/CRITICAL su `requirements.txt`.
- `pip-audit`: nessuna vulnerabilità nota.
- Factory di produzione avviata con i segreti letti da file.
- Test applicativi: 46 passed.

La build e l'avvio effettivi vanno eseguiti sul Tinker Board. Hadolint non
pubblica binari per `linux/arm/v7` e l'immagine Docker ufficiale non supporta
questa architettura: va eseguito su laptop o in CI. Trivy invece ha un pacchetto
`armhf` (binario statico) utilizzabile sul Tinker Board, ma resta opzionale.
Il repository include un workflow CI che esegue Hadolint, build e Trivy.

Nota: Trivy segnala CVE HIGH non corrette nelle immagini base Debian/Alpine
(per lo più senza patch). Il Dockerfile applica `apt-get upgrade` per le patch
Debian disponibili; la CI usa `ignore-unfixed: true`. Ricostruire e scansionare
periodicamente l'immagine.

## Passi successivi

1. Step 3: `cloudflared` su `public_net` con token secret e tunnel reale.
2. Step 4: completato; `ProxyFix` usa l'IP reale del client e il rate limiter
   applica chiavi distinte.
3. Step 5: backup cifrato di database, configurazione e `secrets/`.
4. Sostituire `db-init` con Alembic/Flask-Migrate.

La documentazione operativa dettagliata degli Step 3-5, del backup, del deploy
e del cutover è mantenuta nella cartella privata `aleshaikus-deploy/docs/`,
fuori da questa repository pubblica.
