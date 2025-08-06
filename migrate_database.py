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
                
                # Se mancano colonne, aggiungile
                expected_columns = {
                    'id': 'integer',
                    'title': 'varchar',
                    'content': 'text',
                    'author': 'varchar',
                    'verse_count': 'integer',
                    'syllable_counts': 'varchar',
                    'rhyme_scheme': 'varchar',
                    'poem_type': 'varchar',
                    'created_at': 'timestamp',
                    'is_valid': 'boolean'
                }
                
                for col_name, col_type in expected_columns.items():
                    if col_name not in columns:
                        print(f"➕ Aggiunto colonna mancante: {col_name}")
                        # Le specifiche SQL per aggiungere colonne variano, useremo un approccio sicuro
                        if col_name == 'verse_count':
                            db.engine.execute(text("ALTER TABLE poems ADD COLUMN verse_count INTEGER DEFAULT 0"))
                        elif col_name == 'syllable_counts':
                            db.engine.execute(text("ALTER TABLE poems ADD COLUMN syllable_counts VARCHAR(100) DEFAULT ''"))
                        elif col_name == 'rhyme_scheme':
                            db.engine.execute(text("ALTER TABLE poems ADD COLUMN rhyme_scheme VARCHAR(50)"))
                        elif col_name == 'poem_type':
                            db.engine.execute(text("ALTER TABLE poems ADD COLUMN poem_type VARCHAR(50)"))
                        elif col_name == 'created_at':
                            db.engine.execute(text("ALTER TABLE poems ADD COLUMN created_at TIMESTAMP DEFAULT NOW()"))
                        elif col_name == 'is_valid':
                            db.engine.execute(text("ALTER TABLE poems ADD COLUMN is_valid BOOLEAN DEFAULT FALSE"))
                            
            else:
                print("🆕 Creazione nuova tabella 'poems'...")
                db.create_all()
                print("✅ Tabella creata")
            
            print("✅ Migrazione completata con successo!")
            
        except Exception as e:
            print(f"❌ Errore durante la migrazione: {e}")
            print("🔄 Tentativo di creazione forzata della tabella...")
            try:
                db.create_all()
                print("✅ Tabella creata con schema aggiornato")
            except Exception as e2:
                print(f"❌ Fallimento completo: {e2}")

if __name__ == "__main__":
    migrate_schema()
