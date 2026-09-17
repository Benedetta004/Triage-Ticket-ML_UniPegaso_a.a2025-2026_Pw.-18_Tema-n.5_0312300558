# -*- coding: utf-8 -*-  #serve per gestire i caratteri speciali
import json #serve per leggere i file JSON
from pathlib import Path
import random
import string
import re
import pandas as pd #per strutturare i ticket in colonne
from sklearn.model_selection import train_test_split

DIRECTORY_PRINCIPALE = Path(__file__).parent
PERCORSO_TICKET = DIRECTORY_PRINCIPALE / "tickets.json"

LUNGHEZZA_ID_DEFAULT = 8 #indica la costante della lunghezza degli ID
TICKET_PER_CATEGORIA = 166 #indica la costante dei numeri ticket per ogni categoria

#Funzione per acquisire i templates per le categorie dei ticket
def carica_categorie():
    try: 
        with open(PERCORSO_TICKET, 'r', encoding='utf-8') as documento:
            return json.load(documento)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON malformattato:{e}")
    
#Funzione per generare ID univoco
def generatore_id(num_tk, length = LUNGHEZZA_ID_DEFAULT): #La funzione ha come input il numero di ticket e la costante che le serviranno per definire lunghezza ID
    lettere = string.ascii_lowercase #Utilizza codifica ASCII per lettere minuscole (dell'alfabeto inglese)
    numeri = string.digits #Utilizza codifica ASCII per numeri da 0 a 9
    caratteri = lettere + numeri #Combina lettere e numeri in un'unica stringa
    id_univoci = set() #Crea un insieme per memorizzare ID univoci

    while len(id_univoci) < num_tk: #Continua a generare ID finchè non raggiunge il numero desiderato
        caratteri_obbligatori = [
            random.choice(lettere), #Si assicura che ci sia almeno una lettera
            random.choice(numeri) #Si assicura che ci sia almeno un numero
        ]
        caratteri_id = caratteri_obbligatori + [random.choice(caratteri) for char in range(length-2)] #Aggiunge caratteri casuali per completare ID
        random.shuffle(caratteri_id) #Mescola i caratteri
        id_univoci.add(''.join(caratteri_id))
    return list (id_univoci) #Restituisce la lista di ID univoci generati

categorie = carica_categorie() #Carica le categorie di ticket dal file JSON

#Funzione che generare il Dataset Sintetico di ticket
def genera_dataset_sintetico(categorie, length =TICKET_PER_CATEGORIA):
    nomi_categorie = list(categorie.keys())
    totale_ticket = length * len(nomi_categorie)
    id_univoci = generatore_id(totale_ticket)

    ticket_list = [] #Crea una lista che conterrà i ticket generati

    for nome_categoria in nomi_categorie:
        informazioni = categorie[nome_categoria] 
        ticket_generati = 0 #contatore
        priorita_da_generare = ( # Numero di ticket da generare per ogni priorità
            ["alta"] * 55 +
            ["media"] * 55 +
            ["bassa"] * 56
        )
        random.shuffle(priorita_da_generare)

        while ticket_generati < length: 
            priorita_scelta = priorita_da_generare[ticket_generati]
            template_priorita = [
                template for template in informazioni["ticket_templates"]
                if template["priorita"] == priorita_scelta
            ]
            info_templates = random.choice(template_priorita)
            info_titolo = random.choice(informazioni["dettagli_titolo"]) #Sceglie casualmente un titolo per il ticket
            info_descrizione = random.choice(informazioni["dettagli_descrizione"]) #Sceglie casualmente una descrizione per il ticket
            titolo = info_templates["titolo"].format(dettagli_titolo= info_titolo)
            descrizione = random.choice(info_templates["descrizione"]).format(dettagli_descrizione=info_descrizione)

            if not valida_coerenza_ticket(titolo, descrizione, nome_categoria, categorie):
                continue #Se il ticket non è coerente, riprova il ciclo

            titolo = normalizza_sintassi(titolo) #normalizza il testo del titolo
            descrizione = normalizza_sintassi(descrizione) #normalizza il testo della descrizione

            categoria_finale = reclassifica_categoria(titolo, descrizione, nome_categoria, categorie)

            priorita_originale = info_templates["priorita"] #ottiene la priorità originale dal template
            priorita_riassegnata = assegna_priorita(titolo, descrizione, priorita_originale) #riclassifica priorità in base al titolo e alla descrizione

            varianti = genera_varianti_ticket(titolo, descrizione, categoria_finale, categorie)
            variante_selezionata = random.choice(varianti)

            titolo_finale = variante_selezionata["titolo"] #Ottine il titollo finale dalla variante selezionata
            descrizione_finale = variante_selezionata["descrizione"]

            id_ticket = id_univoci.pop()

            #Creazione dizionario per rappresentare ticket completo
            tk = {
                "id":id_ticket,
                "title": titolo_finale,
                "body": descrizione_finale,
                "category": categoria_finale,
                "priority": priorita_riassegnata
            }
            ticket_list.append(tk) #Aggiunge il ticket generato alla lista dei ticket
            ticket_generati +=1 #Serve per incrementare il contatore dei ticket
    return ticket_list

