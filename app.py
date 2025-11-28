"""
Ale's Haikus - Webapp di analisi poetica
Versione modulare per miglior manutenibilità
"""
import os
from flask import Flask, request, render_template, redirect, send_from_directory, url_for, make_response
from datetime import datetime
import os

# Tentativo import Flask-Compress (opzionale per sviluppo)
try:
    from flask_compress import Compress
    COMPRESS_AVAILABLE = True
except ImportError:
    COMPRESS_AVAILABLE = False
    print("Flask-Compress non disponibile - continuando senza compressione")

# Import dei moduli personalizzati
from config.app_config import config
from models.poem import db
from routes.api import api_bp
from routes.web import web_bp
from services.syllable_analyzer import conta_sillabe

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    Limiter = None
    get_remote_address = None
    LIMITER_AVAILABLE = False

def create_app(config_name=None):
    """Factory function per creare l'app Flask"""

    # Determina l'ambiente (preferisci APP_CONFIG se presente)
    if config_name is None:
        config_name = os.environ.get('APP_CONFIG') or os.environ.get('FLASK_ENV') or 'production'
        # Se valore non riconosciuto, NON cadere su dev: usa produzione
        if config_name not in config:
            config_name = 'production'
    
    # Crea l'app con static folder abilitato ma useremo la nostra route per override
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Carica la configurazione
    app.config.from_object(config[config_name])

    # Fail-fast in produzione se manca SECRET_KEY o è evidente un placeholder
    if config_name == 'production':
        sk = app.config.get('SECRET_KEY')
        if not sk or sk.startswith('dev-secret-key'):
            raise RuntimeError('SECRET_KEY non impostata correttamente per ambiente di produzione: definire variabile d\'ambiente SECRET_KEY.')
    
    # Inizializza le estensioni
    db.init_app(app)
    if LIMITER_AVAILABLE:
        # Rate limiting per-IP con storage in memoria (Heroku: 1 dyno -> ok)
        limiter = Limiter(
            get_remote_address,
            app=app,
            default_limits=["200 per hour"],
            storage_uri="memory://",
        )
        print("✅ Rate limiting attivato")
    
    # Inizializza compressione se disponibile
    if COMPRESS_AVAILABLE:
        Compress(app)
        print("✅ Compressione gzip attivata")
    
    # Registra i blueprint
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)
    
    # Crea le tabelle del database
    with app.app_context():
        db.create_all()

    # Expose optional site verification tokens to templates (Bing/DDG via Bing, Google)
    @app.context_processor
    def inject_verification_meta():
        return dict(
            #BING_SITE_VERIFICATION=os.environ.get('BING_SITE_VERIFICATION'),
            GOOGLE_SITE_VERIFICATION=os.environ.get('GOOGLE_SITE_VERIFICATION')
        )

    # Helper per cache-busting basato su mtime del file statico
    @app.context_processor
    def utility_processor():
        def static_file(filename: str) -> str:
            try:
                file_path = os.path.join(app.static_folder, filename)
                mtime = int(os.path.getmtime(file_path))
            except Exception:
                # Fallback: timestamp corrente per evitare hard cache in caso di errori
                mtime = int(datetime.utcnow().timestamp())
            return url_for('static', filename=filename, v=mtime)
        return dict(static_file=static_file)
    
    # Routes specifiche che rimangono nel main
    @app.route('/sitemap.xml')
    def sitemap_index():
        """Sitemap index che punta alle sottositemap statiche e dinamiche.
        Conserva un profilo conservativo e non impatta altre route.
        """
        # Costruisce un sitemapindex minimale con due sotto-sitemaps
        today = datetime.utcnow().date().isoformat()
        base = request.url_root.rstrip('/')
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>{base + url_for('sitemap_static')}</loc>
    <lastmod>{today}</lastmod>
  </sitemap>
  <sitemap>
    <loc>{base + url_for('sitemap_poesie')}</loc>
    <lastmod>{today}</lastmod>
  </sitemap>
