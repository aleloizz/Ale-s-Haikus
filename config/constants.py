# Costanti linguistiche
VOCALI_FORTI = "aeoàèòáéó"
VOCALI_DEBOLI = "iuìùíú" 
VOCALI = VOCALI_FORTI + VOCALI_DEBOLI

# Eccezioni al conteggio sillabe
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

# Combinazioni consonantiche
DIGRAMMI = {'gn', 'sc'}
TRIGRAMMI = {'sci'}

# Prefissi comuni
PREFISSI_COMUNI = {
    'ri', 'pre', 'pro', 'anti', 'auto', 'co', 'de', 'dis', 'ex', 'in', 'inter', 
    'micro', 'mini', 'multi', 'over', 'post', 'pseudo', 'quasi', 'semi', 'sub', 
    'super', 'trans', 'ultra', 'uni', 'vice', 'bi', 'tri', 'mono', 'poli',
    'contro', 'retro', 'intro', 'extra', 'infra', 'intra', 'meta', 'para',
    'proto', 'tele', 'video', 'audio', 'foto', 'geo', 'bio', 'eco', 'neo'
}

# Dittonghi e trittonghi
DITTONGHI = {
    # Crescenti (i/u + vocale forte)
    *{f"i{v}" for v in VOCALI_FORTI},
    *{f"u{v}" for v in VOCALI_FORTI},
    *{f"ì{v}" for v in VOCALI_FORTI},
    *{f"ù{v}" for v in VOCALI_FORTI},
    
    # Discendenti (vocale forte + i/u)
    *{f"{v}i" for v in VOCALI_FORTI},
    *{f"{v}u" for v in VOCALI_FORTI},
    *{f"{v}ì" for v in VOCALI_FORTI.replace('ì','').replace('ù','')},
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

# Schemi delle poesie
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
        "sillabe": [11] * 14,
        "rima": ["ABBA", "ABBA", "CDC", "DCD"]
    },
    "quartina": {
        "sillabe": [11] * 4,
        "rima": ["ABAB"]
    },
    "stornello": {
        "sillabe": [5, 11, 11],
        "rima": ["ABA"]
    },
    "ottava_rima": {
        "sillabe": [11] * 8,
        "rima": ["ABABABCC"]
    },
    "terzina_dantesca": {
        "sillabe": [11, 11, 11],
        "rima": ["ABA"]
    },
    "versi_liberi": {
        "sillabe": [],
        "rima": []
    },
    "limerick": {
        "sillabe": [8, 8, 5, 5, 8],
        "rima": ["AABBA"]
    },
    "ballad": {
        "sillabe": [8, 6, 8, 6],
        "rima": ["ABCB"]
    },
    "clerihew": {
        "sillabe": [8, 8, 8, 8],
        "rima": ["AABB"]
    },
    "cinquain": {
        "sillabe": [2, 4, 6, 8, 2],
        "rima": []
    }
}
