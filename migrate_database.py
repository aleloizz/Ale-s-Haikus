#!/usr/bin/env python3
"""
Script di migrazione per allineare lo schema del database
Può essere eseguito su Heroku con: heroku run python migrate_database.py
"""
import os
from flask import Flask
from sqlalchemy import text
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

def migrate_schema():
    """Migra lo schema del database"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Avvio migrazione database...")
            
            # Prima verifica se siamo su PostgreSQL o SQLite
            is_postgres = 'postgresql://' in app.config['SQLALCHEMY_DATABASE_URI']
            
            if is_postgres:
                # Controlla se la tabella esiste
                result = db.engine.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'poems'
                """))
                
                table_exists = len(list(result)) > 0
                
                if table_exists:
                    print("✅ Tabella 'poems' esistente")
                    
                    # Controlla le colonne esistenti
                    result = db.engine.execute(text("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = 'poems'
                    """))
                    
                    columns = {row[0]: row[1] for row in result}
                    print(f"📋 Colonne attuali: {list(columns.keys())}")
                    
                    # Se la colonna content non esiste ma text sì, rinomina
                    if 'text' in columns and 'content' not in columns:
                        print("🔄 Rinomino colonna 'text' in 'content'...")
                        db.engine.execute(text("ALTER TABLE poems RENAME COLUMN text TO content"))
                        print("✅ Colonna rinominata")
                    elif 'content' not in columns:
                        # Se non esiste nemmeno text, aggiungi content
                        print("➕ Aggiunta colonna 'content'...")
                        db.engine.execute(text("ALTER TABLE poems ADD COLUMN content TEXT"))
                        print("✅ Colonna 'content' aggiunta")
                    
                    # Aggiungi colonne mancanti
                    if 'verse_count' not in columns:
                        print("➕ Aggiunta colonna 'verse_count'...")
                        db.engine.execute(text("ALTER TABLE poems ADD COLUMN verse_count INTEGER DEFAULT 0"))
                    
                    if 'syllable_counts' not in columns:
                        print("➕ Aggiunta colonna 'syllable_counts'...")
                        db.engine.execute(text("ALTER TABLE poems ADD COLUMN syllable_counts VARCHAR(100) DEFAULT ''"))
                    
                    if 'rhyme_scheme' not in columns:
                        print("➕ Aggiunta colonna 'rhyme_scheme'...")
                        db.engine.execute(text("ALTER TABLE poems ADD COLUMN rhyme_scheme VARCHAR(50)"))
                    
                    if 'poem_type' not in columns:
                        print("➕ Aggiunta colonna 'poem_type'...")
                        db.engine.execute(text("ALTER TABLE poems ADD COLUMN poem_type VARCHAR(50)"))
                    
                    if 'created_at' not in columns:
                        print("➕ Aggiunta colonna 'created_at'...")
                        db.engine.execute(text("ALTER TABLE poems ADD COLUMN created_at TIMESTAMP DEFAULT NOW()"))
                    
                    if 'is_valid' not in columns:
                        print("➕ Aggiunta colonna 'is_valid'...")
                        db.engine.execute(text("ALTER TABLE poems ADD COLUMN is_valid BOOLEAN DEFAULT FALSE"))
                        
                else:
                    print("🆕 Creazione nuova tabella 'poems'...")
                    db.create_all()
                    print("✅ Tabella creata")
            else:
                # Per SQLite, ricrea semplicemente la tabella
                print("🔧 Database SQLite - ricreazione schema...")
                db.create_all()
                print("✅ Schema aggiornato")
            
            print("✅ Migrazione completata con successo!")
            
        except Exception as e:
            print(f"❌ Errore durante la migrazione: {e}")
            print("🔄 Tentativo di creazione forzata della tabella...")
            try:
                # Drop e ricrea la tabella se tutto il resto fallisce
                db.drop_all()
                db.create_all()
                print("✅ Tabella ricreata con schema aggiornato")
            except Exception as e2:
                print(f"❌ Fallimento completo: {e2}")
                # Come ultima risorsa, prova a creare solo la tabella
                try:
                    from models.poem import Poem
                    Poem.__table__.create(db.engine, checkfirst=True)
                    print("✅ Tabella Poem creata direttamente")
                except Exception as e3:
                    print(f"❌ Impossibile creare la tabella: {e3}")

if __name__ == "__main__":
    migrate_schema()
