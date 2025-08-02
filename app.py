"""
Ale's Haikus - Webapp di analisi poetica
Versione modulare per miglior manutenibilità
"""
import os
from flask import Flask, request, render_template, redirect, send_from_directory

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
    
    # Registra i blueprint
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)
    
    # Crea le tabelle del database
    with app.app_context():
        db.create_all()
        
        # Debug: mostra le route registrate
        print("🔍 Route registrate:")
        for rule in app.url_map.iter_rules():
            methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
            print(f"  [{methods}] {rule.rule}")
    
    # Routes specifiche che rimangono nel main
    @app.route('/sitemap.xml')
    def sitemap():
        return send_from_directory('static', 'sitemap.xml')
    
    @app.route('/<path:filename>')
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)
    
    @app.before_request
    def enforce_https_and_www():
        """Forza HTTPS e www in produzione"""
        if not app.debug and request.headers.get('X-Forwarded-Proto') != 'https':
            return redirect(request.url.replace('http://', 'https://'), code=301)
    
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
