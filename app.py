"""
Ale's Haikus - Webapp di analisi poetica
Versione modulare per miglior manutenibilità
"""
import os
from flask import Flask, request, render_template, redirect, send_from_directory

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

def create_app(config_name=None):
    """Factory function per creare l'app Flask"""
    
    # Determina l'ambiente
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
        if config_name not in config:
            config_name = 'default'
    
    # Crea l'app
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Carica la configurazione
    app.config.from_object(config[config_name])
    
    # Inizializza le estensioni
    db.init_app(app)
    
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
    
    # Routes specifiche che rimangono nel main
    @app.route('/sitemap.xml')
    def sitemap():
        return send_from_directory('static', 'sitemap.xml')
    
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
        """Forza HTTPS e www in produzione"""
        if not app.debug and request.headers.get('X-Forwarded-Proto') != 'https':
            return redirect(request.url.replace('http://', 'https://'), code=301)
    
    @app.after_request
    def add_security_headers(response):
        """Aggiunge header di sicurezza e cache ottimizzati"""
        # Header di sicurezza
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Cache per pagine HTML: validazione con ETag ma cache breve
        if response.content_type and 'text/html' in response.content_type:
            response.cache_control.max_age = 300  # 5 minuti
            response.cache_control.public = True
            response.add_etag()
        
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