def esporta_dataset(ticket,nome_iniziale = 'dataset_ticket', stratify_col = 'category', seed = 1):
    if not ticket:
        print ("Nessun ticker da esportare")
        return None

    random.seed(seed) #Consente riproduciblità
    random.shuffle(ticket) #Mescola i ticket in modo casuale
    df = pd.DataFrame(ticket)

    print(df["category"].value_counts())
    print(df["priority"].value_counts())

    #Suddivisione Dataset in Train test (80%) e Test set (20%)
    train, temp = train_test_split(
        df,
        test_size = 0.2,
        stratify = df[stratify_col],
        random_state = seed
    )

    #Valutazione dei modelli sul test set (20%)
    val,test = train_test_split(
        temp,
        test_size = 0.5,
        stratify = temp[stratify_col],
        random_state = seed
    )

    splits = {
        'mix': df,
        'train': train,
        'valid': val,
        'test': test
    }

    #Esportazione dei csv
    try:
        for nome_split, split_df in splits.items():
            filename = f"{nome_iniziale}_{nome_split}.csv"
            path = DIRECTORY_PRINCIPALE / filename
            split_df.to_csv(path, index = False, encoding = 'utf-8-sig')
    except Exception as e:
        print(f"Errore durante il salvataggio dei file CSV: {e}")
        return None

