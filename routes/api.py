from flask import Blueprint, request, jsonify
from services.poetry_analyzer import analizza_poesia_completa
from models.poem import Poem, db
from config.constants import SCHEMI_POESIA

api_bp = Blueprint('api', __name__, url_prefix='/api')

def convert_rhyme_scheme_to_frontend(schema_string, tipo_poesia):
    """Converte lo schema rime da stringa al formato array compatibile con frontend"""
    if not schema_string or not schema_string.strip():
        return []
    
    # Se il tipo di poesia ha uno schema predefinito, usalo per dividere correttamente
    if tipo_poesia in SCHEMI_POESIA and 'rima' in SCHEMI_POESIA[tipo_poesia]:
        schema_predefinito = SCHEMI_POESIA[tipo_poesia]['rima']
        if schema_predefinito:
            return schema_predefinito
    
    # Altrimenti, cerca di dividere in base a pattern comuni
    schema = schema_string.strip()
    
    # Per sonetti (14 versi): ABBAABBACDCDCD -> ["ABBA", "ABBA", "CDC", "DCD"]
    if len(schema) == 14:
        return [schema[0:4], schema[4:8], schema[8:11], schema[11:14]]
    
    # Per quartine (4 versi): ABAB -> ["ABAB"]
    if len(schema) == 4:
        return [schema]
    
    # Per terzine (3 versi): ABA -> ["ABA"]
    if len(schema) == 3:
        return [schema]
    
    # Per limerick (5 versi): AABBA -> ["AABBA"]
    if len(schema) == 5:
        return [schema]
    
    # Default: ogni 4 lettere un gruppo
    groups = []
    for i in range(0, len(schema), 4):
        groups.append(schema[i:i+4])
    
    return groups if groups else [schema]

