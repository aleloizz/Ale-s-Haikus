from flask import Flask, render_template, request, redirect, send_from_directory, jsonify, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configurazione database
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///poems.db').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELLI DATABASE
class Poem(db.Model):
    __tablename__ = 'poems'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    text = db.Column(db.Text, nullable=False)
    poem_type = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(50), default="Poeta Anonimo")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_valid = db.Column(db.Boolean, default=False)  # Se rispetta la metrica
    likes = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Poem {self.id}: {self.title or "Senza titolo"}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'text': self.text,
            'poem_type': self.poem_type,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'is_valid': self.is_valid,
            'likes': self.likes
        }

# CREA LE TABELLE (sostituisci la sezione esistente)
def create_tables():
    """Crea le tabelle del database se non esistono"""
    with app.app_context():
        db.create_all()

# Inizializza all'avvio
create_tables()

# ROUTE ESISTENTI
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route("/wiki")
def wiki():
    return render_template("wiki.html")

# NUOVE ROUTE PER LA BACHECA
@app.route("/bacheca")
def bacheca():
    """Pagina principale della bacheca con tutte le poesie pubblicate"""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('type', 'all')
    
    query = Poem.query
    
    # Filtro per tipo di poesia
    if filter_type != 'all':
        query = query.filter_by(poem_type=filter_type)
    
    # Paginazione (10 poesie per pagina)
    poems = query.order_by(Poem.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Ottieni tutti i tipi di poesia disponibili per il filtro
    poem_types = db.session.query(Poem.poem_type).distinct().all()
    poem_types = [pt[0] for pt in poem_types]
    
    return render_template("bacheca.html", 
                         poems=poems, 
                         poem_types=poem_types,
                         current_filter=filter_type)

@app.route("/api/poems", methods=['GET'])
def api_get_poems():
    """API per ottenere le poesie (per AJAX)"""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('type', 'all')
    
    query = Poem.query
    if filter_type != 'all':
        query = query.filter_by(poem_type=filter_type)
    
    poems = query.order_by(Poem.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return jsonify({
        'poems': [poem.to_dict() for poem in poems.items],
        'has_next': poems.has_next,
        'has_prev': poems.has_prev,
        'page': poems.page,
        'pages': poems.pages,
        'total': poems.total
    })

@app.route("/api/poems/<int:poem_id>/like", methods=['POST'])
def api_like_poem(poem_id):
    """API per mettere like a una poesia"""
    poem = Poem.query.get_or_404(poem_id)
    poem.likes += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'likes': poem.likes
    })

@app.route("/api/poems", methods=['POST'])
def api_create_poem():
    """API per pubblicare una nuova poesia"""
    data = request.get_json()
    
    # Validazione input
    required_fields = ['text', 'poem_type']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'error': True,
                'message': f'Campo obbligatorio mancante: {field}'
            }), 400
    
    # Sanitizzazione
    text = data['text'].strip()
    poem_type = data['poem_type'].lower()
    title = data.get('title', '').strip()[:100]  # Max 100 caratteri
    author = data.get('author', 'Poeta Anonimo').strip()[:50]  # Max 50 caratteri
    
    # Verifica che il tipo di poesia sia supportato
    if poem_type not in SCHEMI_POESIA:
        return jsonify({
            'error': True,
            'message': 'Tipo di poesia non supportato'
        }), 400
    
    # Analizza la poesia per verificare se è valida
    try:
        # Riusa la logica di api_analyze
        verses = [v.strip() for v in text.split('\n') if v.strip()]
        schema = SCHEMI_POESIA[poem_type]
        target_syllables = schema["sillabe"]
        
        is_valid = True
        if poem_type != "versi_liberi":
            # Verifica numero versi
            if len(verses) != len(target_syllables):
                is_valid = False
            else:
                # Verifica sillabe
                for verse, target in zip(verses, target_syllables):
                    if conta_sillabe(verse) != target:
                        is_valid = False
                        break
        
    except Exception:
        is_valid = False
    
    # Crea la nuova poesia
    new_poem = Poem(
        title=title if title else None,
        text=text,
        poem_type=poem_type,
        author=author,
        is_valid=is_valid
    )
    
    try:
        db.session.add(new_poem)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Poesia pubblicata con successo!',
            'poem': new_poem.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': True,
            'message': 'Errore nel salvare la poesia'
        }), 500

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

# COSTANTI E FUNZIONI ESISTENTI (mantieni tutto il codice esistente)
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

# API ESISTENTE (mantieni invariata)
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
        poem_type = request.form.get("poemType", "haiku")
        text = request.form["poemText"].strip()
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