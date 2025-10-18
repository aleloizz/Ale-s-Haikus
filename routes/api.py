from flask import Blueprint, request, jsonify, session
from services.poetry_analyzer import analizza_poesia_completa
from models.poem import Poem, db
from config.constants import SCHEMI_POESIA

api_bp = Blueprint('api', __name__, url_prefix='/api')

def calculate_rhyme_status_for_verses(analyzed_scheme, expected_scheme, num_verses):
    """Calcola lo stato delle rime per ogni verso (valid/invalid)"""
    if not expected_scheme:
        return ['valid'] * num_verses  # Se non c'è schema atteso, tutti validi
    
    # Converti schema atteso in stringa
    expected_string = ''.join(expected_scheme)
    
    if len(analyzed_scheme) != len(expected_string):
        return ['invalid'] * num_verses  # Se lunghezze diverse, tutti invalidi
    
    status = []
    for i in range(num_verses):
        if i < len(analyzed_scheme) and i < len(expected_string):
            if analyzed_scheme[i] == expected_string[i]:
                status.append('valid')
            else:
                status.append('invalid')
        else:
            status.append('invalid')
    
    return status

def validate_rhyme_pattern(analyzed_scheme, expected_scheme, analisi_rime=None, poem_type: str = None):
    """Valida se lo schema rime analizzato corrisponde a quello atteso"""
    if not expected_scheme:
        return True, []  # Se non c'è schema atteso, consideriamo valido
    
    # Converti schema atteso in stringa per confronto
    expected_string = ''.join(expected_scheme)
    analyzed_string = analyzed_scheme or ""
    poem_type = (poem_type or "").lower() if poem_type else None

    # Tolleranza per sonetti: accetta ottave ABBA ABBA o ABAB ABAB e terzine con lettere tra C/D/E
    if poem_type == 'sonetto' and len(analyzed_string) == 14:
        prefix8 = analyzed_string[:8]
        if prefix8 in ('ABBAABBA', 'ABABABAB'):
            suffix6 = analyzed_string[8:14]
            if suffix6 and set(suffix6) <= set('CDE') and 2 <= len(set(suffix6)) <= 3:
                # Ogni lettera deve apparire almeno 2 volte nelle terzine
                from collections import Counter
                cnt = Counter(suffix6)
                if all(v >= 2 for v in cnt.values()):
                    return True, []
    
    if analyzed_string == expected_string:
        return True, []
    
    # Genera errori specifici
    errors = []
    if len(analyzed_scheme) != len(expected_string):
        errors.append(f"Schema ha {len(analyzed_scheme)} rime invece di {len(expected_string)}")
    else:
        # Confronta posizione per posizione
        for i, (actual, expected) in enumerate(zip(analyzed_scheme, expected_string)):
            if actual != expected:
                # Estrai informazioni sui suoni se disponibili
                suono_info = ""
                if analisi_rime and 'suoni_finali' in analisi_rime and i < len(analisi_rime['suoni_finali']):
                    suono_attuale = analisi_rime['suoni_finali'][i]
                    
                    # Trova tutti i versi che dovrebbero rimare con questo (stessa lettera attesa)
                    versi_dovrebbero_rimare = []
                    suoni_dovrebbero_rimare = []
                    for j, lettera in enumerate(expected_string):
                        if j != i and lettera == expected and j < len(analisi_rime['suoni_finali']):
                            versi_dovrebbero_rimare.append(j + 1)
                            suoni_dovrebbero_rimare.append(analisi_rime['suoni_finali'][j])
                    
                    if versi_dovrebbero_rimare:
                        if len(versi_dovrebbero_rimare) == 1:
                            suono_info = f" (suono '{suono_attuale}' non rima con verso {versi_dovrebbero_rimare[0]}: '{suoni_dovrebbero_rimare[0]}')"
                        else:
                            versi_str = ', '.join(map(str, versi_dovrebbero_rimare))
                            suoni_str = ', '.join([f"'{s}'" for s in suoni_dovrebbero_rimare])
                            suono_info = f" (suono '{suono_attuale}' dovrebbe rimare con versi {versi_str}: {suoni_str})"
                    else:
                        suono_info = f" (suono '{suono_attuale}')"
                
                errors.append(f"Verso {i+1}: rima '{actual}' invece di '{expected}'{suono_info}")
    
    return False, errors

