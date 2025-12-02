from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Poem(db.Model):
    """Modello per le poesie salvate nel database"""
    __tablename__ = 'poems'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    
    # Analisi metrica
    verse_count = db.Column(db.Integer, nullable=False)
    syllable_counts = db.Column(db.String(100), nullable=False)  # Es: "5,7,5"
    rhyme_scheme = db.Column(db.String(50), nullable=True)  # Es: "ABA"
    poem_type = db.Column(db.String(50), nullable=True)  # Es: "haiku"
    
    # Metadati
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_valid = db.Column(db.Boolean, default=False)  # Rispetta la metrica
    likes = db.Column(db.Integer, nullable=False, default=0)  # Conteggio like
    
    def __repr__(self):
        return f'<Poem {self.title} by {self.author}>'
    
    def to_dict(self):
        """Converte il modello in dizionario per JSON"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'verse_count': self.verse_count,
            'syllable_counts': self.syllable_counts,
            'rhyme_scheme': self.rhyme_scheme,
            'poem_type': self.poem_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_valid': self.is_valid,
            'likes': self.likes or 0
        }
    
    @classmethod
    def create_from_analysis(cls, title, content, author, analysis, poem_type_override: str | None = None):
        """Crea un nuovo poem dai risultati dell'analisi.

        poem_type_override consente di forzare la tipologia selezionata
        dall'utente quando disponibile (es. katauta), altrimenti usa quella
        riconosciuta dall'analizzatore.
        """
        tipo_riconosciuto = analysis.get('tipo_riconosciuto', 'libero')
        poem_type_final = (poem_type_override or tipo_riconosciuto) or 'libero'
        return cls(
            title=title,
            content=content,
            author=author,
            verse_count=analysis.get('num_versi', 0),
            syllable_counts=','.join(map(str, analysis.get('sillabe_per_verso', []))),
            rhyme_scheme=analysis.get('schema_rime', ''),
            poem_type=poem_type_final,
            is_valid=analysis.get('rispetta_metrica', False)
        )
