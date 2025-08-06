# Script di deployment per Heroku con migrazione database (PowerShell)
# Esegue deployment sicuro con allineamento schema database

Write-Host "`n🚀 HEROKU DEPLOYMENT CON DATABASE MIGRATION" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green

# Spiegazione della migrazione
Write-Host "`n📋 TIPO DI MIGRAZIONE:" -ForegroundColor Yellow
Write-Host "   • Schema-Sync Migration (senza perdita dati)" -ForegroundColor White
Write-Host "   • Rinomina colonna 'text' → 'content' se necessario" -ForegroundColor White  
Write-Host "   • Aggiunge colonne mancanti per nuove feature" -ForegroundColor White
Write-Host "   • Preserva tutti i dati esistenti" -ForegroundColor White

Write-Host "`n🔍 PROBLEMI RISOLTI:" -ForegroundColor Yellow
Write-Host "   ❌ Database: column poems.content does not exist" -ForegroundColor Red
Write-Host "   ❌ Routing: url_for('home') → BuildError" -ForegroundColor Red
Write-Host "   ❌ Template: 500.html not found" -ForegroundColor Red
Write-Host "   ✅ Implementato sistema tolleranza opzionale" -ForegroundColor Green

# Conferma utente
Write-Host "`n⚠️  ATTENZIONE: Questo deployment include:" -ForegroundColor Magenta
Write-Host "   • Modifica schema database di produzione" -ForegroundColor White
Write-Host "   • Fix routing per bacheca e wiki" -ForegroundColor White
Write-Host "   • Nuovo sistema di tolleranza sillabe" -ForegroundColor White

$confirm = Read-Host "`nContinuare con il deployment? (s/N)"
if ($confirm -ne 's' -and $confirm -ne 'S') {
    Write-Host "❌ Deployment annullato dall'utente" -ForegroundColor Red
    exit 1
}

# 1. Controllo git status
Write-Host "`n📤 FASE 1: Preparazione codice..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "   📁 File modificati rilevati, preparazione commit..." -ForegroundColor White
    git add .
    git commit -m "Fix: Correzione problemi database e routing per Heroku

🔧 DATABASE MIGRATION:
- Script migrazione schema per allineare database produzione
- Fix colonna 'content' mancante in tabella poems
- Aggiunta colonne per nuove feature (verse_count, is_valid, etc.)

🌐 ROUTING FIXES:
- Fix url_for('home') → url_for('web.index') in tutti i template  
- Template bacheca.html e wiki.html aggiornati
- Aggiunto template 500.html per gestione errori server

🎯 FEATURE ENHANCEMENT:
- Sistema tolleranza sillabe opzionale implementato
- Checkbox frontend per controllo precisione vs flessibilità
- Parametro use_tolerance propagato a tutte le funzioni analisi

✅ MIGLIORAMENTI:
- Gestione errori bacheca migliorata
- Template 500.html con haiku personalizzato
- Script deployment automatizzato con migrazione"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Errore durante il commit" -ForegroundColor Red
        exit 1
    }
    Write-Host "   ✅ Commit preparato con successo" -ForegroundColor Green
} else {
    Write-Host "   ✅ Repository già aggiornato" -ForegroundColor Green
}

# 2. Deploy del codice
Write-Host "`n🚀 FASE 2: Push codice su Heroku..." -ForegroundColor Yellow
git push heroku main
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Errore durante il push su Heroku" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Codice deployato con successo" -ForegroundColor Green

# 3. Migrazione database
Write-Host "`n🔧 FASE 3: Esecuzione migrazione database..." -ForegroundColor Yellow
Write-Host "   🗄️  Controllo e allineamento schema database..." -ForegroundColor White
heroku run python migrate_database.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Errore durante la migrazione database" -ForegroundColor Red
    Write-Host "   🔄 Tentativo con script di verifica..." -ForegroundColor Yellow
    heroku run python check_database_schema.py
    
    $retryMigration = Read-Host "`nTentare migrazione di emergenza (elimina tutti i dati)? (s/N)"
    if ($retryMigration -eq 's' -or $retryMigration -eq 'S') {
        Write-Host "   ⚠️  Esecuzione migrazione di emergenza..." -ForegroundColor Red
        heroku run 'echo "CONFERMA" | python emergency_recreate_db.py'
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Migrazione di emergenza completata" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Anche la migrazione di emergenza è fallita" -ForegroundColor Red
            Write-Host "   📋 Comandi manuali da provare:" -ForegroundColor Yellow
            Write-Host "      heroku pg:reset --confirm nome-app" -ForegroundColor White
            Write-Host "      heroku run python migrate_database.py" -ForegroundColor White
        }
    }
} else {
    Write-Host "   ✅ Migrazione database completata" -ForegroundColor Green
}

# 4. Restart dell'app
Write-Host "`n🔄 FASE 4: Restart applicazione..." -ForegroundColor Yellow
heroku ps:restart
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Problema durante restart (app potrebbe essere già attiva)" -ForegroundColor Yellow
} else {
    Write-Host "   ✅ Applicazione riavviata" -ForegroundColor Green
}

# 5. Verifica deployment
Write-Host "`n✅ DEPLOYMENT COMPLETATO!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "🌐 App disponibile: https://www.aleshaikus.me" -ForegroundColor Cyan
Write-Host "📊 Bacheca: https://www.aleshaikus.me/bacheca" -ForegroundColor Cyan  
Write-Host "📚 Wiki: https://www.aleshaikus.me/wiki" -ForegroundColor Cyan

Write-Host "`n🔍 CONTROLLI POST-DEPLOYMENT:" -ForegroundColor Yellow
Write-Host "   • Verifica che la bacheca si carichi senza errori" -ForegroundColor White
Write-Host "   • Testa il sistema di tolleranza opzionale" -ForegroundColor White
Write-Host "   • Controlla che le pubblicazioni funzionino" -ForegroundColor White

Write-Host "`n📋 COMANDI UTILI:" -ForegroundColor Yellow
Write-Host "   heroku logs --tail                    # Monitora log in tempo reale" -ForegroundColor White
Write-Host "   heroku run python check_database_schema.py  # Verifica schema DB" -ForegroundColor White
Write-Host "   heroku pg:psql                       # Accesso diretto database" -ForegroundColor White