#Funzione per correggere errori
def normalizza_sintassi(testo):
    if not testo:
        return testo

    encoding_fix = {
        "Ã ": "à",
        "Ã€": "À",
        "Ã¨": "è",
        "Ã©": "é",
        "Ãˆ": "È",
        "Ã‰": "É",
        "Ã¬": "ì",
        "Ã²": "ò",
        "Ã³": "ó",
        "Ã’": "Ò",
        "Ã¹": "ù",
        "Ã™": "Ù",
        "â€™": "'"
        }
    for sbagliato, corretto in encoding_fix.items():
        testo = testo.replace(sbagliato, corretto)

    apostrofi_fix = {
        "e'": "è",
        "E'": "È",
        "a''": "à",
        "A'": "À",
        "i'": "ì",
        "I'": "Ì",
        "o'": "ò",
        "O'": "Ò",
        "u'": "ù",
        "U'": "Ù",
        }
    for sbagliato, corretto in apostrofi_fix.items():
        testo = testo.replace(sbagliato, corretto)

    contrazioni = {
        r'\bdi\s+il\b': "del",
        r'\bdi\s+lo\b': "dello",
        r'\bdi\s+la\b': "della",
        r'\bdi\s+i\b': "dei",
        r'\bdi\s+gli\b': "degli",
        r'\bdi\s+le\b': "delle",
        r'\ba\s+il\b': "al",
        r'\ba\s+lo\b': "allo",
        r'\ba\s+la\b': "alla",
        r'\ba\s+i\b': "ai",
        r'\ba\s+gli\b': "agli",
        r'\ba\s+le\b': "alle",
        r'\bda\s+il\b': "dal",
        r'\bda\s+lo\b': "dallo",
        r'\bda\s+la\b': "dalla",
        r'\bda\s+i\b': "dai",
        r'\bda\s+gli\b': "dagli",
        r'\bda\s+le\b': "dalle",
        r'\bin\s+il\b': "nel",
        r'\bin\s+lo\b': "nello",
        r'\bin\s+la\b': "nella",
        r'\bin\s+i\b': "nei",
        r'\bin\s+gli\b': "negli",
        r'\bin\s+le\b': "nelle",
        r'\bsu\s+il\b': "sul",
        r'\bsu\s+lo\b': "sullo",
        r'\bsu\s+la\b': "sulla",
        r'\bsu\s+i\b': "sui",
        r'\bsu\s+gli\b': "sugli",
        r'\bsu\s+le\b': "sulle",
        r'\bcon\s+il\b': "col",
        r'\bcon\s+i\b': "coi",
        }
    testo_corretto = testo #Mantengo una copia

    #Cerca variabile testo_corretto le corrispondenze della ragex e le sostituisce con la versione corretta
    for chiave, valore in contrazioni.items():
        testo_corretto = re.sub(chiave, valore, testo_corretto, flags =re.IGNORECASE)

    #Pulizia degli spazi
    testo_corretto = re.sub(r'\s+', ' ', testo_corretto) # Rimuove il doppio spazio
    testo_corretto = re.sub(r'\s+([.,!?;:])', r'\1', testo_corretto) # Rimuove lo spazio prima della punteggiatura
    testo_corretto = re.sub(r'([.,!?;:])([a-zA-Z])', r'\1 \2', testo_corretto) # Aggiunge lo spazio dopo la punteggiatura per lettere
    testo_corretto = re.sub(r'([.,!?;:])([0-9])', r'\1 \2', testo_corretto) # Aggiunge lo spazio dopo la punteggiatura per cifre

    return testo_corretto

#Funzione che serve a verificare coerenza del titolo e descrizione ticket
def valida_coerenza_ticket(titolo, descrizione, categoria, categorie):
    combina_testo = (titolo + " " + descrizione).lower() #Titolo e descrizione in minuscolo
    info_categoria = categorie[categoria] #Acquisisce le liste da categoria
    parole_chiave = info_categoria.get("parole_chiave", []) #Estraggo la lista delle parole chiave
    parole_correlate = info_categoria.get("parole_correlate",[]) #Estraggo la lista delle parole correlate
   
    parole_count = 0 # Contatore per parole chiave e correlate
    for parola, sinonimi in parole_correlate.items():
        if parola.lower() in combina_testo:
            parole_count += 1 #Incrementa il contatore
        for sinonimo in sinonimi:
            if sinonimo.lower() in combina_testo:
                parole_count +=1

    if len(descrizione.strip()) < 20: #Nel caso in cui la lunghezza del testo è minore di 20 caratteri (senza spazi)
        return False
    if "{" in titolo or "{" in descrizione:
        return False

    return parole_count >= 1

# Funzione riassegnazione priorità ticket
def assegna_priorita(titolo, descrizione, priorita_originale):
    return priorita_originale

