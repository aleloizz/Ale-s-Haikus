from config.constants import *
from utils.text_processing import *

def conta_sillabe(testo):
    """Funzione principale per contare le sillabe"""
    if not testo or not testo.strip():
        return 0
    
    testo_pulito_temp = pulisci_testo(testo)
    if ' ' not in testo_pulito_temp and testo_pulito_temp.lower() in ECCEZIONI:
        return ECCEZIONI[testo_pulito_temp.lower()]
    
    return conta_sillabe_parola_composta(testo)

def conta_sillabe_parola_composta(testo):
    """Conta le sillabe di un testo con più parole"""
    testo_pulito = pulisci_testo(testo)
    parole = testo_pulito.split()
    
    sillabe_totali = 0
    
    for parola in parole:
        if not parola.strip():
            continue
            
        parti_parola = gestisci_apostrofi(parola)
        
        for parte in parti_parola:
            parte = parte.strip()
            if parte:
                sillabe_totali += conta_sillabe_singola(parte)
    
    return sillabe_totali

def conta_sillabe_singola(parola):
    """Conta le sillabe di una singola parola - PRIORITÀ ASSOLUTA alle eccezioni"""
    if not parola or not parola.strip():
        return 0
        
    parola_clean = parola.strip().lower()
    
    # Controlla nelle eccezioni PRIMA di tutto
    if parola_clean in ECCEZIONI:
        return ECCEZIONI[parola_clean]
    
    return conta_sillabe_algoritmo(parola_clean)

def conta_sillabe_algoritmo(parola):
    """Algoritmo di conteggio sillabe con gestione prefissi"""
    if not parola:
        return 0
    
    parola_processed = gestisci_prefissi_vocalici(parola)
        
    count = 0
    i = 0
    n = len(parola_processed)
    
    while i < n:
        if i + 2 < n and parola_processed[i:i+3] in TRIGRAMMI:
            i += 3
        elif i + 1 < n and parola_processed[i:i+2] in DIGRAMMI:
            i += 2
        elif i < n and is_vocale(parola_processed[i]):
            count += 1
            if i + 2 < n and is_trittongo(parola_processed[i], parola_processed[i+1], parola_processed[i+2]):
                i += 3
            elif i + 1 < n and is_dittongo(parola_processed[i], parola_processed[i+1]):
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    return max(1, count)

def is_dittongo(c1, c2):
    """Verifica se due caratteri formano un dittongo"""
    if c1 == '|' or c2 == '|':
        return False
        
    combo = f"{c1.lower()}{c2.lower()}"
    return combo in DITTONGHI and not is_iato(c1, c2)

def is_trittongo(c1, c2, c3):
    """Verifica se tre caratteri formano un trittongo"""
    if c1 == '|' or c2 == '|' or c3 == '|':
        return False
        
    combo = f"{c1.lower()}{c2.lower()}{c3.lower()}"
    return combo in TRITTONGHI or (
        c1.lower() in 'iìuù' and 
        is_vocale(c2) and 
        c3.lower() in 'iìuù'
    )

def is_digramma(c1, c2):
    """Controlla se due caratteri formano un digramma"""
    return (c1 == 'g' and c2 == 'n') or (c1 == 's' and c2 == 'c')

def is_trigramma(c1, c2, c3):
    """Controlla se tre caratteri formano un trigramma"""
    return (c1 == 's' and c2 == 'c' and c3 == 'i')
