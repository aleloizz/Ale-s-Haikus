# Step 1 — Preparazione codice per Docker/PostgreSQL

Questo documento descrive le modifiche applicate al codice sorgente prima di
scrivere `Dockerfile`, `docker-compose.yml` e i file di deployment (Step 2).
Nessun file di deployment è stato creato o applicato in questa fase.

## Obiettivo

Rendere l'applicazione pronta a girare su un container con PostgreSQL, senza
fallback SQLite silenzioso, e chiudere le vulnerabilità P0/P1 dell'assessment
`Ale-s-Haikus-Security-Assessment.md`.

## Modifiche principali

### Database e configurazione

- `DATABASE_URL` è obbligatoria in produzione; l'app rifiuta di avviarsi se
  manca o se non punta a PostgreSQL.
- Nessun fallback SQLite in produzione. SQLite resta solo per sviluppo/test.
- `SECRET_KEY` deve essere presente, non un placeholder e lunga almeno 32
  caratteri in produzione.
- In produzione l'app rifiuta anche `CSRF_ENABLED=false`,
  `RATELIMIT_ENABLED=false`, `SESSION_COOKIE_SECURE=false`,
  `SESSION_COOKIE_HTTPONLY=false` e `SameSite` diverso da `Lax`/`Strict`.
- `AUTO_CREATE_DB` è disattivato di default in produzione. Lo schema iniziale
  si crea esplicitamente una volta con:

  ```bash
  APP_CONFIG=production flask --app app init-db
  ```

  È una baseline temporanea: Alembic/Flask-Migrate arriverà in uno step
  successivo. Non usare `AUTO_CREATE_DB=true` come soluzione permanente.

### Sicurezza applicativa

| Finding | Intervento |
|---|---|
| H-01 | Allowlist `poem_type` lato API e modello; rimosso il bypass `"distico" in tipo`; normalizzazione alias esplicita. |
| H-02 | `sanitize_user_text()` fail-closed; controllo di importabilità di `bleach` in produzione; rimosso `|safe` dal contenuto poesie; rendering con `textContent`/DOM. |
| M-01 | CSRF synchronizer token in sessione, header `X-CSRF-Token`, meta tag e controllo `Origin`/`Referer`. |
| M-02 | Tabella `poem_likes` con vincolo unico `(poem_id, voter_key)`; contatore aggiornato atomicamente; `voter_key` = HMAC-SHA256(IP + User-Agent). |
| M-03 | Limiti su `page`, `per_page`, testo, titolo, autore e numero versi; `MAX_CONTENT_LENGTH` 1 MiB; Gunicorn con 2 worker e 4 thread. |
| M-04 | `ProxyFix` configurabile, `TRUSTED_PROXY_COUNT`, rate limit per endpoint e storage configurabile via `RATELIMIT_STORAGE_URI`. |
| M-05 | CSP con nonce, HSTS, Referrer-Policy, Permissions-Policy, COOP/CORP, cookie `Secure`/`SameSite=Lax`/`HttpOnly`. |
| M-06 | `TRUSTED_HOSTS`, sitemap costruite su `CANONICAL_BASE_URL`, redirect HTTPS senza usare l'Host della richiesta. |
| M-07 | 404 API/HTML corretti, template `404.html` e `dettaglio_poesia.html`, errori 5xx generici e loggati. |
| M-08 | Logging strutturato JSON opzionale, request ID, log di richieste e eventi di sicurezza. |
| L-01 | Bootstrap JS e Bootstrap Icons serviti localmente da `static/vendor/`; rimossi i CDN jsDelivr. Google Fonts/GA4 restano esterni e sono dichiarati nella CSP. |
| L-02 | CI con test e `pip-audit` (advisory) + Dependabot. |
| L-03 | Fail-fast su `DATABASE_URL`; `create_all()` gated; comando `init-db`. |
| L-04 | `X-XSS-Protection: 0`. |
| L-05 | Il sanitizer JS resta solo UX; il server è l'autorità. |
| L-06 | Fallback dev esplicitamente locale; hardening cookie; like fuori dalla sessione. |
| L-07 | Messaggi e dettagli server renderizzati con `textContent`/DOM, non `innerHTML`. |
| M-09 | Non implementato in questa fase: moderazione/CAPTCHA/quota restano roadmap P2. |

