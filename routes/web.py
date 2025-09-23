from flask import Blueprint, render_template, request, flash, redirect, url_for
from models.poem import Poem, db
from services.poetry_analyzer import analizza_poesia_completa

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Pagina principale dell'applicazione"""
    return render_template('index.html')

@web_bp.route('/comingsoon')
def comingsoon():
    """Pagina coming soon per la bacheca"""
    return render_template('comingsoon.html')

@web_bp.route('/wiki')
def wiki():
    """Wiki delle forme poetiche"""
    return render_template('wiki.html')

@web_bp.route('/bacheca')
def bacheca():
    """Pagina della bacheca comunitaria con filtri avanzati"""
    try:
        # Parametri di paginazione e filtri con valori DEFAULT sicuri
        page = max(1, request.args.get('page', 1, type=int))
        per_page = 12
        
        # Parametri filtro - SEMPRE stringe, mai None
        tipo_filtro = request.args.get('tipo', '').strip()
        autore_filtro = request.args.get('autore', '').strip()
        # Ricerca: normalizza e applica limiti
        raw_search = request.args.get('search', '') or ''
        # Normalizza whitespace e rimuovi caratteri di controllo
        try:
            import re
            search_query = re.sub(r"[\t\n\r\x00-\x1F\x7F]+", " ", str(raw_search))
            search_query = re.sub(r"\s{2,}", " ", search_query).strip()
        except Exception:
            search_query = str(raw_search).strip()
        # Limite di lunghezza per query efficienti
        if len(search_query) > 120:
            search_query = search_query[:120]
        solo_valide = request.args.get('solo_valide', '').lower() == 'true'
        sort_by = request.args.get('sort', 'recent').strip() or 'recent'
        
        # Query base
        query = Poem.query
        
        # Applica filtri solo se non vuoti
        if search_query:
            # Escapa i caratteri jolly di LIKE per trattarli come letterali
            # Usa backslash come escape char e specifica escape='\\'
            like_input = search_query.replace('\\', '\\\\').replace('%', r'\%').replace('_', r'\_')
            search_pattern = f"%{like_input}%"
            query = query.filter(
                db.or_(
                    Poem.title.ilike(search_pattern, escape='\\'),
                    Poem.content.ilike(search_pattern, escape='\\'),
                    Poem.author.ilike(search_pattern, escape='\\')
                )
            )
        
        if tipo_filtro:
            query = query.filter(Poem.poem_type == tipo_filtro)
        
        if autore_filtro:
            query = query.filter(Poem.author == autore_filtro)
        
        if solo_valide:
            query = query.filter(Poem.is_valid == True)
        
        # Ordinamento sicuro
        if sort_by == 'recent':
            query = query.order_by(Poem.created_at.desc())
        elif sort_by == 'oldest':
            query = query.order_by(Poem.created_at.asc())
        elif sort_by == 'title':
            query = query.order_by(Poem.title.asc())
        elif sort_by == 'author':
            query = query.order_by(Poem.author.asc())
        elif sort_by == 'type':
            query = query.order_by(Poem.poem_type.asc())
        else:
            query = query.order_by(Poem.created_at.desc())
        
        # Paginazione sicura
        try:
            poesie = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
        except Exception as paginate_error:
            print(f"Errore paginazione: {paginate_error}")
            # Fallback alla prima pagina
            poesie = query.paginate(
                page=1, 
                per_page=per_page, 
                error_out=False
            )
        
        # Lista autori sicura
        try:
            autori = db.session.query(Poem.author).distinct().filter(
                Poem.author.isnot(None),
                Poem.author != ''
            ).order_by(Poem.author.asc()).all()
            autori = [a[0] for a in autori if a[0]]
        except Exception as authors_error:
            print(f"Errore caricamento autori: {authors_error}")
            autori = []
        
        # RETURN con valori SEMPRE definiti
        return render_template('bacheca.html',
                             poesie=poesie,
                             search_query=search_query,  # Sempre stringa
                             tipo_filtro=tipo_filtro,    # Sempre stringa
                             autore_filtro=autore_filtro, # Sempre stringa
                             solo_valide=solo_valide,    # Sempre boolean
                             sort_by=sort_by,           # Sempre stringa
                             autori=autori)             # Sempre lista
                             
    except Exception as e:
        print(f"ERRORE CRITICO BACHECA: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Template di emergenza con valori sicuri
        return render_template('bacheca.html',
                             poesie=None,
                             search_query='',
                             tipo_filtro='',
                             autore_filtro='',
                             solo_valide=False,
                             sort_by='recent',
                             autori=[]), 500

@web_bp.route('/poesia/<int:poesia_id>')
def dettaglio_poesia(poesia_id):
    """Dettaglio di una singola poesia"""
    try:
        poem = Poem.query.get_or_404(poesia_id)
        return render_template('dettaglio_poesia.html', poem=poem)
    except Exception as e:
        flash('Poesia non trovata', 'error')
        return redirect(url_for('web.bacheca'))

@web_bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@web_bp.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
