from services.syllable_analyzer import conta_sillabe
from services.rhyme_analyzer import analizza_rime, identifica_schema_poetico
from config.constants import SCHEMI_POESIA

def analizza_poesia_completa(testo, use_tolerance=False):
    """Analisi completa di una poesia"""
    if not testo or not testo.strip():
        return {
            'errore': 'Testo non fornito o vuoto',
            'num_versi': 0,
            'sillabe_per_verso': [],
            'sillabe_totali': 0,
            'schema_rime': '',
            'tipo_riconosciuto': 'sconosciuto',
            'rispetta_metrica': False
        }
    
    # Dividi in versi
    versi = [verso.strip() for verso in testo.strip().split('\n') if verso.strip()]
    
    if not versi:
        return {
            'errore': 'Nessun verso trovato',
            'num_versi': 0,
            'sillabe_per_verso': [],
            'sillabe_totali': 0,
            'schema_rime': '',
            'tipo_riconosciuto': 'sconosciuto',
            'rispetta_metrica': False
        }
    
    # Conta sillabe per ogni verso
    sillabe_per_verso = []
    for verso in versi:
        sillabe = conta_sillabe(verso)
        sillabe_per_verso.append(sillabe)
    
    # Analizza le rime
    analisi_rime = analizza_rime(versi)
    schema_rime = analisi_rime['schema']
    
    # Identifica il tipo di poesia
    tipo_riconosciuto = identifica_tipo_poesia(len(versi), sillabe_per_verso, schema_rime, use_tolerance)
    
    # Verifica se rispetta la metrica
    rispetta_metrica = verifica_metrica(tipo_riconosciuto, len(versi), sillabe_per_verso, schema_rime, use_tolerance)
    
    return {
        'num_versi': len(versi),
        'versi': versi,
        'sillabe_per_verso': sillabe_per_verso,
        'sillabe_totali': sum(sillabe_per_verso),
        'schema_rime': schema_rime,
        'analisi_rime': analisi_rime,
        'tipo_riconosciuto': tipo_riconosciuto,
        'rispetta_metrica': rispetta_metrica,
        'dettagli_metrica': get_dettagli_metrica(tipo_riconosciuto)
    }

def identifica_tipo_poesia(num_versi, sillabe_per_verso, schema_rime, use_tolerance=False):
    """Identifica il tipo di poesia basandosi su versi, sillabe e rime"""
    
    # Haiku: 3 versi, schema 5-7-5 sillabe (tolleranza ±1 se abilitata)
    if num_versi == 3 and len(sillabe_per_verso) == 3:
        tolerance = 1 if use_tolerance else 0
        if (abs(sillabe_per_verso[0] - 5) <= tolerance and 
            abs(sillabe_per_verso[1] - 7) <= tolerance and 
            abs(sillabe_per_verso[2] - 5) <= tolerance):
            return 'haiku'
    
    # Tanka: 5 versi, schema 5-7-5-7-7 sillabe (tolleranza ±1 se abilitata)
    if num_versi == 5 and len(sillabe_per_verso) == 5:
        target = [5, 7, 5, 7, 7]
        tolerance = 1 if use_tolerance else 0
        if all(abs(sillabe_per_verso[i] - target[i]) <= tolerance for i in range(5)):
            return 'tanka'
    
    # Limerick: 5 versi, schema AABBA
    if num_versi == 5 and schema_rime == 'AABBA':
        return 'limerick'
    
    # Quartina - riconosce anche con tolleranza sulle sillabe se abilitata
    if num_versi == 4:
        # Controlla se ha sillabe simili agli endecasillabi (tolleranza opzionale)
        tolerance = 2 if use_tolerance else 0
        if all(abs(s - 11) <= tolerance for s in sillabe_per_verso):
            if schema_rime == 'AABB':
                return 'quartina'  # Usa il tipo base per compatibilità
            elif schema_rime == 'ABAB':
                return 'quartina'  # Usa il tipo base per compatibilità
            elif schema_rime == 'ABBA':
                return 'quartina'  # Usa il tipo base per compatibilità
            else:
                return 'quartina'  # Comunque una quartina
        else:
            # Se le sillabe sono molto diverse, potrebbe essere verso libero
            return 'versi_liberi'  # Usa nome compatibile con SCHEMI_POESIA
    
    # Terzina - riconosce anche con tolleranza sulle sillabe se abilitata
    if num_versi == 3:
        # Controlla se ha sillabe simili agli endecasillabi (tolleranza opzionale)
        tolerance = 2 if use_tolerance else 0
        if all(abs(s - 11) <= tolerance for s in sillabe_per_verso):
            return 'terzina_dantesca'  # Usa nome compatibile
        else:
            return 'versi_liberi'  # Usa nome compatibile con SCHEMI_POESIA
    
    # Sonetto: 14 versi con schema specifico e sillabe simili a 11 (tolleranza opzionale)
    if num_versi == 14:
        tolerance = 2 if use_tolerance else 0
        if all(abs(s - 11) <= tolerance for s in sillabe_per_verso) and (schema_rime.startswith('ABAB') or schema_rime.startswith('ABBA')):
            return 'sonetto'
    
    # Distici
    if num_versi == 2:
        if schema_rime == 'AA':
            return 'distico (rima baciata)'
        else:
            return 'distico'
    
    # Altre forme
    if num_versi == 6:
        return 'sestina'
    elif num_versi == 8:
        return 'ottava'
    elif num_versi == 1:
        return 'monostico'
    
    return 'versi_liberi'  # Usa nome compatibile con SCHEMI_POESIA

