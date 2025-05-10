from flask import Flask, render_template, request, redirect, send_from_directory, jsonify
import re
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

#attenzione a possibili conflitti
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route("/wiki")
def wiki():
    return render_template("wiki.html")

#!!!decommentare in fase di produzione!!!
@app.before_request
def enforce_https_and_www():
    url = request.url
    if url.startswith("http://"):
        url = url.replace("http://", "https://", 1)
    if not url.startswith("https://www."):
        url = url.replace("https://", "https://www.", 1)
    if url != request.url:
        return redirect(url, code=301)


# Riorganizza le eccezioni e le costanti in modo più efficiente
VOCALI_FORTI = "aeoàèòáéó"
VOCALI_DEBOLI = "iuìùíú"
VOCALI = VOCALI_FORTI + VOCALI_DEBOLI

ECCEZIONI = {
    "poesia": 4, "eroico": 3, "eroiche": 3, "aerei": 3,
    "aereo" : 3, "continuò": 4, "scippo": 2, "scippar": 2,
    "scippa": 2, "obbluò":3,
    "quì": 1, "quí": 1, "più": 1, "piú": 1,
    "qui": 1, "cui": 1, "lui": 1, "sui": 1,
    "fui": 1, "fù": 1, "ambiguò" :4, "ambiguità": 4, 
    "già": 1, "giù": 1, "giú": 1, "giù": 1,
    "asciugamano": 5, "asciugamani": 5, "whisky": 2,
    "quiz": 1, "quizz": 1, "guizzare" :3, "quindicina": 4,
}

DIGRAMMI = {'gn', 'sc'}
TRIGRAMMI = {'sci'}

# Struttura unificata per schemi metrici e rimici
SCHEMI_POESIA = {
    "haiku": {
        "sillabe": [5, 7, 5],
        "rima": []
    },
    "tanka": {
        "sillabe": [5, 7, 5, 7, 7],
        "rima": []
    },
        "katauta": {
        "sillabe": [5, 7, 7],
        "rima": []
    },
    "choka": {
        "sillabe": [5, 7, 5, 7, 5, 7, 5, 7, 7],
        "rima": []
    },
    "sedoka": {
        "sillabe": [5, 7, 7, 5, 7, 7],
        "rima": []
    },
    "sonetto": {
        "sillabe": [11] * 14,  # Endecasillabi
        "rima": ["ABBA", "ABBA", "CDC", "DCD"]
    },
    "quartina": {
        "sillabe": [11] * 4,  # Endecasillabi
        "rima": ["ABAB"]
    },
        "stornello": {
        "sillabe": [5, 11, 11],  # quinario, endecasillabo, endecasillabo
        "rima": ["ABA"]           # primo e terzo rimano, secondo in consonanza
    },
     "ottava_rima": {
        "sillabe": [11] * 8,  # 8 endecasillabi
        "rima": ["ABABABCC"]
    },
    "terzina_dantesca": {
        "sillabe": [11, 11, 11],  # 3 endecasillabi per ogni terzina
        "rima": ["ABA"]  # Solo la prima terzina, per ora
    },
        "versi_liberi": {
        "sillabe": [],  # Nessun vincolo
        "rima": []
    },
    "limerick": {
        "sillabe": [8, 8, 5, 5, 8],
        "rima": ["AABBA"]
    },
        "ballad": {
        "sillabe": [8, 6, 8, 6],  # Ballad stanza tipica
        "rima": ["ABCB"]
    },
    "clerihew": {
        "sillabe": [8, 8, 8, 8],  # Clerihew: metrica libera, 4 versi
        "rima": ["AABB"]
    },
    "cinquain": {
        "sillabe": [2, 4, 6, 8, 2],  # Cinquain classico
        "rima": []
    }
}

def conta_sillabe(parola):
    """Versione ottimizzata che gestisce accuratamente accenti"""
    if parola in ECCEZIONI:
        return ECCEZIONI[parola]
    
    parola = parola.lower()
    count = 0
    i = 0
    n = len(parola)
    
    while i < n:
        # Gestione trigrammi consonantici (es. 'sci')
        if i + 2 < n and parola[i:i+3] in TRIGRAMMI:
            i += 3
        # Gestione digrammi consonantici (es. 'gn', 'sc')
        elif i + 1 < n and parola[i:i+2] in DIGRAMMI:
            i += 2
        # Gestione vocali e gruppi vocalici
        elif i < n and is_vocale(parola[i]):
            count += 1
            # Controlla trittonghi
            if i + 2 < n and is_trittongo(parola[i], parola[i+1], parola[i+2]):
                i += 3
            # Controlla dittonghi
            elif i + 1 < n and is_dittongo(parola[i], parola[i+1]):
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    return count



