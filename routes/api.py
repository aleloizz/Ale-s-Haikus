from flask import Blueprint, request, jsonify
from services.poetry_analyzer import analizza_poesia_completa
from models.poem import Poem, db

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/analyze', methods=['POST'])
def api_analizza():
    """API endpoint per analizzare una poesia"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Testo non fornito'}), 400
        
        testo = data['text']
        if not testo or not testo.strip():
            return jsonify({'error': 'Testo vuoto'}), 400
        
        # Analizza la poesia
        analisi = analizza_poesia_completa(testo)
        
        # Formatta la risposta per il frontend
        results = []
        for i, verso in enumerate(analisi['versi']):
            sillabe = analisi['sillabe_per_verso'][i]
            # Determina il target basato sul tipo di poesia
            target = get_target_sillabe(analisi['tipo_riconosciuto'], i)
            
            results.append({
                'verse': i + 1,
                'text': verso,
                'syllables': sillabe,
                'target': target,
                'correct': sillabe == target if target else True
            })
        
        return jsonify({
            'results': results,
            'poem_type': analisi['tipo_riconosciuto'],
            'rhyme_analysis': {
                'scheme': analisi['schema_rime'],
                'details': analisi['analisi_rime']
            },
            'total_syllables': analisi['sillabe_totali'],
            'total_verses': analisi['num_versi'],
            'valid_structure': analisi['rispetta_metrica'],
            'metadata': analisi['dettagli_metrica']
        })
        
    except Exception as e:
        return jsonify({'error': f'Errore durante l\'analisi: {str(e)}'}), 500

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