def get_expected_rhyme_scheme(tipo_poesia):
    """Restituisce lo schema rime atteso per un tipo di poesia"""
    # Prima controlla negli schemi predefiniti
    if tipo_poesia in SCHEMI_POESIA and 'rima' in SCHEMI_POESIA[tipo_poesia]:
        schema_predefinito = SCHEMI_POESIA[tipo_poesia]['rima']
        if schema_predefinito:
            return schema_predefinito
    
    # Schemi di default per tipi comuni
    schemi_attesi = {
        'sonetto': ['ABBA', 'ABBA', 'CDC', 'DCD'],
        'quartina': ['ABAB'],  # Schema più comune
        'quartina (rima alternata)': ['ABAB'],
        'quartina (rima baciata)': ['AABB'],
        'quartina (rima incrociata)': ['ABBA'],
        'terzina_dantesca': ['ABA'],
        'terzina (rima continua)': ['AAA'],
        'limerick': ['AABBA'],
        'ballad': ['ABCB'],
        'clerihew': ['AABB'],
        'stornello': ['ABA']
    }
    
    return schemi_attesi.get(tipo_poesia, [])

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
        
        # Parametro tolleranza opzionale (default: False per precisione assoluta)
        use_tolerance = data.get('use_tolerance', False)
        
        # Validazioni di base: consenti componimenti più lunghi (es. sonetto)
        # Alza il limite a 2000 caratteri per evitare falsi negativi sui sonetti
        if len(testo) > 2000:
            return jsonify({
                'error': True,
                'error_type': 'too_long',
                'message': 'Il testo è troppo lungo (max 2000 caratteri).'
            }), 400
        
        # Verifica tag HTML
        import re
        if re.search(r'<[^>]+>', testo):
            return jsonify({
                'error': True,
                'error_type': 'invalid_input',
                'message': 'Il testo contiene caratteri non ammessi.'
            }), 400
        
        # Analizza la poesia (passando parametro tolleranza)
        analisi = analizza_poesia_completa(testo, use_tolerance=use_tolerance)
        
        # Verifica errori nell'analisi
        if 'errore' in analisi:
            return jsonify({
                'error': True,
                'message': f'Errore nell\'analisi: {analisi["errore"]}'
            }), 500

        # Determina il tipo di poesia: se non fornito, usa quello riconosciuto dall'analizzatore
        tipo_poesia_req = (data.get('type') or '').strip().lower()
        tipo_poesia = tipo_poesia_req if tipo_poesia_req else analisi.get('tipo_riconosciuto', 'versi_liberi')
        
        # Ottieni il pattern aspettato per questo tipo di poesia
        pattern = get_syllable_pattern(tipo_poesia)
        
        # Verifica numero di versi
        num_versi = len(analisi['versi'])
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
                })
            elif num_versi > len(pattern):
                return jsonify({
                    'error': True,
                    'error_type': 'too_many_verses',
                    'poem_type': tipo_poesia,
                    'pattern': pattern,
                    'required': len(pattern),
                    'received': num_versi,
                    'message': f'Poesia troppo lunga! Un {tipo_poesia} richiede {len(pattern)} versi.'
                })
        
        # Formatta la risposta per il frontend
        results = []
        for i, verso in enumerate(analisi['versi']):
            sillabe = analisi['sillabe_per_verso'][i]
            # Determina il target basato sul tipo di poesia
            target = get_target_sillabe(tipo_poesia, i)
            
            # Estrai informazioni sulle rime per questo verso
            rhyme_info = None
            if 'analisi_rime' in analisi and 'schema' in analisi['analisi_rime']:
                schema = analisi['analisi_rime']['schema']
                if i < len(schema):
                    rhyme_info = schema[i] if schema[i] != '-' else None
            
            result_item = {
                'verse': i + 1,
                'text': verso,
                'syllables': sillabe,
                'target': target,
                'correct': sillabe == target if target else True
            }
            
            # Aggiungi informazioni sulle rime se disponibili (sempre per i versi liberi)
            if rhyme_info:
                result_item['rhyme'] = rhyme_info
            elif tipo_poesia == 'versi_liberi':
                # Per i versi liberi, aggiungi sempre il campo rhyme anche se null
                result_item['rhyme'] = None
                
            results.append(result_item)
        
        # Converti lo schema rime per compatibilità frontend
        # IMPORTANTE: Usa lo schema ATTESO, non quello analizzato
        expected_scheme = get_expected_rhyme_scheme(tipo_poesia)
        
        # Se non c'è uno schema atteso, usa quello analizzato come fallback
        if not expected_scheme:
            scheme_for_frontend = convert_rhyme_scheme_to_frontend(analisi['schema_rime'], analisi['tipo_riconosciuto'])
        else:
            scheme_for_frontend = expected_scheme
        
        # Valida se le rime rispettano il pattern atteso
            rhyme_valid, rhyme_errors = validate_rhyme_pattern(
                analisi['schema_rime'], 
                expected_scheme, 
                analisi.get('analisi_rime', {}),
                poem_type=tipo_poesia
            )
        
        # Calcola lo stato delle rime per ogni verso (per i badge nel frontend)
        rhyme_status = calculate_rhyme_status_for_verses(analisi['schema_rime'], expected_scheme, len(analisi['versi']))
        
        # Calcola la validità globale
        all_correct = all(r['correct'] for r in results)
        
        return jsonify({
            'poem_type': tipo_poesia,
            'pattern': pattern or [],
            'results': results,
            'valid': all_correct,
            'rhyme_analysis': {
                'scheme': scheme_for_frontend,
                'details': analisi['analisi_rime'],
                'valid': rhyme_valid,
                'errors': rhyme_errors,
                'verse_status': rhyme_status
            },
            'total_syllables': analisi['sillabe_totali'],
            'total_verses': analisi['num_versi'],
            'valid_structure': analisi['rispetta_metrica'],
            'metadata': analisi['dettagli_metrica'],
            'error': False,
            'parsing_version': 'modular_v1.0'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Errore durante l\'analisi: {str(e)}'
        }), 500

