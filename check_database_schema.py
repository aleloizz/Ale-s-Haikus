#!/usr/bin/env python3
"""
Script per verificare e allineare lo schema del database
"""
import os
from flask import Flask
from models.poem import db, Poem
from sqlalchemy import inspect

app = Flask(__name__)

# Configura l'app per production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/poems.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inizializza il database
db.init_app(app)

def check_schema():
    """Controlla lo schema del database"""
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("=== VERIFICA SCHEMA DATABASE ===")
        
        # Controlla se la tabella poems exists
        if 'poems' in inspector.get_table_names():
            print("✅ Tabella 'poems' trovata")
            
            # Controlla le colonne
            columns = inspector.get_columns('poems')
            print(f"\n📋 Colonne presenti ({len(columns)}):")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
                
            # Controlla se esiste la colonna content
            column_names = [col['name'] for col in columns]
            if 'content' in column_names:
                print("✅ Colonna 'content' trovata")
            else:
                print("❌ Colonna 'content' NON trovata")
                if 'text' in column_names:
                    print("⚠️  Trovata colonna 'text' invece di 'content'")

            # Conteggio righe e sample
            try:
                total = db.session.query(Poem).count()
                print(f"\n📦 Totale poesie: {total}")
                if total > 0:
                    print("🧾 Esempi (max 5):")
                    samples = db.session.query(Poem).order_by(Poem.created_at.desc()).limit(5).all()
                    for p in samples:
                        created = p.created_at.isoformat() if p.created_at else 'n/a'
                        print(f"  - id={p.id} | titolo='{p.title}' | autore='{p.author}' | created_at={created}")
            except Exception as e:
                print(f"⚠️  Impossibile leggere i dati: {e}")
                    
        else:
            print("❌ Tabella 'poems' NON trovata")
            print("🔧 Creazione tabella...")
            db.create_all()
            print("✅ Tabella creata")

def fix_schema():
    """Tenta di correggere lo schema se necessario"""
    with app.app_context():
        try:
            # Prova a creare le tabelle se non esistono
            db.create_all()
            print("✅ Schema verificato/creato")
        except Exception as e:
            print(f"❌ Errore durante la creazione dello schema: {e}")

if __name__ == "__main__":
    check_schema()
    print("\n" + "="*50)
    fix_schema()
