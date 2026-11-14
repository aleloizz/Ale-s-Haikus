"""Route HTML pubbliche."""
import re

from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)

from config.constants import (
    MAX_BACHECA_PAGE,
    MAX_FILTER_LENGTH,
)
from models.poem import Poem, db

web_bp = Blueprint("web", __name__)

_SEARCH_CONTROL_RE = re.compile(r"[\t\n\r\x00-\x1F\x7F]+")
_SEARCH_SPACES_RE = re.compile(r"\s{2,}")


@web_bp.route("/")
def index():
    """Homepage: landing page."""
    return render_template("landing.html")


@web_bp.route("/landing")
def landing():
    """Redirect alla root per evitare duplicati SEO."""
    return redirect(url_for("web.index"), code=301)


@web_bp.route("/analizzatore")
def analyzer():
    """Pagina analizzatore (ex index)."""
    return render_template("index.html")


@web_bp.route("/comingsoon")
def comingsoon():
    """Pagina coming soon per la bacheca."""
    return render_template("comingsoon.html")


@web_bp.route("/wiki")
def wiki():
    """Wiki delle forme poetiche."""
    return render_template("wiki.html")


@web_bp.route("/bacheca")
def bacheca():
    """Bacheca comunitaria con filtri e paginazione limitata."""
    page = request.args.get("page", 1, type=int) or 1
    page = max(1, min(page, MAX_BACHECA_PAGE))
    per_page = 12

    tipo_filtro = (request.args.get("tipo") or "").strip()[:MAX_FILTER_LENGTH]
    autore_filtro = (request.args.get("autore") or "").strip()[:MAX_FILTER_LENGTH]

    raw_search = request.args.get("search", "") or ""
    search_query = _SEARCH_CONTROL_RE.sub(" ", str(raw_search))
    search_query = _SEARCH_SPACES_RE.sub(" ", search_query).strip()[:MAX_FILTER_LENGTH]

    solo_valide = (request.args.get("solo_valide") or "").lower() == "true"
    sort_by = (request.args.get("sort") or "recent").strip() or "recent"

    try:
        query = Poem.query

        if search_query:
            like_input = (
                search_query.replace("\\", "\\\\")
                .replace("%", r"\%")
                .replace("_", r"\_")
            )
            search_pattern = f"%{like_input}%"
            query = query.filter(
                db.or_(
                    Poem.title.ilike(search_pattern, escape="\\"),
                    Poem.content.ilike(search_pattern, escape="\\"),
                    Poem.author.ilike(search_pattern, escape="\\"),
                )
            )

        if tipo_filtro:
            query = query.filter(Poem.poem_type == tipo_filtro)

        if autore_filtro:
            query = query.filter(Poem.author == autore_filtro)

        if solo_valide:
            query = query.filter(Poem.is_valid.is_(True))

        if sort_by == "oldest":
            query = query.order_by(Poem.created_at.asc())
        elif sort_by == "title":
            query = query.order_by(Poem.title.asc())
        elif sort_by == "author":
            query = query.order_by(Poem.author.asc())
        elif sort_by == "type":
            query = query.order_by(Poem.poem_type.asc())
        else:
            sort_by = "recent"
            query = query.order_by(Poem.created_at.desc())

        poesie = query.paginate(page=page, per_page=per_page, error_out=False)

        autori = (
            db.session.query(Poem.author)
            .distinct()
            .filter(Poem.author.isnot(None), Poem.author != "")
            .order_by(Poem.author.asc())
            .all()
        )
        autori = [author[0] for author in autori if author[0]]

        return render_template(
            "bacheca.html",
            poesie=poesie,
            search_query=search_query,
            tipo_filtro=tipo_filtro,
            autore_filtro=autore_filtro,
            solo_valide=solo_valide,
            sort_by=sort_by,
            autori=autori,
        )
    except Exception:
        current_app.logger.exception("bacheca_render_error")
        return (
            render_template(
                "bacheca.html",
                poesie=None,
                search_query="",
                tipo_filtro="",
                autore_filtro="",
                solo_valide=False,
                sort_by="recent",
                autori=[],
            ),
            500,
        )


@web_bp.route("/poesia/<int:poesia_id>")
def dettaglio_poesia(poesia_id):
    """Dettaglio di una singola poesia."""
    poem = db.session.get(Poem, poesia_id)
    if poem is None:
        abort(404)
    return render_template("dettaglio_poesia.html", poem=poem)
