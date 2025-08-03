from services.syllable_analyzer import conta_sillabe
from services.rhyme_analyzer import analizza_rime, identifica_schema_poetico
from config.constants import SCHEMI_POESIA

def analizza_poesia_completa(testo):
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
    tipo_riconosciuto = identifica_tipo_poesia(len(versi), sillabe_per_verso, schema_rime)
    
    # Verifica se rispetta la metrica
    rispetta_metrica = verifica_metrica(tipo_riconosciuto, len(versi), sillabe_per_verso, schema_rime)
    
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

def identifica_tipo_poesia(num_versi, sillabe_per_verso, schema_rime):
    """Identifica il tipo di poesia basandosi su versi, sillabe e rime"""
    
    # Haiku: 3 versi, schema 5-7-5 sillabe
    if num_versi == 3 and len(sillabe_per_verso) == 3:
        if sillabe_per_verso == [5, 7, 5]:
            return 'haiku'
    
    # Tanka: 5 versi, schema 5-7-5-7-7 sillabe
    if num_versi == 5 and len(sillabe_per_verso) == 5:
        if sillabe_per_verso == [5, 7, 5, 7, 7]:
            return 'tanka'
    
    # Limerick: 5 versi, schema AABBA
    if num_versi == 5 and schema_rime == 'AABBA':
        return 'limerick'
    
    # Quartina - solo se rispetta la metrica standard
    if num_versi == 4:
        # Controlla se ha le sillabe standard (11-11-11-11)
        if all(s == 11 for s in sillabe_per_verso):
            if schema_rime == 'AABB':
                return 'quartina (rima baciata)'
            elif schema_rime == 'ABAB':
                return 'quartina (rima alternata)'
            elif schema_rime == 'ABBA':
                return 'quartina (rima incrociata)'
            else:
                return 'quartina'
        else:
            # Se non rispetta la metrica standard, è verso libero
            return 'verso libero'
    
    # Terzina - solo se rispetta la metrica standard
    if num_versi == 3:
        # Controlla se ha le sillabe standard (11-11-11)
        if all(s == 11 for s in sillabe_per_verso):
            if schema_rime == 'AAA':
                return 'terzina (rima continua)'
            elif schema_rime == 'ABA':
                return 'terzina_dantesca'
            else:
                return 'terzina_dantesca'  # Usa lo schema dantesco come default per terzine
        else:
            # Se non rispetta la metrica standard, è verso libero
            return 'verso libero'
    
    # Sonetto: 14 versi con schema specifico e sillabe 11
    if num_versi == 14:
        if all(s == 11 for s in sillabe_per_verso) and (schema_rime.startswith('ABAB') or schema_rime.startswith('ABBA')):
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
    
    return 'verso libero'

def verifica_metrica(tipo_poesia, num_versi, sillabe_per_verso, schema_rime):
    """Verifica se la poesia rispetta la metrica del tipo identificato"""
    
    if tipo_poesia not in SCHEMI_POESIA:
        return False  # Tipo non riconosciuto o verso libero
    
    schema = SCHEMI_POESIA[tipo_poesia]
    
    # Verifica sillabe per verso (se specificato)
    if 'sillabe' in schema and schema['sillabe']:
        # Il numero di versi deve corrispondere alla lunghezza dello schema sillabe
        if len(sillabe_per_verso) != len(schema['sillabe']):
            return False
        for i, sillabe_attese in enumerate(schema['sillabe']):
            if sillabe_per_verso[i] != sillabe_attese:
                return False
    
    # Verifica schema rime (se specificato)
    if 'rima' in schema and schema['rima']:
        if schema_rime != ''.join(schema['rima']):
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