# Funzione per verifica e correzione delle categorie associate ai ticket
def reclassifica_categoria(titolo, descrizione, categoria_iniziale, categorie):
    combina_testo = (titolo + " " + descrizione).lower()
    punto_coerenza = {} # Dizionario per punteggi categoria

    for categoria in categorie.keys():
        info_categorie = categorie[categoria]
        totale = list(info_categorie.get("parole_chiave", []))

        parole_correlate = []

        # Itera sul dizionario delle parole correlate e i suoi sinonimi
        for parola, sinonimi in info_categorie.get("parole_correlate", {}).items():
            parole_correlate.extend(sinonimi) # aggiunge sinonimi in lista
        totale.extend(parole_correlate) # aggiunge le parole correlate alla lista

        # Conta parole chiave nel testo del ticket (titolo e descrizione) e salva punteggio
        punto_categoria = sum(1 for kw in totale if kw.lower() in combina_testo)
        punto_coerenza[categoria] = punto_categoria
   
    # Cerca la categoria con più punti, la salva e salva anche quella iniziale
    miglior_categoria = max(punto_coerenza, key = punto_coerenza.get)
    punto_max = punto_coerenza[miglior_categoria]
    punto_originale = punto_coerenza[categoria_iniziale]

    # Se la categoria migliore è diversa da quella iniziale ed ha almeno 2 punti in più la uso, altrimenti torna quella inziale
    if miglior_categoria != categoria_iniziale and punto_max >= punto_originale + 2:
        return miglior_categoria
    return categoria_iniziale

def genera_varianti_ticket(titolo, descrizione, categoria, categorie):
    # Prima variante: ticket originale
    variante1 = {
        'titolo': titolo,
        'descrizione': descrizione,
        'tipo_variante': 'originale'
    }

    # Seconda variante: sostituzione di una parola correlata
    variante2_titolo = titolo
    variante2_descrizione = descrizione

    if categoria in categorie and 'parole_correlate' in categorie[categoria]:
        parole_correlate_categoria = categorie[categoria]['parole_correlate']
        parole_disponibili = list(parole_correlate_categoria.items()) # Scelta casuale di una parola da sostituire
        if parole_disponibili:
            parola_originale, lista_parole_correlate = random.choice(parole_disponibili)
            if lista_parole_correlate:
                sostituzione = random.choice(lista_parole_correlate)
                if parola_originale.lower() in variante2_titolo.lower(): # Prova a sostituire la parola nel titolo
                    variante2_titolo = re.sub(
                        re.escape(parola_originale),
                        sostituzione,
                        variante2_titolo,
                        count=1,
                        flags=re.IGNORECASE
                    )
                elif parola_originale.lower() in variante2_descrizione.lower(): #prova nella descrizione
                    variante2_descrizione = re.sub(
                        re.escape(parola_originale),
                        sostituzione,
                        variante2_descrizione,
                        count=1,
                        flags=re.IGNORECASE
                    )
    variante2 = {
        'titolo': variante2_titolo,
        'descrizione': variante2_descrizione,
        'tipo_variante': 'parole correlate'
    }
    return [variante1, variante2]
if __name__ == '__main__':
    try:
        categorie = carica_categorie()
        ticket_generati = genera_dataset_sintetico(
            categorie,
            TICKET_PER_CATEGORIA
        )
        print(f"{len(ticket_generati)} ticket generati")
        cat_count = {}
        for tk in ticket_generati:
            cat_count[tk['category']] = cat_count.get(tk['category'], 0) + 1
        print("Ticket per categoria:", {k: v for k, v in cat_count.items()})
        prio_count = {}
        for tk in ticket_generati:
            prio_count[tk["priority"]] = prio_count.get(tk["priority"], 0) + 1
        print("Ticket per priorità:", {k: v for k, v in prio_count.items()})
        print("")
        print("Sono stati generati n. 4 file .csv, contenenti:")
        print("dataset_ticket_mix.csv: 498 righe, l'elenco completo dei ticket mescolati")
        print("dataset_ticket_train.csv: 398 righe, corrispondenti all'80% del totale per addestramento")
        print("dataset_ticket_valid.csv: 50 righe, corrispondenti al 10% del totale per validazione")
        print("dataset_ticket_test.csv: 50 righe, corrispondenti al 10% del totale per test")
        print("")
        # Esporta i CSV
        esporta_dataset(ticket_generati)
    except Exception as e:
        print(f"Errore: {e}")