import string
from config.constants import VOCALI, VOCALI_FORTI, VOCALI_DEBOLI, PREFISSI_COMUNI

def pulisci_testo(testo):
    """Pulisce il testo mantenendo apostrofi e caratteri essenziali"""
    caratteri_da_mantenere = string.ascii_letters + "àèéìíîòóùú' "
    testo_pulito = ''.join(c if c in caratteri_da_mantenere else ' ' for c in testo.lower())
    return ' '.join(testo_pulito.split())

def gestisci_apostrofi(parola):
    """Gestisce parole con apostrofi dividendole correttamente"""
    if "'" not in parola:
        return [parola]
    
    contrazioni = {
        "dell'": ("del", "l'"),
        "nell'": ("nel", "l'"),
        "all'": ("al", "l'"),
        "dall'": ("dal", "l'"),
        "sull'": ("sul", "l'"),
        "coll'": ("col", "l'"),
        "quell'": ("quel", "l'"),
        "quest'": ("quest", ""),
        "sant'": ("sant", ""),
        "un'": ("un", ""),
        "l'": ("", "l'")
    }
    
    parola_lower = parola.lower()
    
    for contrazione, (prima, dopo) in contrazioni.items():
        if parola_lower.startswith(contrazione):
            resto = parola_lower[len(contrazione):]
            parti = []
            if prima: parti.append(prima)
            if dopo: parti.append(dopo)
            if resto: parti.append(resto)
            return parti
    
    # Gestione generica per altri apostrofi
    parti = parola.split("'")
    risultato = []
    
    for i, parte in enumerate(parti):
        parte = parte.strip()
        if parte:
            if i == 0 and len(parte) > 1:
                risultato.append(parte)
            elif i > 0 and parte and is_vocale(parte[0]):
                risultato.append(parte)
            elif parte:
                risultato.append(parte)
    
    return risultato if risultato else [parola]

def gestisci_prefissi_vocalici(parola):
    """Gestisce i prefissi con separatore virtuale"""
    parola_lower = parola.lower()
    
    for prefisso in PREFISSI_COMUNI:
        if parola_lower.startswith(prefisso):
            resto_parola = parola_lower[len(prefisso):]
            
            if (prefisso[-1] in VOCALI_DEBOLI and 
                resto_parola and 
                is_vocale(resto_parola[0]) and
                resto_parola[0] in VOCALI_FORTI):
                
                return prefisso + "|" + resto_parola
    
    return parola_lower

def is_vocale(c):
    """Controlla se un carattere è una vocale"""
    if c == '|':
        return False
    return c.lower() in VOCALI

def is_iato(c1, c2):
    """Controlla se due vocali formano uno iato"""
    c1, c2 = c1.lower(), c2.lower()
    return ((c1 in VOCALI_FORTI and c2 in VOCALI_FORTI) or
            (c1 in VOCALI_DEBOLI and c2 in VOCALI_DEBOLI) or
            (c1 in VOCALI_DEBOLI and c1.isupper()) or
            (c2 in VOCALI_DEBOLI and c2.isupper()))
