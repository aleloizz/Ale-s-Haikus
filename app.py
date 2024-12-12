from flask import Flask, render_template, request, redirect, send_from_directory

app = Flask(__name__)

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.before_request
def enforce_https_and_www():
    url = request.url
    if url.startswith("http://"):
        url = url.replace("http://", "https://", 1)
    if not url.startswith("https://www."):
        url = url.replace("https://", "https://www.", 1)
    if url != request.url:
        return redirect(url, code=301)
    
    
# Lista di eccezioni
eccezioni = {
    "poesia": 4,
    "eroico": 3,
    "eroiche": 3,
    "aerei": 3,
}

def conta_sillabe(stringa):
    """
    Conta il numero di sillabe in una stringa.
    """
    # Controlla se la parola è un'eccezione
    if stringa in eccezioni:
        return eccezioni[stringa]

    count = 0
    i = 0
    while i < len(stringa):
        if is_vocale(stringa[i]):
            count += 1

            # Gestione dei trittonghi
            if i + 2 < len(stringa) and is_trittongo(stringa[i], stringa[i + 1], stringa[i + 2]):
                i += 2
            # Gestione dei dittonghi
            elif i + 1 < len(stringa) and is_dittongo(stringa[i], stringa[i + 1]):
                i += 1
            # Gestione dello iato
            elif i + 1 < len(stringa) and is_iato(stringa[i], stringa[i + 1]):
                pass
        # Salta digrammi e trigrammi
        elif i + 1 < len(stringa) and is_digramma(stringa[i], stringa[i + 1]):
            pass
        elif i + 2 < len(stringa) and is_trigramma(stringa[i], stringa[i + 1], stringa[i + 2]):
            pass
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
        elif is_vocale(c) == is_vocale(buffer[-1] if buffer else ""):
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


def conta_sillabe_da_cluster(cluster):
    """
    Conta le sillabe in base ai cluster di vocali e consonanti.
    """
    count = 0
    for gruppo in cluster:
        if all(is_vocale(c) for c in gruppo):  # Cluster di vocali
            i = 0
            while i < len(gruppo):
                # Controllo trittongo
                if i + 2 < len(gruppo) and is_trittongo(gruppo[i], gruppo[i + 1], gruppo[i + 2]):
                    count += 1
                    i += 3
                # Controllo dittongo
                elif i + 1 < len(gruppo) and is_dittongo(gruppo[i], gruppo[i + 1]):
                    count += 1
                    i += 2
                # Controllo iato (che separa vocali)
                elif i + 1 < len(gruppo) and is_iato(gruppo[i], gruppo[i + 1]):
                    count += 1
                    i += 1  # Conta la prima vocale dello iato
                else:
                    count += 1
                    i += 1
        else:  # Cluster di consonanti
            pass  # Le consonanti non aggiungono sillabe
    return count


# Funzioni di supporto

def is_vocale(c):
    """
    Verifica se un carattere è una vocale.
    """
    c = c.lower()
    return c in "aeiouàèìòùáéíóú"


def is_iato(c1, c2):
    """
    Controlla se due caratteri formano uno iato.
    """
    vocali_forti = "aeo"
    vocali_deboli = "iu"
    return (
        (c1 in vocali_forti and c2 in vocali_forti) or  # Due vocali forti (o-e)
        (c1 in vocali_deboli and c2 in vocali_deboli) or  # Due vocali deboli (i-u)
        (c1 in vocali_deboli and c1.isupper()) or  # Vocale debole accentata (ì-a)
        (c2 in vocali_deboli and c2.isupper())    # Vocale debole accentata (a-ì)
    )


def is_dittongo(c1, c2):
    """
    Controlla se due caratteri formano un dittongo.
    """
    c1, c2 = c1.lower(), c2.lower()
    dittonghi = {("i", "a"), ("i", "e"), ("i", "o"), ("i", "u"),
                 ("u", "a"), ("u", "e"), ("u", "o")}
    return (c1, c2) in dittonghi and not is_iato(c1, c2)


def is_trittongo(c1, c2, c3):
    """
    Controlla se tre caratteri formano un trittongo.
    """
    c1, c2, c3 = c1.lower(), c2.lower(), c3.lower()
    return (c1 == 'i' and is_vocale(c2) and c3 == 'u') or \
           (c1 == 'u' and is_vocale(c2) and c3 == 'i')


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





@app.route("/", methods=["GET", "POST"])
def home():
    haiku = ""
    if request.method == "POST":
        haiku = request.form["haiku"].strip()
        versi = haiku.split("\n")
        if len(versi) != 3:
            return render_template("index.html", haiku=haiku, message="Devi inserire esattamente 3 versi! >:(")

        v1 = versi[0].strip().lower()
        v2 = versi[1].strip().lower()
        v3 = versi[2].strip().lower()



        s1 = conta_sillabe(v1)
        s2 = conta_sillabe(v2)
        s3 = conta_sillabe(v3)

        errors = []
        if s1 != 5:
            errors.append(f"Il primo verso dovrebbe avere 5 sillabe, ne ha {s1}.")
        if s2 != 7:
            errors.append(f"Il secondo verso dovrebbe avere 7 sillabe, ne ha {s2}.")
        if s3 != 5:
            errors.append(f"Il terzo verso dovrebbe avere 5 sillabe, ne ha {s3}.")

        if not errors:
            message = "Il tuo haiku è perfetto! :3"
        else:
            message = "<br>".join(errors)

        return render_template("index.html", haiku=haiku, message=message)

    return render_template("index.html", haiku=haiku, message="")

if __name__ == "__main__":
    app.run(debug=True)