def verifica_metrica(tipo_poesia, num_versi, sillabe_per_verso, schema_rime, use_tolerance=False):
    """Verifica se la poesia rispetta la metrica del tipo identificato"""
    
    # Per i versi liberi, sempre valido
    if tipo_poesia in ['verso libero', 'versi_liberi']:
        return True
    
    if tipo_poesia not in SCHEMI_POESIA:
        # Se il tipo non è negli schemi, ma è una variante riconosciuta, cerca il tipo base
        tipo_base = None
        if 'quartina' in tipo_poesia:
            tipo_base = 'quartina'
        elif 'terzina' in tipo_poesia:
            tipo_base = 'terzina_dantesca'
        elif 'distico' in tipo_poesia:
            return True  # I distici sono sempre validi
        
        if tipo_base and tipo_base in SCHEMI_POESIA:
            tipo_poesia = tipo_base
        else:
            return False  # Tipo non riconosciuto
    
    schema = SCHEMI_POESIA[tipo_poesia]
    
    # Verifica sillabe per verso (se specificato) - con tolleranza opzionale
    if 'sillabe' in schema and schema['sillabe']:
        # Il numero di versi deve corrispondere alla lunghezza dello schema sillabe
        if len(sillabe_per_verso) != len(schema['sillabe']):
            return False
        
        # Applica tolleranza solo se richiesta dall'utente
        for i, sillabe_attese in enumerate(schema['sillabe']):
            sillabe_effettive = sillabe_per_verso[i]
            if use_tolerance:
                # Con tolleranza: ±1 sillaba per haiku/tanka, ±2 per forme complesse
                if tipo_poesia in ['haiku', 'tanka', 'katauta', 'choka', 'sedoka']:
                    tolleranza = 1
                else:
                    tolleranza = 2
                    
                if abs(sillabe_effettive - sillabe_attese) > tolleranza:
                    return False
            else:
                # Senza tolleranza: precisione assoluta
                if sillabe_effettive != sillabe_attese:
                    return False
    
    # Verifica schema rime (se specificato) - più flessibile
    if 'rima' in schema and schema['rima']:
        schema_atteso = ''.join(schema['rima'])
        if schema_rime != schema_atteso:
            # Per alcuni tipi, accetta varianti comuni
            if tipo_poesia == 'quartina':
                # Accetta ABAB, AABB, ABBA per quartine
                if schema_rime not in ['ABAB', 'AABB', 'ABBA']:
                    return False
            else:
                return False
    
    return True

def get_dettagli_metrica(tipo_poesia):
    """Restituisce i dettagli della metrica per un tipo di poesia"""
    if tipo_poesia not in SCHEMI_POESIA:
        return {
            'descrizione': 'Schema non definito o verso libero',
            'versi': None,
            'sillabe': None,
            'rime': None
        }
    
    schema = SCHEMI_POESIA[tipo_poesia]
    num_versi = len(schema.get('sillabe', [])) if schema.get('sillabe') else None
    
    return {
        'descrizione': schema.get('descrizione', f'Schema per {tipo_poesia}'),
        'versi': num_versi,
        'sillabe': schema.get('sillabe'),
        'rime': schema.get('rima')
    }