# Esempio di correzione per segmenta_cluster
def segmenta_cluster(stringa):
    """
    Divide la stringa in cluster di vocali e consonanti, considerando digrammi e trigrammi.
    """
    cluster = []
    buffer = ""
    i = 0
    while i < len(stringa):
        c = stringa[i]
        # Controllo trigrammi
        if i + 2 < len(stringa) and is_trigramma(c, stringa[i + 1], stringa[i + 2]):
            if buffer:
                cluster.append(buffer)
                buffer = ""
            cluster.append(c + stringa[i + 1] + stringa[i + 2])
            i += 3
        # Controllo digrammi
        elif i + 1 < len(stringa) and is_digramma(c, stringa[i + 1]):
            if buffer:
                cluster.append(buffer)
                buffer = ""
            cluster.append(c + stringa[i + 1])
            i += 2
        # Raggruppa vocali o consonanti
        elif is_vocale(c) == (is_vocale(buffer[-1]) if buffer else False):
            buffer += c
            i += 1
        else:
            if buffer:
                cluster.append(buffer)
            buffer = c
            i += 1
    if buffer:
        cluster.append(buffer)
    return cluster


# Funzioni di supporto

def is_vocale(c):
    """Versione ottimizzata per controllare se un carattere è una vocale"""
    return c.lower() in VOCALI

def is_iato(c1, c2):
    """Versione più efficiente per controllare se due vocali formano uno iato"""
    c1, c2 = c1.lower(), c2.lower()
    return ((c1 in VOCALI_FORTI and c2 in VOCALI_FORTI) or
            (c1 in VOCALI_DEBOLI and c2 in VOCALI_DEBOLI) or
            (c1 in VOCALI_DEBOLI and c1.isupper()) or
            (c2 in VOCALI_DEBOLI and c2.isupper()))


# Dittonghi precalcolati con tutte le combinazioni accentate
DITTONGHI = {
    # Crescenti (i/u + vocale forte)
    *{f"i{v}" for v in VOCALI_FORTI},
    *{f"u{v}" for v in VOCALI_FORTI},
    *{f"ì{v}" for v in VOCALI_FORTI},
    *{f"ù{v}" for v in VOCALI_FORTI},
    
    # Discendenti (vocale forte + i/u)
    *{f"{v}i" for v in VOCALI_FORTI},
    *{f"{v}u" for v in VOCALI_FORTI},
    *{f"{v}ì" for v in VOCALI_FORTI.replace('ì','').replace('ù','')},  # Evita doppi accenti
    *{f"{v}ù" for v in VOCALI_FORTI.replace('ì','').replace('ù','')},
    
    # Deboli (i/u combinate)
    'iu', 'ui', 'ìu', 'ùi', 'iù', 'uì'
}

# Trittonghi precalcolati con accenti
TRITTONGHI = {
    'iai', 'iei', 'uai', 'uei',
    'iài', 'ièi', 'iéi', 'uài', 'uèi', 'uéi',
    'ìai', 'ìei', 'ùai', 'ùei',
    'iaì', 'ieì', 'uaì', 'ueì',
    'iàu', 'ièu', 'iéu', 'uàu', 'uèu', 'uéu'
}

def is_dittongo(c1, c2):
    """Verifica se due caratteri formano un dittongo, inclusi accenti"""
    combo = f"{c1.lower()}{c2.lower()}"
    return combo in DITTONGHI and not is_iato(c1, c2)

def is_trittongo(c1, c2, c3):
    """Verifica se tre caratteri formano un trittongo, inclusi accenti"""
    combo = f"{c1.lower()}{c2.lower()}{c3.lower()}"
    return combo in TRITTONGHI or (
        c1.lower() in 'iìuù' and 
        is_vocale(c2) and 
        c3.lower() in 'iìuù'
    ) 
           

def is_digramma(c1, c2):
    """
    Controlla se due caratteri formano un digramma.
    """
    return (c1 == 'g' and c2 == 'n') or (c1 == 's' and c2 == 'c')


def is_trigramma(c1, c2, c3):
    """
    Controlla se tre caratteri formano un trigramma.
    """
    return (c1 == 's' and c2 == 'c' and c3 == 'i')

def estrai_ultime_sillabe(verso, num_sillabe=2):
    """Estrae le ultime 'num_sillabe' sillabe per l'analisi delle rime"""
    sillabe = []
    cluster = segmenta_cluster(verso.lower())
    i = len(cluster) - 1
    
    while len(sillabe) < num_sillabe and i >= 0:
        if any(is_vocale(c) for c in cluster[i]):  # Se è un cluster vocalico
            sillabe.insert(0, cluster[i])
        i -= 1
    
    return ''.join(sillabe[-num_sillabe:]) if sillabe else ""

def analizza_rima(verso1, verso2):
    """Confronta due versi restituendo il grado di rima (0-3)"""
    suf1 = estrai_ultime_sillabe(verso1)
    suf2 = estrai_ultime_sillabe(verso2)
    
    if not suf1 or not suf2:
        return 0
    
    # Gradi di rima:
    if suf1 == suf2:  # Rima perfetta
        return 3
    elif suf1[-3:] == suf2[-3:]:  # Rima al trittongo
        return 2
    elif suf1[-2:] == suf2[-2:]:  # Rima al dittongo
        return 1
    return 0