</sitemapindex>"""
        resp = make_response(xml)
        resp.headers['Content-Type'] = 'application/xml; charset=utf-8'
        # Cache breve per permettere refresh quotidiano
        resp.headers['Cache-Control'] = 'public, max-age=3600'
        return resp

    @app.route('/sitemap-static.xml')
    def sitemap_static():
        """Sitemap con le pagine principali statiche (landing, analizzatore, bacheca, wiki)."""
        today = datetime.utcnow().date().isoformat()
        # Forza https negli URL assoluti
        def abs_url(endpoint):
            return url_for(endpoint, _external=True, _scheme='https')

        entries = [
            {
                'loc': abs_url('web.index'),
                'lastmod': today,
                'changefreq': 'weekly',
                'priority': '1.0'
            },
            {
                'loc': abs_url('web.analyzer'),
                'lastmod': today,
                'changefreq': 'weekly',
                'priority': '0.8'
            },
            {
                'loc': abs_url('web.bacheca'),
                'lastmod': today,
                'changefreq': 'daily',
                'priority': '0.8'
            },
            {
                'loc': abs_url('web.wiki'),
                'lastmod': today,
                'changefreq': 'weekly',
                'priority': '0.7'
            },
        ]

        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
            '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">'
        ]
        for e in entries:
            parts.append('  <url>')
            parts.append(f"    <loc>{e['loc']}</loc>")
            parts.append(f"    <lastmod>{e['lastmod']}</lastmod>")
            parts.append(f"    <changefreq>{e['changefreq']}</changefreq>")
            parts.append(f"    <priority>{e['priority']}</priority>")
            parts.append('  </url>')
        parts.append('</urlset>')
        xml = "\n".join(parts)

        resp = make_response(xml)
        resp.headers['Content-Type'] = 'application/xml; charset=utf-8'
        resp.headers['Cache-Control'] = 'public, max-age=3600'
        return resp

    @app.route('/sitemap-poesie.xml')
    def sitemap_poesie():
        """Sitemap dinamica per le poesie pubblicate.
        Limita a un massimo ragionevole per non appesantire la risposta.
        """
        # Import locale per evitare cicli e carichi all'avvio
        from models.poem import Poem
        # Limite conservativo (modificabile in futuro)
        LIMIT = 5000
        try:
            poems = Poem.query.order_by(Poem.created_at.desc()).limit(LIMIT).all()
        except Exception as e:
            print(f"Errore caricamento poesie per sitemap: {e}")
            poems = []

        def poem_url(pid: int) -> str:
            return url_for('web.dettaglio_poesia', poesia_id=pid, _external=True, _scheme='https')

        def to_date(dt) -> str:
            try:
                return (dt or datetime.utcnow()).date().isoformat()
            except Exception:
                return datetime.utcnow().date().isoformat()

        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
            '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">'
        ]
        for p in poems:
            parts.append('  <url>')
            parts.append(f"    <loc>{poem_url(p.id)}</loc>")
            parts.append(f"    <lastmod>{to_date(p.created_at)}</lastmod>")
            parts.append("    <changefreq>weekly</changefreq>")
            parts.append("    <priority>0.6</priority>")
            parts.append('  </url>')
        parts.append('</urlset>')
        xml = "\n".join(parts)

        resp = make_response(xml)
        resp.headers['Content-Type'] = 'application/xml; charset=utf-8'
        # Le poesie cambiano con frequenza, mantenere cache breve
        resp.headers['Cache-Control'] = 'public, max-age=1800'
        return resp

    # Service Worker route (served from root scope)
    @app.route('/sw.js')
    def service_worker():
        response = send_from_directory('static', 'sw.js')
        # Ensure no caching so updates roll out
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.mimetype = 'application/javascript'
        return response
    
    # robots.txt dalla root per i crawler
    @app.route('/robots.txt')
    def robots_txt():
        response = send_from_directory('static', 'robots.txt')
        # Cache moderata: 1 giorno
        response.headers['Cache-Control'] = 'public, max-age=86400'
        response.mimetype = 'text/plain'
        return response
    
    # Override della route built-in per static files con cache ottimizzata
    @app.route('/static/<path:filename>')
    def static_files(filename):
        response = send_from_directory(app.static_folder, filename)
        
        # Configurazione cache per diversi tipi di file
        if filename.endswith(('.css', '.js')):
            # CSS e JS: cache per 1 anno con validazione
            response.cache_control.max_age = 31536000  # 1 anno
            response.cache_control.public = True
            response.cache_control.must_revalidate = False
            # Aggiungi ETag per validazione
            response.add_etag()
            # Header espliciti per sovrascrivere proxy
            response.headers['Cache-Control'] = 'public, max-age=31536000'
            response.headers['Expires'] = 'Thu, 01 Dec 2025 16:00:00 GMT'
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.webp', '.ico', '.svg')):
            # Immagini e icone: cache per 1 anno
            response.cache_control.max_age = 31536000  # 1 anno
            response.cache_control.public = True
            response.cache_control.immutable = True
            # Header espliciti
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            response.headers['Expires'] = 'Thu, 01 Dec 2025 16:00:00 GMT'
        elif filename.endswith(('.woff', '.woff2', '.ttf', '.otf')):
            # Font: cache per 1 anno
            response.cache_control.max_age = 31536000  # 1 anno
            response.cache_control.public = True
            response.cache_control.immutable = True
        elif filename.endswith(('.xml', '.txt', '.json')):
            # File di configurazione: cache breve con validazione
            response.cache_control.max_age = 3600  # 1 ora
            response.cache_control.public = True
            response.add_etag()
        else:
            # Altri file: cache media
            response.cache_control.max_age = 86400  # 1 giorno
            response.cache_control.public = True
            
        return response
    
    @app.before_request
    def enforce_https_and_www():
        """Forza HTTPS (solo in produzione reale) evitando loop in test/local."""
        # Evita su test client / strumenti locali e se già HTTPS
        if app.testing:
            return None
        if app.debug:
            return None
        proto = request.headers.get('X-Forwarded-Proto', 'http')
        if proto != 'https':
            # Evita redirect infinito se host è localhost/heroku local
            target = request.url.replace('http://', 'https://', 1)
            if target == request.url:
                return None
            return redirect(target, code=301)
    
    @app.after_request
    def add_security_headers(response):
        """Aggiunge header di sicurezza e cache ottimizzati"""
        # Header di sicurezza
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # FORZA CACHE HEADERS per static files anche se serviti da Heroku
        path = request.path
        if path.startswith('/static/'):
            filename = path.split('/')[-1]
            
            if any(filename.endswith(ext) for ext in ['.css', '.js']):
                # CSS e JS: cache per 1 anno
                response.headers['Cache-Control'] = 'public, max-age=31536000'
                response.headers['Expires'] = 'Thu, 01 Dec 2025 16:00:00 GMT'
            elif any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp', '.ico', '.svg']):
                # Immagini: cache per 1 anno con immutable
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                response.headers['Expires'] = 'Thu, 01 Dec 2025 16:00:00 GMT'
            elif any(filename.endswith(ext) for ext in ['.woff', '.woff2', '.ttf', '.otf']):
                # Font: cache per 1 anno con immutable
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            elif any(filename.endswith(ext) for ext in ['.xml', '.txt', '.json']):
                # Configurazioni: cache breve
                response.headers['Cache-Control'] = 'public, max-age=3600'
            else:
                # Altri static: cache media
                response.headers['Cache-Control'] = 'public, max-age=86400'
        
        # Pagine HTML dinamiche: niente cache per evitare contenuti stantii (bacheca, dettagli, ecc.)
        elif response.content_type and 'text/html' in response.content_type:
            # Disabilita cache per assicurare che azioni come delete siano visibili subito
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    
    # Route legacy per analisi haiku (mantenuta per compatibilità)
    @app.route('/analizza', methods=['POST'])
    def analizza_haiku():
        """Analisi specifica per haiku - route legacy"""
        text = request.form.get("text", "").strip()
        
        if not text:
            return render_template("index.html", haiku="", message="Inserisci del testo!")
        
        versi = [verso.strip() for verso in text.split('\n') if verso.strip()]
        
        if len(versi) != 3:
            return render_template("index.html", haiku=text, 
                                 message="Devi inserire esattamente 3 versi! >:(")
        
        results = []
        for i, verso in enumerate(versi):
            count = conta_sillabe(verso.strip())
            results.append({
                'verse': i+1,
                'syllables': count,
                'target': [5,7,5][i]
            })
        
        errors = [
            f"Il verso {res['verse']} dovrebbe avere {res['target']} sillabe, ne ha {res['syllables']}."
            for res in results if res['syllables'] != res['target']
        ]
        
        message = "Il tuo haiku è perfetto! :3" if not errors else "<br>".join(errors)
        return render_template("index.html", haiku=text, message=message)
    
    return app

# Crea l'istanza dell'app
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
