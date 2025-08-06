#!/bin/bash
# Script di deployment per Heroku con fix per database

echo "🚀 Avvio deployment con fix database..."

# 1. Deploy del codice
git add .
git commit -m "Fix: Correzione problemi database e routing per Heroku

- Fix routing URLs da 'home' a 'web.index' nei template
- Aggiunto template 500.html mancante  
- Script di migrazione database per allineare schema
- Implementato sistema di tolleranza opzionale
- Migliorata gestione errori bacheca"

git push heroku main

# 2. Esegui migrazione database
echo "🔧 Esecuzione migrazione database..."
heroku run python migrate_database.py

# 3. Restart dell'app per sicurezza
echo "🔄 Restart applicazione..."
heroku ps:restart

echo "✅ Deployment completato!"
echo "🌐 App disponibile su: https://www.aleshaikus.me"
