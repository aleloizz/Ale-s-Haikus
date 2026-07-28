<div align="center">

<img src="static/android-chrome-512x512.png" alt="Ale's Haikus Logo" width="120" height="120" style="border-radius: 16px;">

# Ale's Haikus

### Analizza, crea e condividi poesie brevi

[![Live Site](https://img.shields.io/badge/Live-aleshaikus.me-8B5CF6?style=for-the-badge&logo=globe&logoColor=white)](https://www.aleshaikus.me)
[![GitHub](https://img.shields.io/badge/GitHub-Ale's%20Haikus-1e142c?style=for-the-badge&logo=github)](https://github.com/aleloizz/Ale-s-Haikus)
[![Made with Flask](https://img.shields.io/badge/Made%20with-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
<br>
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=flat-square&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Heroku](https://img.shields.io/badge/Heroku-430098?style=flat-square&logo=heroku&logoColor=white)](https://heroku.com)

</div>

---

## Panoramica

**Ale's Haikus** è una web app dedicata all'arte della poesia breve. Che tu sia un poeta esperto o alle prime armi, la piattaforma ti offre tutto il necessario per **scrivere**, **analizzare** e **condividere** le tue creazioni poetiche.

Il cuore dell'applicazione è un **conta-sillabe avanzato per la lingua italiana** che gestisce le sfumature della metrica italiana — dittonghi, iati, sineresi e decine di eccezioni linguistiche — rendendolo uno strumento indispensabile per chiunque scriva poesia strutturata in italiano.

> **Live su:** [www.aleshaikus.me](https://www.aleshaikus.me)

---

## Funzionalita

### Analizzatore metrico

Il motore principale fornisce un **sistema di analisi metrica completo**:

| Funzione | Descrizione |
|----------|-------------|
| **Conteggio sillabe** | Algoritmo di precisione che gestisce dittonghi, trittonghi, iati, prefissi vocalici e un dizionario curato di eccezioni linguistiche |
| **Rilevamento rime** | Identificazione automatica dello schema rimico (ABA, ABBA, AABBA, ABCB, ecc.) |
| **Riconoscimento forme** | Rilevamento automatico della forma poetica dai versi inseriti (haiku, sonetto, tanka, ecc.) |
| **Validazione in tempo reale** | Feedback visivo con badge del conteggio sillabe e indicatori dello stato delle rime |
| **Modalita tolleranza** | Tolleranza opzionale ±1 sillaba per poesie flessibili o dialettali |
| **Pubblicazione** | Pubblicazione con un clic sulla bacheca comunitaria |

### Forme poetiche supportate

Ale's Haikus supporta un'ampia varieta di strutture poetiche da diverse tradizioni:

| Italiane | Giapponesi | Inglesi |
|:--------:|:----------:|:-------:|
| Sonetto (14 versi, 11 sillabe) | Haiku (5-7-5) | Limerick (AABBA) |
| Quartina (4 versi, 11 sillabe) | Tanka (5-7-5-7-7) | Ballad (ABCB) |
| Terzina dantesca (11-11-11) | Katauta (5-7-7) | Clerihew (AABB) |
| Ottava rima (ABABABCC) | Choka (5-7-5-7-5-7-5-7-7) | Cinquain (2-4-6-8-2) |
| Stornello (5-11-11, ABA) | Sedoka (5-7-7-5-7-7) | |
| Versi liberi | | |

### Bacheca comunitaria

Leggi, scopri e condividi l'ispirazione poetica con la comunità:

- **Sfoglia poesie** in vista griglia o lista con layout masonry
- **Filtri avanzati** — ricerca per testo, autore o forma poetica
- **Opzioni di ordinamento** — per data, titolo, autore o tipo di poesia
- **Like** — metti un cuore alle tue poesie preferite, e mostra la tua approvazione a chi le ha scritte
- **Condivisione** — generazione di immagini Canvas per i social network
- **Paginazione** — navigazione fluida tra le pagine

### Wiki poetica

Una risorsa educativa che spiega la **storia, le regole e la struttura** di ogni forma poetica supportata, ideale per chi si avvicina per la prima volta alla scrittura poetica.

### Generazione immagini di condivisione

Trasforma qualsiasi poesia in un'**immagine condivisibile** (formato storia 1080×1920 o post 1080×1350) con sfondi personalizzabili, pronta per Instagram, WhatsApp, Facebook e Twitter/X.

### Progressive Web App

Ale's Haikus e installabile come PWA:

- Aggiunta alla schermata home su iOS e Android
- Integrazione con la barra di stato tramite theme-color
- Service worker registrato
- Design responsive che si adatta a ogni dimensione di schermo
- Pulsanti ottimizzati al tocco con area minima di 44px

### Ottimizzazione SEO

- Sitemap XML dinamiche (sitemap index, pagine statiche, poesie)
- Dati strutturati JSON-LD (Organization, WebSite, BreadcrumbList, FAQ)
- Meta tag Open Graph e Twitter Card per anteprime social
- URL canonici con tag hreflang
- Schema FAQ per risultati di ricerca avanzati

---

## Design e UX

Ale's Haikus presenta un'identita visiva **glassmorphism**, con una palette calda e ispirata ai colori del tramonto:

```
Palette colori
  Primary    #D4B8FF  Lavanda tenue
  Secondary  #FFE5D9  Pesca calda
  Accent     #A2D7D8  Verde menta
  Text       #5E5E5E  Grigio caldo
  Background #FAF7FF  Bianco avorio
  Dark       #1E142C  Viola profondo
```
---

## Architettura

```
aleshaikus/
+-- app.py                  # Flask application factory
+-- Procfile                # Configurazione deploy Heroku
+-- requirements.txt        # Dipendenze Python
+-- static.json             # Regole cache file statici
+-- CNAME                   # Dominio personalizzato
+-- config/
|   +-- app_config.py       # Configurazione ambienti (dev/prod/test)
|   +-- constants.py        # Costanti linguistiche e definizioni forme poetiche
+-- models/
|   +-- poem.py             # Modello SQLAlchemy Poem
+-- routes/
|   +-- api.py              # Endpoint REST API
|   +-- web.py              # Route web
+-- services/
|   +-- poetry_analyzer.py  # Orchestratore analisi poetica completa
|   +-- syllable_analyzer.py# Motore conteggio sillabe italiano
|   +-- rhyme_analyzer.py   # Rilevamento rime e identificazione schema
+-- utils/
|   +-- text_processing.py  # Sanificazione testo (Bleach) e utilita linguistiche
|   +-- delete_poem.py      # CLI per gestione poesie nel database
+-- templates/              # Template Jinja2
|   +-- landing.html        # Landing page (hero + introduzione SVG animata)
|   +-- index.html          # Pagina analizzatore poetico
|   +-- bacheca.html        # Bacheca comunitaria
|   +-- wiki.html           # Wiki forme poetiche
|   +-- 500.html, 404.html, comingsoon.html
+-- static/
    +-- css/                # CSS modulari
    +-- js/                 # Moduli ES6
    +-- images/             # Background, immagini OG, template condivisione
```

### Motore di conteggio sillabe

L'analizzatore di sillabe e il componente centrale del progetto. Gestisce:

1. **Dizionario eccezioni** — circa 35 eccezioni predefinite (`"poesia"`=4, `"qui"`=1, `"whisky"`=2)
2. **Digrammi e trigrammi** — gestione gruppi consonantici `gn`, `sc`, `sci`
3. **Dittonghi** — crescenti (`iu`, `ie`, `uo`), discendenti (`ai`, `eu`, `oi`), varianti accentate
4. **Trittonghi** — combinazioni di tre vocali (`iai`, `uai`, `iei`, `uei`)
5. **Rilevamento iati** — coppie vocaliche che deliberatamente NON formano dittongo
6. **Gestione apostrofi** — separazione di `dell'`, `nell'`, `all'`, `dall'`, `sull'`, `quest'`, ecc.
7. **Elaborazione prefissi** — oltre 40 prefissi italiani comuni con separazione del confine vocalico
8. **Sineresi e dialefe** — supporto per schemi naturali del parlato italiano

### API Endpoints

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/analyze` | POST | Analisi metrica di una poesia (sillabe, rime, struttura) |
| `/api/poems` | POST | Pubblicazione di una poesia sulla bacheca |
| `/api/pubblica` | POST | Endpoint legacy per pubblicazione |
| `/api/bacheca` | GET | Recupero poesie con paginazione e filtri |
| `/api/poesia/<id>` | GET | Dettaglio di una singola poesia |
| `/api/poems/<id>/like` | POST | Aggiunta like a una poesia |
| `/api/poems/<id>/unlike` | POST | Rimozione like da una poesia |
| `/api/poems/<id>/like/status` | GET | Stato like per la sessione corrente |
| `/api/stats` | GET | Statistiche generali della bacheca |

### Mappa delle route

| Route | Pagina | Descrizione |
|-------|--------|-------------|
| `/` | Landing | Hero con animazione SVG + card funzionalita |
| `/analizzatore` | Analizzatore | Tool principale di analisi poetica |
| `/bacheca` | Bacheca | Galleria poesie comunitarie con filtri |
| `/wiki` | Wiki | Guida educativa alle forme poetiche |
| `/poesia/<id>` | Dettaglio | Vista singola poesia |
| `/comingsoon` | Coming Soon | Pagina placeholder |
| `/sitemap.xml` | XML | Sitemap index |
| `/sitemap-static.xml` | XML | Sitemap pagine statiche |
| `/sitemap-poesie.xml` | XML | Sitemap poesie dinamiche |

---

## Primi passi

### Prerequisiti

- Python 3.12+
- PostgreSQL (consigliato per produzione) o SQLite (per sviluppo)

### Sviluppo locale

```bash
# Clona il repository
git clone https://github.com/aleloizz/Ale-s-Haikus.git
cd Ale-s-Haikus

# Crea un ambiente virtuale
python3 -m venv venv
source venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt

# Esegui in modalita sviluppo
SECRET_KEY=dev-key FLASK_ENV=development python -c "
from app import create_app
app = create_app('development')
app.run(debug=True, host='0.0.0.0', port=5000)
"
```

### Deploy in produzione (Heroku)

L'app e configurata per il deploy su **Heroku** tramite `Procfile`:

```bash
web: gunicorn app:app
```

**Variabili d'ambiente richieste:**
| Variabile | Descrizione |
|-----------|-------------|
| `DATABASE_URL` | Stringa di connessione PostgreSQL |
| `SECRET_KEY` | Chave segreta per le sessioni |
| `APP_CONFIG` | Impostare a `production` |

**Opzionali:**
| Variabile | Descrizione |
|-----------|-------------|
| `GOOGLE_SITE_VERIFICATION` | Codice di verifica Google Search Console |

---

## Stack tecnologico

| Livello | Tecnologia |
|---------|-----------|
| **Backend** | Python 3, Flask 3.1, Gunicorn 26 |
| **Database** | PostgreSQL (produzione), SQLite (sviluppo) tramite SQLAlchemy 3.1 |
| **Sicurezza** | Flask-Limiter (rate limiting, 200 req/h per IP), Bleach (sanificazione XSS) |
| **Frontend** | Vanilla JavaScript ES6 Modules, CSS3 Custom Properties |
| **Icone** | Sistema SVG inline personalizzato (oltre 60 icone, zero dipendenze esterne) |
| **Font** | Inter (UI) + Playfair Display (accento) tramite Google Fonts |
| **PWA** | Service Worker, Web App Manifest, meta tag iOS |
| **Analytics** | Google Analytics 4 (gtag.js) |
| **Hosting** | Heroku |
| **Compressione** | Flask-Compress (gzip automatico) |
| **SEO** | Sitemap XML dinamici, JSON-LD, Open Graph, Twitter Cards, URL canonici |

---

## Dipendenze

```
Flask==3.1.3              # Framework web
Flask-SQLAlchemy==3.1.1   # ORM per database
Flask-Compress==1.24      # Compressione gzip
Flask-Limiter==4.1.1      # Rate limiting
gunicorn==26.0.0          # Server WSGI per produzione
psycopg2-binary==2.9.12   # Driver PostgreSQL
bleach==6.4.0             # Sanificazione HTML
Jinja2==3.1.6             # Motore template
Werkzeug==3.1.8           # Toolkit WSGI
```

---

## Contribuire

I contributi sono benvenuti! Ecco come puoi aiutare:

1. **Segnalazione bug** — Apri una issue con i passaggi per riprodurre
2. **Richiesta funzionalita** — Suggerisci nuove forme poetiche o funzionalita
3. **Pull request** — Fai un fork del repo e invia una PR
4. **Eccezioni linguistiche** — Aiuta ad espandere il dizionario delle eccezioni sillabiche
5. **Traduzioni** — Aiuta a rendere l'app multilingue
6. **Miglioramenti design** — Raffina UI/UX

### Linee guida per lo sviluppo

- Segui l'architettura modulare esistente (blueprint, servizi, utility)
- Mantieni la retrocompatibilita con le API REST
- Mantieni la lista delle eccezioni dell'analizzatore sillabico curata e documentata
- Assicurati che le misure di prevenzione CLS siano mantenute
- Testa sia su viewport mobile che desktop
- Rispetta gli standard di accessibilita (navigazione da tastiera, screen reader, movimento ridotto)

---

## Licenza

Tutti i diritti riservati.

---

## Riconoscimenti

- Realizzato con passione 
- Ispirato dalle forme poetiche tradizionali **giapponesi** (haiku, tanka) e **italiane** (sonetto, stornello)
- Tutte le poesie appartengono ai rispettivi autori della comunita
- Ogni poeta che condivide i propri versi rende questo progetto significativo

---

<div align="center">

Realizzato con cura da aleloizz

[www.aleshaikus.me](https://www.aleshaikus.me) &middot; [Contatto](mailto:aleloizz.github@gmail.com) &middot; [Segnala bug](https://github.com/aleloizz/Ale-s-Haikus/issues)

*"Nel silenzio dei versi, risuona l'infinito."*</br>
*"詩の静寂の中に、無限が響き渡る"*

</div>