# Nuovo endpoint API
@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json()
    poem_type = data.get('type', 'haiku').lower()
    text = data.get('text', '')

    # Rifiuta input con tag HTML
    if re.search(r'<[^>]+>', text):
        return jsonify({
            'error': True,
            'error_type': 'invalid_input',
            'message': 'Il testo contiene caratteri non ammessi.'
        }), 400

    MAX_LEN = 500
    if len(text) > MAX_LEN:
        return jsonify({
            'error': True,
            'error_type': 'too_long',
            'message': f'Il testo è troppo lungo (max {MAX_LEN} caratteri).'
        }), 400

    if poem_type not in SCHEMI_POESIA:
        return jsonify({
            'error': True,
            'error_type': 'unsupported_poem_type',
            'poem_type': poem_type,
            'supported_types': list(SCHEMI_POESIA.keys()),
            'message': f'Tipo di poesia non supportato. Scegli tra: {", ".join(SCHEMI_POESIA.keys())}'
        }), 400

    schema = SCHEMI_POESIA[poem_type]
    verses = [v.strip() for v in text.split('\n') if v.strip()]
    target_syllables = schema["sillabe"]

    if poem_type != "versi_liberi":
        if len(verses) < len(target_syllables):
            return jsonify({
                'error': True,
                'error_type': 'too_few_verses',
                'poem_type': poem_type,
                'pattern': target_syllables,
                'required': len(target_syllables),
                'received': len(verses),
                'message': f'Poesia troppo corta! Un {poem_type} richiede {len(target_syllables)} versi.'
            })

        if len(verses) > len(target_syllables):
            return jsonify({
                'error': True,
                'error_type': 'too_many_verses',
                'poem_type': poem_type,
                'pattern': target_syllables,
                'required': len(target_syllables),
                'received': len(verses),
                'message': f'Poesia troppo lunga! Un {poem_type} richiede {len(target_syllables)} versi.'
            })

    results = []
    if poem_type == "versi_liberi":
        for i, verse in enumerate(verses):
            try:
                count = conta_sillabe(verse)
                rima = estrai_ultime_sillabe(verse, num_sillabe=2)
                results.append({
                    'verse': i+1,
                    'text': verse,
                    'syllables': count,
                    'rhyme': rima,
                    'target': None,
                    'correct': True
                })
            except Exception as e:
                results.append({
                    'verse': i+1,
                    'text': verse,
                    'error': str(e),
                    'rhyme': '',
                    'correct': False
                })
        rhyme_report = None
    else:
        for i, (verse, target) in enumerate(zip(verses, target_syllables)):
            try:
                count = conta_sillabe(verse)
                results.append({
                    'verse': i+1,
                    'text': verse,
                    'syllables': count,
                    'target': target,
                    'correct': count == target
                })
            except Exception as e:
                results.append({
                    'verse': i+1,
                    'text': verse,
                    'error': str(e),
                    'correct': False
                })

    # Analisi rime solo se schema di rima presente e non versi liberi
    rhyme_report = None
    if poem_type != "versi_liberi" and schema.get("rima"):
        rime_finali = [estrai_ultime_sillabe(res['text'], num_sillabe=2) for res in results]
        scheme = schema["rima"]
        errors = []
        valid = True
        rhyme_map = {}
        verse_idx = 0
        # Mappa ogni lettera dello schema ai versi globali
        for group in scheme:
            for letter in group:
                if letter not in rhyme_map:
                    rhyme_map[letter] = []
                rhyme_map[letter].append(verse_idx)
                verse_idx += 1
        # Controlla che tutti i versi con la stessa lettera abbiano la stessa rima
        for letter, indices in rhyme_map.items():
            if len(indices) > 1:
                ref = rime_finali[indices[0]]
                for i in indices[1:]:
                    if rime_finali[i] != ref:
                        valid = False
                        errors.append(f"I versi {', '.join(str(j+1) for j in indices)} dovrebbero rimare ({letter}), ma non coincidono.")
                        break
        rhyme_report = {
            "valid": valid,
            "scheme": scheme,
            "errors": errors
        }

    return jsonify({
        'poem_type': poem_type,
        'pattern': target_syllables,
        'results': results,
        'valid': all(r.get('correct', False) for r in results),
        'rhyme_analysis': rhyme_report,
        'error': False
    })

# Route esistente modificata per compatibilità
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Supporta sia form tradizionale che AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return api_analyze()
            
        # Logica esistente per il form tradizionale
        poem_type = request.form.get("poemType", "haiku")  # Modifica qui
        text = request.form["poemText"].strip()  # Modifica qui
        versi = [v.strip() for v in text.split('\n') if v.strip()]
        
        if len(versi) != 3:
            return render_template("index.html", haiku=text, message="Devi inserire esattamente 3 versi! >:(")

        results = []
        for i, verso in enumerate(versi):
            count = conta_sillabe(verso.strip().lower())
            results.append({
                'verse': i+1,
                'syllables': count,
                'target': [5,7,5][i]
            })

        errors = [
            f"Il verso {res['verse']} dovrebbe avere {res['target']} sillabe, ne ha {res['syllables']}."
            for res in results if res['syllables'] != res['target']
        ]
        
        message = "Il tuo haiku è perfetto! :3" if not errors else "<br>".join(errors)
        return render_template("index.html", haiku=text, message=message)

    return render_template("index.html", haiku="", message="")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)