@api_bp.route('/analyze', methods=['POST'])
def api_analizza():
    """API endpoint per analizzare una poesia"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': True, 'message': 'Testo non fornito'}), 400
        
        testo = data['text']
        if not testo or not testo.strip():
            return jsonify({'error': True, 'message': 'Testo vuoto'}), 400
        
        # Validazioni di base
        if len(testo) > 500:
            return jsonify({
                'error': True,
                'error_type': 'too_long',
                'message': 'Il testo è troppo lungo (max 500 caratteri).'
            }), 400
        
        # Verifica tag HTML
        import re
        if re.search(r'<[^>]+>', testo):
            return jsonify({
                'error': True,
                'error_type': 'invalid_input',
                'message': 'Il testo contiene caratteri non ammessi.'
            }), 400
        
        # Analizza la poesia
        analisi = analizza_poesia_completa(testo)
        
        # Verifica errori nell'analisi
        if 'errore' in analisi:
            return jsonify({
                'error': True,
                'message': f'Errore nell\'analisi: {analisi["errore"]}'
            }), 500
        
        # Ottieni il pattern aspettato per questo tipo di poesia
        tipo_poesia = data.get('type', 'haiku').lower()
        pattern = get_syllable_pattern(tipo_poesia)
        
        # Usa il campo corretto dalla struttura restituita da poetry_analyzer
        versi = analisi.get('versi', [])
        sillabe_per_verso = analisi.get('sillabe_per_verso', [])
        num_versi = len(versi)
        
        # Verifica numero di versi
        if tipo_poesia != 'versi_liberi' and pattern:
            if num_versi < len(pattern):
                return jsonify({
                    'error': True,
                    'error_type': 'too_few_verses',
                    'poem_type': tipo_poesia,
                    'pattern': pattern,
                    'required': len(pattern),
                    'received': num_versi,
                    'message': f'Poesia troppo corta! Un {tipo_poesia} richiede {len(pattern)} versi.'
                }), 400
            elif num_versi > len(pattern):
                return jsonify({
                    'error': True,
                    'error_type': 'too_many_verses',
                    'poem_type': tipo_poesia,
                    'pattern': pattern,
                    'required': len(pattern),
                    'received': num_versi,
                    'message': f'Poesia troppo lunga! Un {tipo_poesia} richiede {len(pattern)} versi.'
                }), 400
        
        # Costruisci i risultati nel formato aspettato dal frontend
        results = []
        for i, (verso, sillabe) in enumerate(zip(versi, sillabe_per_verso)):
            target_sillabe = pattern[i] if pattern and i < len(pattern) else sillabe
            results.append({
                'verse': i + 1,
                'text': verso,
                'syllables': sillabe,
                'target': target_sillabe,
                'correct': sillabe == target_sillabe
            })
        
        # Calcola se la poesia è valida
        all_correct = all(res['correct'] for res in results)
        
        # Prepara l'analisi delle rime nel formato aspettato dal frontend
        analisi_rime = analisi.get('analisi_rime', {})
        schema_rime = analisi_rime.get('schema', '')
        
        rhyme_analysis = {
            'scheme': convert_rhyme_scheme_to_frontend(schema_rime, tipo_poesia),
            'valid': analisi.get('rispetta_metrica', False),
            'errors': []
        }
        
        return jsonify({
            'results': results,
            'poem_type': tipo_poesia,
            'pattern': pattern,
            'rhyme_analysis': rhyme_analysis,
            'total_syllables': sum(sillabe_per_verso),
            'valid': all_correct,
            'valid_structure': analisi.get('rispetta_metrica', False)
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Errore interno: {str(e)}'
        }), 500

def get_syllable_pattern(tipo_poesia):
    """Restituisce il pattern di sillabe atteso per un tipo di poesia"""
    patterns = {
        'haiku': [5, 7, 5],
        'tanka': [5, 7, 5, 7, 7],
        'katauta': [5, 7, 7],
        'choka': [5, 7, 5, 7, 5, 7, 5, 7, 7],
        'sedoka': [5, 7, 7, 5, 7, 7],
        'sonetto': [11] * 14,
        'stornello': [5, 11, 11],
        'quartina': [11] * 4,
        'ottava_rima': [11] * 8,
        'terzina_dantesca': [11, 11, 11],
        'limerick': [8, 8, 5, 5, 8],
        'ballad': [8, 6, 8, 6],
        'clerihew': [8, 8, 8, 8],
        'cinquain': [2, 4, 6, 8, 2],
        'versi_liberi': []
    }
    return patterns.get(tipo_poesia, [])

def get_target_sillabe(tipo_poesia, indice_verso):
    """Restituisce il numero di sillabe atteso per un verso specifico"""
    targets = {
        'haiku': [5, 7, 5],
        'tanka': [5, 7, 5, 7, 7],
        'katauta': [5, 7, 7],
        'limerick': [8, 8, 5, 5, 8]
    }
    
    if tipo_poesia in targets and indice_verso < len(targets[tipo_poesia]):
        return targets[tipo_poesia][indice_verso]
    
    return None  # Nessun target specifico

@api_bp.route('/poems', methods=['POST'])
def api_create_poem():
    """API endpoint per creare una poesia (alias per pubblica)"""
    try:
        data = request.get_json()
        
        # Validazione dati richiesti
        required_fields = ['title', 'text', 'author']
        for field in required_fields:
            if not data or field not in data or not data[field].strip():
                return jsonify({'error': f'Campo {field} mancante o vuoto'}), 400
        
        # Rimappa i campi per compatibilità con api_pubblica
        data['titolo'] = data['title']
        data['testo'] = data['text']
        data['autore'] = data['author']
        
        # Analizza la poesia
        analisi = analizza_poesia_completa(data['testo'])
        
        # Verifica se ci sono errori nell'analisi
        if 'errore' in analisi:
            return jsonify({'error': f'Errore nell\'analisi: {analisi["errore"]}'}), 400
        
        # Controlla se rispetta la metrica (solo se richiesto)
        richiede_metrica = data.get('richiede_metrica', False)  # Default False per poems
        if richiede_metrica and not analisi.get('rispetta_metrica', False):
            return jsonify({
                'error': 'La poesia non rispetta la metrica richiesta',
                'tipo_riconosciuto': analisi.get('tipo_riconosciuto', 'sconosciuto'),
                'dettagli_metrica': analisi.get('dettagli_metrica', {}),
                'analisi': analisi
            }), 400
        
        # Crea e salva la poesia
        poesia = Poem.create_from_analysis(data['titolo'], data['testo'], data['autore'], analisi)
        
        db.session.add(poesia)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Poesia pubblicata con successo!',
            'id': poesia.id,
            'analisi': analisi
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Errore durante la pubblicazione: {str(e)}'}), 500

@api_bp.route('/pubblica', methods=['POST'])
def api_pubblica():
    """API endpoint per pubblicare una poesia nella bacheca"""
    try:
        data = request.get_json()
        
        # Validazione dati richiesti
        required_fields = ['titolo', 'testo', 'autore']
        for field in required_fields:
            if not data or field not in data or not data[field].strip():
                return jsonify({'error': f'Campo {field} mancante o vuoto'}), 400
        
        titolo = data['titolo'].strip()
        testo = data['testo'].strip()
        autore = data['autore'].strip()
        
        # Analizza la poesia
        analisi = analizza_poesia_completa(testo)
        
        # Verifica se ci sono errori nell'analisi
        if 'errore' in analisi:
            return jsonify({'error': f'Errore nell\'analisi: {analisi["errore"]}'}), 400
        
        # Controlla se rispetta la metrica (solo se richiesto)
        richiede_metrica = data.get('richiede_metrica', True)
        if richiede_metrica and not analisi.get('rispetta_metrica', False):
            return jsonify({
                'error': 'La poesia non rispetta la metrica richiesta',
                'tipo_riconosciuto': analisi.get('tipo_riconosciuto', 'sconosciuto'),
                'dettagli_metrica': analisi.get('dettagli_metrica', {}),
                'analisi': analisi
            }), 400
        
        # Crea e salva la poesia
        poesia = Poem.create_from_analysis(titolo, testo, autore, analisi)
        
        db.session.add(poesia)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Poesia pubblicata con successo!',
            'id': poesia.id,
            'analisi': analisi
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Errore durante la pubblicazione: {str(e)}'}), 500

@api_bp.route('/bacheca', methods=['GET'])
def api_bacheca():
    """API endpoint per ottenere le poesie della bacheca"""
    try:
        # Parametri di paginazione
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filtri
        tipo = request.args.get('tipo')  # Filtra per tipo di poesia
        autore = request.args.get('autore')  # Filtra per autore
        solo_valide = request.args.get('solo_valide', 'false').lower() == 'true'
        
        # Costruisci la query
        query = Poem.query
        
        if tipo:
            query = query.filter(Poem.poem_type.ilike(f'%{tipo}%'))
        
        if autore:
            query = query.filter(Poem.author.ilike(f'%{autore}%'))
        
        if solo_valide:
            query = query.filter(Poem.is_valid == True)
        
        # Ordina per data di creazione (più recenti prima)
        query = query.order_by(Poem.created_at.desc())
        
        # Paginazione
        poesie_paginate = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'poesie': [poesia.to_dict() for poesia in poesie_paginate.items],
            'total': poesie_paginate.total,
            'pages': poesie_paginate.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': poesie_paginate.has_next,
            'has_prev': poesie_paginate.has_prev
        })
        
    except Exception as e:
        return jsonify({'error': f'Errore nel recupero delle poesie: {str(e)}'}), 500

@api_bp.route('/poesia/<int:poesia_id>', methods=['GET'])
def api_poesia_dettaglio(poesia_id):
    """API endpoint per ottenere i dettagli di una poesia specifica"""
    try:
        poesia = Poem.query.get_or_404(poesia_id)
        return jsonify(poesia.to_dict())
        
    except Exception as e:
        return jsonify({'error': f'Errore nel recupero della poesia: {str(e)}'}), 500
