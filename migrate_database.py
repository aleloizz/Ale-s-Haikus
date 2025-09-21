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
            
            # Helper per esecuzione compatibile con SQLAlchemy 2.0
            def exec_fetchall(sql: str, params: dict | None = None):
                with db.engine.connect() as conn:
                    result = conn.execute(text(sql), params or {})
                    return result.fetchall()

            def exec_ddl(sql: str, params: dict | None = None):
                # Usa una transazione esplicita per DDL
                with db.engine.begin() as conn:
                    conn.execute(text(sql), params or {})
            
            if is_postgres:
                # Controlla se la tabella esiste
                result = exec_fetchall(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'poems'
                    """
                )
                table_exists = len(result) > 0
                
                if table_exists:
                    print("✅ Tabella 'poems' esistente")
                    
                    # Controlla le colonne esistenti
                    result = exec_fetchall(
                        """
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = 'poems'
                        """
                    )
                    columns = {row[0]: row[1] for row in result}
                    print(f"📋 Colonne attuali: {list(columns.keys())}")
                    
                    # Se la colonna content non esiste ma text sì, rinomina
                    if 'text' in columns and 'content' not in columns:
                        print("🔄 Rinomino colonna 'text' in 'content'...")
                        exec_ddl("ALTER TABLE poems RENAME COLUMN text TO content")
                        print("✅ Colonna rinominata")
                    elif 'content' not in columns:
                        # Se non esiste nemmeno text, aggiungi content
                        print("➕ Aggiunta colonna 'content'...")
                        exec_ddl("ALTER TABLE poems ADD COLUMN content TEXT")
                        print("✅ Colonna 'content' aggiunta")
                    
                    # Aggiungi colonne mancanti
                    if 'verse_count' not in columns:
                        print("➕ Aggiunta colonna 'verse_count'...")
                        exec_ddl("ALTER TABLE poems ADD COLUMN verse_count INTEGER DEFAULT 0")
                    
                    if 'syllable_counts' not in columns:
                        print("➕ Aggiunta colonna 'syllable_counts'...")
                        exec_ddl("ALTER TABLE poems ADD COLUMN syllable_counts VARCHAR(100) DEFAULT ''")
                    
                    if 'rhyme_scheme' not in columns:
                        print("➕ Aggiunta colonna 'rhyme_scheme'...")
                        exec_ddl("ALTER TABLE poems ADD COLUMN rhyme_scheme VARCHAR(50)")
                    
                    if 'poem_type' not in columns:
                        print("➕ Aggiunta colonna 'poem_type'...")
                        exec_ddl("ALTER TABLE poems ADD COLUMN poem_type VARCHAR(50)")
                    
                    if 'created_at' not in columns:
                        print("➕ Aggiunta colonna 'created_at'...")
                        exec_ddl("ALTER TABLE poems ADD COLUMN created_at TIMESTAMP DEFAULT NOW()")
                    
                    if 'is_valid' not in columns:
                        print("➕ Aggiunta colonna 'is_valid'...")
                        exec_ddl("ALTER TABLE poems ADD COLUMN is_valid BOOLEAN DEFAULT FALSE")
                    
                    # Aggiungi colonna likes se mancante
                    if 'likes' not in columns:
                        print("➕ Aggiunta colonna 'likes'...")
                        exec_ddl("ALTER TABLE poems ADD COLUMN likes INTEGER DEFAULT 0")
                        
                else:
                    print("🆕 Creazione nuova tabella 'poems'...")
                    db.create_all()
                    print("✅ Tabella creata")
            else:
                # Per SQLite, ricrea semplicemente la tabella
                print("🔧 Database SQLite - aggiornamento schema...")
                # Per SQLite, verifica ed aggiungi la colonna 'likes' se manca
                try:
                    res = exec_fetchall("PRAGMA table_info(poems);")
                    columns = {row[1] for row in res}
                    print(f"📋 Colonne attuali (SQLite): {columns}")
                    if 'likes' not in columns:
                        print("➕ Aggiunta colonna 'likes' su SQLite...")
                        exec_ddl("ALTER TABLE poems ADD COLUMN likes INTEGER NOT NULL DEFAULT 0")
                except Exception as e_sqlite:
                    print(f"⚠️  Impossibile ispezionare/alterare tabella SQLite: {e_sqlite}")
                
                # Esegui comunque create_all per eventuali nuove tabelle
                db.create_all()
                print("✅ Schema aggiornato")
            
            print("✅ Migrazione completata con successo!")
            
        except Exception as e:
            print(f"❌ Errore durante la migrazione: {e}")
            # Per sicurezza, NON droppare mai automaticamente in produzione.
            # Se vuoi permettere il fallback distruttivo, imposta MIGRATION_ALLOW_DROP=1
            if os.environ.get('MIGRATION_ALLOW_DROP') == '1':
                print("🔄 Tentativo di creazione forzata della tabella (DROP/CREATE abilitato)...")
                try:
                    db.drop_all()
                    db.create_all()
                    print("✅ Tabella ricreata con schema aggiornato")
                except Exception as e2:
                    print(f"❌ Fallimento completo: {e2}")
                    # Ultimo tentativo: creare direttamente la tabella Poem
                    try:
                        Poem.__table__.create(db.engine, checkfirst=True)
                        print("✅ Tabella Poem creata direttamente")
                    except Exception as e3:
                        print(f"❌ Impossibile creare la tabella: {e3}")
            else:
                print("⛔ Fallback distruttivo disabilitato. Nessun drop è stato eseguito.")

if __name__ == "__main__":
    migrate_schema()
