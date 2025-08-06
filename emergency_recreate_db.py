#!/usr/bin/env python3
"""
Script di emergenza per ricreare completamente il database
ATTENZIONE: Questo script elimina tutti i dati esistenti!
Usare solo se la migrazione normale fallisce.
"""
import os
from flask import Flask
from models.poem import db, Poem

def create_app():
    """Crea l'app Flask per la migrazione"""
    app = Flask(__name__)
    
    # Configura il database
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///instance/poems.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def emergency_recreate():
    """Ricrea completamente il database (PERDE TUTTI I DATI!)"""
    app = create_app()
    
    with app.app_context():
        try:
            print("⚠️  EMERGENZA: Ricreazione completa database...")
            print("🗑️  ATTENZIONE: Tutti i dati esistenti verranno eliminati!")
            
            # Elimina tutte le tabelle
            db.drop_all()
            print("✅ Tabelle eliminate")
            
            # Ricrea tutte le tabelle
            db.create_all()
            print("✅ Tabelle ricreate con schema aggiornato")
            
            # Verifica che la tabella sia stata creata correttamente
            inspector = db.inspect(db.engine)
            if 'poems' in inspector.get_table_names():
                columns = inspector.get_columns('poems')
                print(f"📋 Nuove colonne create: {[col['name'] for col in columns]}")
                print("✅ Ricreazione emergency completata!")
            else:
                print("❌ Errore: Tabella poems non creata")
                
        except Exception as e:
            print(f"❌ Errore durante la ricreazione emergency: {e}")

if __name__ == "__main__":
    print("⚠️  SCRIPT DI EMERGENZA - RICREAZIONE DATABASE")
    print("=" * 50)
    print("Questo script eliminerà TUTTI i dati esistenti nel database!")
    print("Usare solo se:")
    print("- La migrazione normale è fallita")
    print("- Il database è corrotto")
    print("- È accettabile perdere i dati esistenti")
    print("=" * 50)
    
    confirm = input("Digitare 'CONFERMA' per procedere: ")
    if confirm == 'CONFERMA':
        emergency_recreate()
    else:
        print("❌ Operazione annullata")