## Variabili d'ambiente

| Variabile | Obbligatoria | Default | Note |
|---|---|---|---|
| `APP_CONFIG` | consigliata | `production` | `production`, `development`, `testing`. |
| `SECRET_KEY` | sì in produzione | — | ≥ 32 caratteri casuali. |
| `DATABASE_URL` | sì in produzione | — | `postgresql+psycopg2://...`; `postgres://` viene normalizzato. |
| `AUTO_CREATE_DB` | no | `false` in produzione | Solo bootstrap temporaneo. |
| `TRUSTED_HOSTS` | sì in produzione | domini del sito + localhost | Lista separata da virgole. |
| `CANONICAL_BASE_URL` | sì in produzione | `https://www.aleshaikus.me` | Deve essere `https://`. |
| `TRUSTED_PROXY_COUNT` | no | `1` in produzione | Hop fidati davanti a Flask. |
| `RATELIMIT_STORAGE_URI` | no | `memory://` | In produzione usare Redis per più worker. |
| `RATELIMIT_ENABLED` | no | `true` | — |
| `CSRF_ENABLED` | no | `true` | Non disattivare in produzione. |
| `SESSION_COOKIE_SECURE` | no | `true` in produzione | — |
| `LOG_LEVEL` | no | `INFO` | — |
| `LOG_JSON` | no | `true` in produzione | Log JSON per Docker/Cloudflare. |
| `GOOGLE_SITE_VERIFICATION` | no | — | Meta tag Search Console. |

## Comandi utili

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Sviluppo
APP_CONFIG=development flask --app app run --debug

# Test
APP_CONFIG=testing python -m pytest -q

# Produzione (esempio; le variabili reali arriveranno nello Step 2)
APP_CONFIG=production gunicorn 'app:create_app()' \
  --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 60
```

## Note per lo Step 2

- Il `Procfile` ora usa la factory `app:create_app()` e non `app:app`.
- In Docker impostare `APP_CONFIG=production`, `TRUSTED_PROXY_COUNT=1` e
  `RATELIMIT_STORAGE_URI=redis://...` se si usano più worker.
- `AUTO_CREATE_DB` va lasciato `false`; eseguire `flask --app app init-db` una
  volta (o una migrazione Alembic quando sarà introdotta).
- `psycopg2-binary` resta in `requirements.txt` per comodità locale; il
  Dockerfile lo sostituisce con `psycopg2` compilato contro la libpq di runtime
  (I-01).
- `static.json` e `CNAME` sono residui Heroku/GitHub Pages: vanno rimossi o
  sostituiti nella fase di deployment.
- Normalizzare le righe `poem_type` legacy già presenti in produzione (es.
  `distico (rima baciata)`, `ottava`, `verso libero`) verso gli slug canonici
  con una migrazione dati, così i filtri della bacheca restano coerenti.
- Google Fonts e Google Analytics restano dipendenze esterne fidate; la CSP le
  consente esplicitamente. Valutarne la self-hostizzazione in seguito.
- Ruotare `SECRET_KEY`, credenziali PostgreSQL e config var storiche (I-02).

## Verifica eseguita

```bash
APP_CONFIG=testing python -m pytest -q
# 42 passed
```

I test coprono: payload XSS H-01, sanitizer fail-closed, escaping in bacheca e
dettaglio, CSRF e Origin, clamp paginazione, limiti publish/analyze, header di
sicurezza e nonce CSP, HSTS, Host header, sitemap canonica, 404 API/HTML,
unicità e atomicità dei like, health check e guardrail sui template.