def get_syllable_pattern(tipo_poesia):
    """Restituisce il pattern di sillabe per un tipo di poesia"""
    patterns = {
        'haiku': [5, 7, 5],
        'tanka': [5, 7, 5, 7, 7],
        'katauta': [5, 7, 7],
        'choka': [5, 7, 5, 7, 5, 7, 5, 7, 7],
        'sedoka': [5, 7, 7, 5, 7, 7],
        'sonetto': [11] * 14,
        'quartina': [11] * 4,
        'stornello': [5, 11, 11],
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
    # Usa la stessa logica di get_syllable_pattern per mantenere coerenza
    pattern = get_syllable_pattern(tipo_poesia)
    
    if pattern and indice_verso < len(pattern):
        return pattern[indice_verso]
    
    return None  # Nessun target specifico (per versi liberi o fuori dal pattern)

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

        # Parametri opzionali
        use_tolerance = data.get('use_tolerance', False)
        selected_type = (data.get('poem_type') or '').strip().lower() or None

        # Analizza la poesia (passando parametro tolleranza)
        analisi = analizza_poesia_completa(data['testo'], use_tolerance=use_tolerance)

        # Verifica se ci sono errori nell'analisi
        if 'errore' in analisi:
            return jsonify({'error': f"Errore nell'analisi: {analisi['errore']}"}), 400

        # Enforce: pubblicazione consentita SOLO se la poesia rispetta la metrica
        # 1) Calcolo basato sul tipo selezionato dall'utente (se fornito)
        from services.poetry_analyzer import verifica_metrica
        is_valid_selected = None
        if selected_type:
            is_valid_selected = verifica_metrica(
                selected_type,
                analisi.get('num_versi', 0),
                analisi.get('sillabe_per_verso', []),
                analisi.get('schema_rime', ''),
                use_tolerance=use_tolerance
            )

        # 2) Fallback: usa la validità calcolata dall'analizzatore (tipo riconosciuto)
        is_valid_recognized = bool(analisi.get('rispetta_metrica', False))

        # Determina validità finale (preferisci controllo sul tipo selezionato se presente)
        final_valid = (is_valid_selected if is_valid_selected is not None else is_valid_recognized)
        if not final_valid:
            # Prepara messaggio coerente col frontend
            expected_info = get_syllable_pattern(selected_type) if selected_type else None
            return jsonify({
                'success': False,
                'message': 'Pubblicazione non consentita: la poesia non rispetta i vincoli metrici della tipologia scelta.',
                'details': [
                    f"Tipo selezionato: {selected_type}" if selected_type else f"Tipo riconosciuto: {analisi.get('tipo_riconosciuto', 'sconosciuto')}",
                    f"Tolleranza attiva: {'sì' if use_tolerance else 'no'}",
                ] + ([f"Pattern atteso: {expected_info}"] if expected_info else []),
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

        # Parametri opzionali
        use_tolerance = data.get('use_tolerance', False)
        selected_type = (data.get('poem_type') or data.get('tipo') or '').strip().lower() or None

        # Analizza la poesia con eventuale tolleranza
        analisi = analizza_poesia_completa(testo, use_tolerance=use_tolerance)

        # Verifica se ci sono errori nell'analisi
        if 'errore' in analisi:
            return jsonify({'error': f"Errore nell'analisi: {analisi['errore']}"}), 400

        # Enforce: la pubblicazione è consentita SOLO se la poesia rispetta la metrica del tipo scelto
        from services.poetry_analyzer import verifica_metrica
        is_valid_selected = None
        if selected_type:
            is_valid_selected = verifica_metrica(
                selected_type,
                analisi.get('num_versi', 0),
                analisi.get('sillabe_per_verso', []),
                analisi.get('schema_rime', ''),
                use_tolerance=use_tolerance
            )
        is_valid_recognized = bool(analisi.get('rispetta_metrica', False))
        final_valid = (is_valid_selected if is_valid_selected is not None else is_valid_recognized)
        if not final_valid:
            expected_info = get_syllable_pattern(selected_type) if selected_type else None
            return jsonify({
                'success': False,
                'message': 'Pubblicazione non consentita: la poesia non rispetta i vincoli metrici della tipologia scelta.',
                'details': [
                    f"Tipo selezionato: {selected_type}" if selected_type else f"Tipo riconosciuto: {analisi.get('tipo_riconosciuto', 'sconosciuto')}",
                    f"Tolleranza attiva: {'sì' if use_tolerance else 'no'}",
                ] + ([f"Pattern atteso: {expected_info}"] if expected_info else []),
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

@api_bp.route('/poems/<int:poem_id>/like', methods=['POST'])
def api_like_poem(poem_id):
    """API endpoint per dare like a una poesia"""
    try:
        # Trova la poesia
        poem = Poem.query.get_or_404(poem_id)
        
        # Evita doppio-like nella stessa sessione
        liked_poems = session.get('liked_poems', [])
        if poem_id in liked_poems:
            # Nessun incremento, già apprezzata in questa sessione
            return jsonify({
                'success': True,
                'likes': poem.likes or 0,
                'already_liked': True,
                'message': 'Hai già messo like a questa poesia.'
            })
        
        # Incrementa likes persistenti (contatore)
        poem.likes = (poem.likes or 0) + 1
        db.session.commit()
        
        # Aggiorna sessione
        liked_poems.append(poem_id)
        session['liked_poems'] = liked_poems
        
        return jsonify({
            'success': True,
            'likes': poem.likes,
            'message': 'Like aggiunto con successo!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Errore nel dare like: {str(e)}'
        }), 500

@api_bp.route('/poems/<int:poem_id>/unlike', methods=['POST'])
def api_unlike_poem(poem_id):
    """API endpoint per rimuovere like da una poesia"""
    try:
        # Trova la poesia
        poem = Poem.query.get_or_404(poem_id)
        
        # Rimuovi like solo se presente nella sessione
        liked_poems = session.get('liked_poems', [])
        if poem_id in liked_poems:
            poem.likes = max(0, (poem.likes or 0) - 1)
            db.session.commit()
            liked_poems = [pid for pid in liked_poems if pid != poem_id]
            session['liked_poems'] = liked_poems
        # Se non era presente, non decrementare
        
        return jsonify({
            'success': True,
            'likes': poem.likes,
            'message': 'Like rimosso!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Errore nel rimuovere like: {str(e)}'
        }), 500
        
@api_bp.route('/poems/<int:poem_id>/like/status', methods=['GET'])
def api_like_status(poem_id):
    """Ritorna lo stato like per questa poesia nella sessione corrente"""
    try:
        poem = Poem.query.get_or_404(poem_id)
        liked_poems = session.get('liked_poems', [])
        return jsonify({
            'success': True,
            'liked': poem_id in liked_poems,
            'likes': poem.likes or 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    

@api_bp.route('/stats', methods=['GET'])
def api_stats():
    """API endpoint per statistiche generali della bacheca"""
    try:
        total_poems = Poem.query.count()
        valid_poems = Poem.query.filter(Poem.is_valid == True).count()
        authors_count = db.session.query(Poem.author).distinct().count()
        
        # Conta poesie per tipo
        poems_by_type = db.session.query(
            Poem.poem_type, 
            db.func.count(Poem.id)
        ).filter(
            Poem.poem_type.isnot(None)
        ).group_by(Poem.poem_type).all()
        
        type_stats = {tipo: count for tipo, count in poems_by_type}
        
        return jsonify({
            'total_poems': total_poems,
            'valid_poems': valid_poems,
            'total_authors': authors_count,
            'poems_by_type': type_stats,
            'success_rate': round((valid_poems / total_poems * 100) if total_poems > 0 else 0, 2)
        })
        
    except Exception as e:
        return jsonify({'error': f'Errore nel recupero statistiche: {str(e)}'}), 500
