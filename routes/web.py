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
        per_page = 12
        
        # Parametri filtro
        tipo_filtro = request.args.get('tipo', '').strip()
        autore_filtro = request.args.get('autore', '').strip()
        search_query = request.args.get('search', '').strip()
        solo_valide = request.args.get('solo_valide', 'false').lower() == 'true'
        sort_by = request.args.get('sort', 'recent')
        
        # Query base - MANTIENI I NOMI ORIGINALI DELLE COLONNE
        query = Poem.query
        
        # Applica filtri di ricerca
        if search_query:
            search_pattern = f'%{search_query}%'
            query = query.filter(
                db.or_(
                    Poem.title.ilike(search_pattern),      
                    Poem.content.ilike(search_pattern),   
                    Poem.author.ilike(search_pattern)      
                )
            )
        
        # Filtro per tipologia
        if tipo_filtro:
            query = query.filter(Poem.poem_type == tipo_filtro)  
        
        # Filtro per autore
        if autore_filtro:
            query = query.filter(Poem.author == autore_filtro)   
        
        # Filtro solo poesie valide
        if solo_valide:
            query = query.filter(Poem.is_valid == True)          
        
        # Ordinamento
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
        
        # Paginazione
        poesie = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Lista autori per filtro dropdown - MANTIENI NOMI ORIGINALI
        autori = db.session.query(Poem.author).distinct().filter(
            Poem.author.isnot(None),
            Poem.author != ''
        ).order_by(Poem.author.asc()).all()
        autori = [a[0] for a in autori if a[0]]
        
        return render_template('bacheca.html',
                             poesie=poesie,
                             search_query=search_query,
                             tipo_filtro=tipo_filtro,
                             autore_filtro=autore_filtro,
                             solo_valide=solo_valide,
                             sort_by=sort_by,
                             autori=autori)
                             
    except Exception as e:
        flash(f'Errore nel caricamento della bacheca: {str(e)}', 'error')
        return render_template('500.html'), 500


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
