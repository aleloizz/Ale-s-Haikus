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

@web_bp.route('/bacheca')
def bacheca():
    """Pagina della bacheca comunitaria con filtri avanzati"""
    try:
        # Parametri di paginazione e filtri
        page = request.args.get('page', 1, type=int)
        per_page = 12  # Aumentato per la griglia
        
        tipo_filtro = request.args.get('tipo', '')
        autore_filtro = request.args.get('autore', '')
        search_query = request.args.get('search', '')
        solo_valide = request.args.get('solo_valide', 'false') == 'true'
        sort_by = request.args.get('sort', 'recent')  # recent, oldest, title, author, type
        
        # Costruisci la query base
        query = Poem.query
        
        # Applica filtri
        if tipo_filtro and tipo_filtro != 'all':
            query = query.filter(Poem.poem_type.ilike(f'%{tipo_filtro}%'))
        
        if autore_filtro and autore_filtro != 'all':
            query = query.filter(Poem.author.ilike(f'%{autore_filtro}%'))
        
        if search_query:
            # Ricerca nel titolo, contenuto e autore
            search_filter = f'%{search_query}%'
            query = query.filter(
                db.or_(
                    Poem.title.ilike(search_filter),
                    Poem.content.ilike(search_filter),
                    Poem.author.ilike(search_filter)
                )
            )
        
        if solo_valide:
            query = query.filter(Poem.is_valid == True)
        
        # Applica ordinamento
        if sort_by == 'recent':
            query = query.order_by(Poem.created_at.desc())
        elif sort_by == 'oldest':
            query = query.order_by(Poem.created_at.asc())
        elif sort_by == 'title':
            query = query.order_by(Poem.title.asc().nullslast(), Poem.created_at.desc())
        elif sort_by == 'author':
            query = query.order_by(Poem.author.asc().nullslast(), Poem.created_at.desc())
        elif sort_by == 'type':
            query = query.order_by(Poem.poem_type.asc().nullslast(), Poem.created_at.desc())
        else:
            query = query.order_by(Poem.created_at.desc())
        
        # Paginazione
        poesie = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Ottieni i tipi di poesia unici per il filtro
        tipi_disponibili = db.session.query(Poem.poem_type).distinct().filter(
            Poem.poem_type.isnot(None),
            Poem.poem_type != ''
        ).all()
        tipi_disponibili = [tipo[0] for tipo in tipi_disponibili if tipo[0]]
        
        # Ottieni gli autori unici per il filtro
        autori_disponibili = db.session.query(Poem.author).distinct().filter(
            Poem.author.isnot(None),
            Poem.author != ''
        ).all()
        autori_disponibili = [autore[0] for autore in autori_disponibili if autore[0]]
        
        return render_template('bacheca.html', 
                             poesie=poesie,
                             tipo_filtro=tipo_filtro,
                             autore_filtro=autore_filtro,
                             search_query=search_query,
                             solo_valide=solo_valide,
                             sort_by=sort_by,
                             tipi_disponibili=sorted(tipi_disponibili),
                             autori_disponibili=sorted(autori_disponibili))
        
    except Exception as e:
        flash(f'Errore nel caricamento della bacheca: {str(e)}', 'error')
        return render_template('bacheca.html', 
                             poesie=None,
                             tipo_filtro='',
                             autore_filtro='',
                             search_query='',
                             solo_valide=False,
                             sort_by='recent',
                             tipi_disponibili=[],
                             autori_disponibili=[])


@web_bp.route('/bacheca')
def bacheca():
    # Temporaneamente reindirizza alla pagina coming soon
    return render_template('comingsoon.html')
    
    # Il codice originale della bacheca rimane commentato per sviluppi futuri
    # ...resto del codice bacheca...

@web_bp.route('/wiki')
def wiki():
    """Pagina wiki con informazioni sui tipi di poesia"""
    return render_template('wiki.html')

@web_bp.route('/poesia/<int:poesia_id>')
def dettaglio_poesia(poesia_id):
    """Pagina di dettaglio di una singola poesia"""
    try:
        poesia = Poem.query.get_or_404(poesia_id)
        
        # Rianalizza la poesia per mostrare i dettagli completi
        analisi = analizza_poesia_completa(poesia.content)
        
        return render_template('dettaglio_poesia.html', 
                             poesia=poesia, 
                             analisi=analisi)
        
    except Exception as e:
        flash(f'Errore nel caricamento della poesia: {str(e)}', 'error')
        return redirect(url_for('web.bacheca'))

@web_bp.errorhandler(404)
def not_found_error(error):
    """Gestione errore 404"""
    return render_template('404.html'), 404

@web_bp.errorhandler(500)
def internal_error(error):
    """Gestione errore 500"""
    db.session.rollback()
    return render_template('500.html'), 500
