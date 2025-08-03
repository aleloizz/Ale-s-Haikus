from config.constants import *

def normalizza_per_rima(parola):
    """Normalizza una parola per l'analisi delle rime"""
    if not parola:
        return ""
    
    parola = parola.lower().strip()
    
    # Rimuovi punteggiatura
    chars_to_remove = '.,!?;:"()-[]{}«»""''…'
    for char in chars_to_remove:
        parola = parola.replace(char, '')
    
    return parola

def estrai_suono_finale(parola):
    """Estrae il suono finale di una parola per l'analisi delle rime"""
    parola_norm = normalizza_per_rima(parola)
    
    if len(parola_norm) < 2:
        return parola_norm
    
    # Per le rime italiane, tipicamente si considera l'accento sulla penultima sillaba
    # Quindi prendiamo dalla penultima vocale alla fine, o dall'ultima se è l'unica
    
    # Trova tutte le vocali
    vocali_pos = []
    for i, char in enumerate(parola_norm):
        if char in VOCALI:
            vocali_pos.append(i)
    
    if not vocali_pos:
        return parola_norm[-2:]  # Fallback
    
    # Se c'è solo una vocale, prendi da lì alla fine
    if len(vocali_pos) == 1:
        return parola_norm[vocali_pos[0]:]
    
    # Se ci sono 2 o più vocali, prendi dalla penultima alla fine
    # Questo cattura la sillaba tonica + eventuale atona finale
    start_pos = vocali_pos[-2]
    return parola_norm[start_pos:]

def analizza_rime(versi):
    """Analizza le rime tra i versi"""
    if not versi or len(versi) < 2:
        return {"schema": "", "rime": []}
    
    # Estrai l'ultima parola significativa di ogni verso
    parole_finali = []
    for verso in versi:
        if not verso.strip():
            parole_finali.append("")
            continue
            
        parole = verso.strip().split()
        if parole:
            parole_finali.append(parole[-1])
        else:
            parole_finali.append("")
    
    # Estrai i suoni finali
    suoni_finali = [estrai_suono_finale(parola) for parola in parole_finali]
    
    # Raggruppa le rime
    gruppi_rime = {}
    schema_lettere = []
    lettera_corrente = 'A'
    
    for i, suono in enumerate(suoni_finali):
        if not suono:
            schema_lettere.append('-')
            continue
            
        # Cerca se questo suono rima con uno precedente
        trovato = False
        for lettera, gruppo_suoni in gruppi_rime.items():
            if any(suoni_rimano(suono, s) for s in gruppo_suoni):
                schema_lettere.append(lettera)
                gruppo_suoni.append(suono)
                trovato = True
                break
        
        if not trovato:
            # Nuovo gruppo di rime
            gruppi_rime[lettera_corrente] = [suono]
            schema_lettere.append(lettera_corrente)
            lettera_corrente = chr(ord(lettera_corrente) + 1)
    
    return {
        "schema": "".join(schema_lettere),
        "rime": gruppi_rime,
        "suoni_finali": suoni_finali
    }

def suoni_rimano(suono1, suono2):
    """Verifica se due suoni rimano"""
    if not suono1 or not suono2:
        return False
    
    # Uguaglianza diretta
    if suono1 == suono2:
        return True
    
    # Per rime vere, devono avere almeno 2 caratteri identici alla fine
    # Ma almeno uno deve essere una vocale per costituire una rima valida
    if len(suono1) >= 2 and len(suono2) >= 2:
        # Confronta gli ultimi 2 caratteri
        finale1 = suono1[-2:]
        finale2 = suono2[-2:]
        
        if finale1 == finale2:
            return True
            
        # Se hanno solo l'ultima lettera uguale, devono essere vocali pure (monosillabi)
        if (len(suono1) == 1 and len(suono2) == 1 and 
            suono1[-1] == suono2[-1] and suono1[-1] in VOCALI):
            return True
    
    return False

def identifica_schema_poetico(schema_rime, num_versi):
    """Identifica il tipo di schema poetico"""
    if not schema_rime:
        return "libero"
    
    schema = schema_rime.upper()
    
    # Schemi specifici per numero di versi
    if num_versi == 3:
        if schema in ['AAA', 'ABA']:
            return "terzina"
    elif num_versi == 4:
        if schema == 'AABB':
            return "quartina (rima baciata)"
        elif schema == 'ABAB':
            return "quartina (rima alternata)"
        elif schema == 'ABBA':
            return "quartina (rima incrociata)"
    elif num_versi == 14:
        if schema.startswith('ABAB'):
            return "sonetto"
    elif num_versi == 5:
        if schema == 'AABBA':
            return "limerick"
    
    return "schema personalizzato"
