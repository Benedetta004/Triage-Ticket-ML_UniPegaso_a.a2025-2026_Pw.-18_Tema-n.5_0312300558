import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import joblib
import pandas as pd
import re
from sklearn.metrics import accuracy_score, f1_score

# Correzione di alcuni caratteri che possono comparire nel testo
def correggi_testo(testo):
    if not testo:
        return testo
    x = {
        "Ã¨": "è",
        "Ã¬": "ì",
        "Ã²": "ò",
        "Ã¹": "ù",
        "Ã ": "à",
        "Ã€": "À",
        "Ãˆ": "È",
        "Ã’": "Ò",
        "Ã™": "Ù",
        "â‚¬": "€",
        "Â": ""
    }

    for sbagliato, corretto in x.items():
        testo = testo.replace(sbagliato, corretto)

    y = {
        "â€™": "'",
        "â8017": "'",
        "â80": "'",
        "â\x80\x99": "'"
    }

    for sbagliato, corretto in y.items():
        testo = testo.replace(sbagliato, corretto)

    testo = testo.replace("'", " ")
    testo = re.sub(r'\s+', ' ', testo)
    testo = testo.strip()

    return testo


class Dashboard(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title(
            "Progettazione e sviluppo di un sistema per lo smistamento automatizzato delle e-mail in un’azienda di personalizzazione. Baruzzi Benedetta Marcella. Matricola: 0312300558")
        self.geometry("1000x800")
        self.minsize(1000, 800)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.csv_path = None

        self.header()
        self.centro()
        self.log_area()

    # Parte superiore della dashboard
    def header(self):

        header = ttk.Frame(self, padding=20)
        header.grid(row=0, column=0, sticky='ew')

        title = ttk.Label(
            header,
            text="SISTEMA DI SMISTAMENTO AUTOMATIZZATO DI TICKET",
            font=('Arial', 18, 'bold')
        )
        title.pack(pady=10)

        subtitle = ttk.Label(
            header,
            text="Classificazione automatica della categoria e della priorità tramite Machine Learning",
            font=('Arial', 10)
        )
        subtitle.pack()

    # Parte centrale della dashboard
    def centro(self):

        centro = ttk.Frame(self, padding=20)
        centro.grid(row=1, column=0, sticky='nsew')

        centro.columnconfigure(0, weight=1, uniform="col")
        centro.columnconfigure(1, weight=1, uniform="col")
        centro.rowconfigure(0, weight=1)

        # Ticket singolo
        self.singolo_frame = ttk.LabelFrame(centro,text="TICKET SINGOLO",padding=15)
        self.singolo_frame.grid(row=0,column=0,sticky='nsew',padx=(0, 10),pady=10)

        self.singolo_frame.columnconfigure(1, weight=1)
        self.singolo_frame.rowconfigure(1, weight=3)

        # Batch CSV
        self.batch_frame = ttk.LabelFrame(centro,text="BATCH CSV",padding=15)
        self.batch_frame.grid(row=0,column=1,sticky='nsew',padx=(10, 0),pady=10)
        self.batch_frame.columnconfigure(0, weight=1)

        self.singolo_ticket()
        self.batch_ticket()

    # Inserimento e previsione di un ticket singolo
    def singolo_ticket(self):
        ttk.Label(self.singolo_frame,text="Titolo:").grid(row=0,column=0,sticky='nw',pady=5)
        self.titolo_entry = ttk.Entry(self.singolo_frame,font=('Consolas', 10))
        self.titolo_entry.grid(row=0,column=1,sticky='ew',pady=5,padx=(5, 0))

        ttk.Label(self.singolo_frame,text="Descrizione:").grid(row=1,column=0,sticky='nw',pady=5)
        self.descr_text = tk.Text(self.singolo_frame,height=8,font=('Consolas', 10))
        self.descr_text.grid(row=1,column=1,sticky='nsew',pady=5,padx=(5, 0))

        btn_frame = ttk.Frame(self.singolo_frame)
        btn_frame.grid(row=2,column=0,columnspan=2,pady=10)

        ttk.Button(btn_frame,text="OTTIENI PREVISIONE",command=self.classifica).pack(side='right')

        # Risultati
        ris_frame = ttk.LabelFrame(self.singolo_frame,text="RISULTATI",padding=10)

        ris_frame.grid(row=3,column=0,columnspan=2,sticky='ew',pady=10)

        ris_frame.columnconfigure(1, weight=1)

        ttk.Label(ris_frame,text="Categoria prevista:").grid(row=0,column=0,sticky='w',pady=2)

        self.cat_label = ttk.Label(ris_frame,text="-",font=('Consolas', 9, 'bold'))

        self.cat_label.grid(row=0,column=1,sticky='w',pady=2)

        ttk.Label(ris_frame,text="Priorità prevista:").grid(row=1,column=0,sticky='w',pady=2)

        self.prio_label = ttk.Label(ris_frame,text="-",font=('Consolas', 9, 'bold'))

        self.prio_label.grid(row=1,column=1,sticky='w',pady=2)

        ttk.Label(ris_frame,text="Confidenza:").grid(row=2,column=0,sticky='w',pady=2)

        self.conf_label = ttk.Label(ris_frame,text="-",font=('Consolas', 9, 'bold'))

        self.conf_label.grid(row=2,column=1,sticky='w',pady=2)

    # Parte dedicata al caricamento del CSV
    def batch_ticket(self):
        ttk.Label(self.batch_frame,text="Carica CSV").grid(row=0,column=0,sticky='w',pady=10)

        btn_csv = ttk.Button(self.batch_frame,text="SCEGLI CSV",command=self.seleziona_csv)
        btn_csv.grid(row=1,column=0,pady=10,sticky='ew')

        self.csv_label = ttk.Label(self.batch_frame,text="Nessun file selezionato",foreground="gray")
        self.csv_label.grid(row=2,column=0,sticky='w',pady=5)

        btn_batch = ttk.Button(self.batch_frame,text="PREVEDI BATCH",command=self.lavora_batch)
        btn_batch.grid(row=3,column=0,pady=10,sticky='ew')

        # Risultati batch
        self.risultati_batch_frame = ttk.LabelFrame(self.batch_frame,text="RISULTATI BATCH",padding=8)
        self.risultati_batch_frame.grid(row=4,column=0,sticky='ew',pady=10)
        self.risultati_batch_frame.columnconfigure(1, weight=1)

        # Stato
        self.stato_batch = ttk.Label(self.risultati_batch_frame,text="Pronto",foreground="green",font=('Consolas', 9, 'bold'))

        self.stato_batch.grid(row=0,column=0,columnspan=2,pady=(0, 5))

        # Numero ticket
        ttk.Label(self.risultati_batch_frame,text="Ticket:").grid(row=1,column=0,sticky='w',pady=2)
        self.num_ticket_label = ttk.Label(self.risultati_batch_frame,text="-")
        self.num_ticket_label.grid(row=1,column=1,sticky='w',pady=2)

        # Accuracy categoria
        ttk.Label(self.risultati_batch_frame,text="Cat.Acc:").grid(row=2,column=0,sticky='w',pady=2)
        self.acc_cat_label = ttk.Label(self.risultati_batch_frame,text="-")
        self.acc_cat_label.grid(row=2,column=1,sticky='w',pady=2)

        # F1 categoria
        ttk.Label(self.risultati_batch_frame,text="Cat.F1:").grid(row=3,column=0,sticky='w',pady=2)
        self.f1_cat_label = ttk.Label(self.risultati_batch_frame,text="-")
        self.f1_cat_label.grid(row=3,column=1,sticky='w',pady=2)

        # Accuracy priorità
        ttk.Label(self.risultati_batch_frame,text="Pri.Acc:").grid(row=4,column=0,sticky='w',pady=2)
        self.acc_prio_label = ttk.Label(self.risultati_batch_frame,text="-")
        self.acc_prio_label.grid(row=4,column=1,sticky='w',pady=2)

        # F1 priorità
        ttk.Label(self.risultati_batch_frame,text="Pri.F1:").grid(row=5,column=0,sticky='w',pady=2)
        self.f1_prio_label = ttk.Label(self.risultati_batch_frame,text="-")
        self.f1_prio_label.grid(row=5,column=1,sticky='w',pady=2)

    # Area dove vengono visualizzati i messaggi
    def log_area(self):
        log_frame = ttk.LabelFrame(self,text="Log e Metriche",padding=15)
        log_frame.grid(row=2,column=0,sticky='nsew',padx=20,pady=10)

        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame,height=12,font=('Consolas', 9),state='disabled')

        self.log_text.grid(row=0,column=0,sticky='nsew')

        scrollbar = ttk.Scrollbar(log_frame,orient='vertical',command=self.log_text.yview)
        scrollbar.grid(row=0,column=1,sticky='ns')

        self.log_text.config(yscrollcommand=scrollbar.set)

    # Scrive un messaggio nell'area Log
    def scrivi_log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"{msg}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    # Carica i due modelli addestrati
    # Carica i due modelli addestrati
    def carica_modelli(self):
        print("Caricamento modelli...")
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            file_categoria = os.path.join(
                base_path,
                "Logistic_Regression_definitiva_categorie.pkl"
            )
            file_priorita = os.path.join(
                base_path,
                "Logistic_Regression_definitiva_priorita.pkl"
            )
            modello_categoria = joblib.load(file_categoria)
            modello_priorita = joblib.load(file_priorita)
            print("Modelli caricati correttamente.")
            return modello_categoria, modello_priorita

        except FileNotFoundError as errore:
            self.scrivi_log(f"File pkl mancante: {errore}")
            return None, None

    # Classificazione del ticket singolo
    def classifica(self):
        try:
            titolo = self.titolo_entry.get().strip()
            descrizione = self.descr_text.get("1.0",tk.END).strip()
            categoria, priorita, proba = self.ticket_singolo(titolo,descrizione)

            self.cat_label.config(text=categoria)
            self.prio_label.config(text=priorita)
            self.conf_label.config(text=f"{proba:.1%}")
            self.scrivi_log(f"{categoria}/{priorita} | {proba:.1%}")

        except Exception as e:
            self.scrivi_log(f"Errore classificazione: {e}")

    # Selezione del file CSV
    def seleziona_csv(self):
        messagebox.showinfo(
            "Requisiti CSV", 
            "Il file CSV deve contenere le due colonne obbligatorie:\n"
            "'title' e 'body'"
        )

        filename = filedialog.askopenfilename(
            title="Seleziona file CSV",
            filetypes = [
                ("File CSV", "*.csv"),
                ("Tutti i file", "*.*")
            ]
        )
        print("PERCORSO SELEZIONATO:", repr(filename))

        if filename:
            self.csv_path = filename

            try:
                df_preview = pd.read_csv(filename,nrows=3)
                total_rows = len(pd.read_csv(filename))
                colonne_obbligatorie = ['title', 'body']
                mancanti = [
                    col
                    for col in colonne_obbligatorie
                    if col not in df_preview.columns
                ]
                if mancanti:
                    messagebox.showwarning("Colonne Mancanti",f"Mancano: {mancanti}")
                    self.csv_label.config(text="File non valido",foreground='red')

                    return
                self.csv_label.config(
                    text=f"{os.path.basename(filename)} ({total_rows} righe)",
                    foreground='black'
                )
                self.scrivi_log(
                    f"File CSV caricato: {total_rows} ticket | "
                    f"Colonne: {list(df_preview.columns)}"
                )

            except Exception as e:
                self.scrivi_log(f"Errore lettura CSV: {e}")
            else:
                messagebox.showwarning(
                    "CSV non caricato",
                    "Non è stato selezionato alcun file CSV."
                )
                self.scrivi_log("CSV non caricato.")

    # Previsione batch dei ticket
    def lavora_batch(self):
        if not self.csv_path:
            messagebox.showerror("Errore","Selezionare un file CSV.")
            return
        try:
            self.stato_batch.config(text="Caricamento in corso...",foreground='black')
            df = pd.read_csv(self.csv_path)
            # Controllo delle colonne
            colonne_obbligatorie = ['title', 'body']
            mancanti = [
                col
                for col in colonne_obbligatorie
                if col not in df.columns
            ]

            if mancanti:
                raise ValueError(
                    f"Nel file non risultano presenti le colonne: "
                    f"{mancanti}. Necessarie 'title' e 'body'."
                )
            self.scrivi_log(f"Batch: {len(df)} ticket da elaborare.")
            self.stato_batch.config(text="Predizione in corso...")

            # Caricamento dei modelli
            modello_categoria, modello_priorita = self.carica_modelli()
            if modello_categoria is None or modello_priorita is None:
                raise ValueError("Modelli non caricati.")

            # Unione di titolo e descrizione
            df['testo'] = (df['title'].fillna('').astype(str)+ ' '+ df['body'].fillna('').astype(str))

            # Correzione e pulizia del testo
            testi_puliti = df['testo'].apply(correggi_testo).str.lower().tolist()
            # Predizione categoria
            categoria_pred = modello_categoria.predict(testi_puliti)
            # Predizione priorità
            priorita_pred = modello_priorita.predict(testi_puliti)

            df['categoria_pred'] = categoria_pred
            df['priorita_pred'] = priorita_pred

            # Salvataggio del nuovo CSV
            output_path = filedialog.asksaveasfilename(
                title="Salvataggio file con predizioni",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=os.path.basename(self.csv_path).replace('.csv','_predizioni.csv')
            )

            if not output_path:
                self.scrivi_log("Salvataggio file annullato dall'utente.")
                self.stato_batch.config(text="Salvataggio annullato.",foreground='red')
                return

            df.to_csv(output_path,index=False,encoding='utf-8-sig')
            self.scrivi_log(f"File CSV salvato in: {output_path}")

            # Calcolo delle metriche
            metriche = {}
            if 'category' in df.columns:
                metriche['Accuracy_categoria'] = accuracy_score(
                    df['category'],
                    df['categoria_pred']
                )

                metriche['F1-Score_categoria'] = f1_score(
                    df['category'],
                    df['categoria_pred'],
                    average='macro'
                )

            if 'priority' in df.columns:
                metriche['Accuracy_priorita'] = accuracy_score(
                    df['priority'],
                    df['priorita_pred']
                )
                metriche['F1-Score_priorita'] = f1_score(
                    df['priority'],
                    df['priorita_pred'],
                    average='macro'
                )

            if 'Accuracy_categoria' in metriche:
                self.acc_cat_label.config(text=f"{metriche['Accuracy_categoria']:.1%}")
                self.scrivi_log(f"Categoria - Accuracy:{metriche['Accuracy_categoria']:.1%}")

            if 'F1-Score_categoria' in metriche:
                self.f1_cat_label.config(text=f"{metriche['F1-Score_categoria']:.1%}")
                self.scrivi_log(f"Categoria - F1 macro:{metriche['F1-Score_categoria']:.1%}")

            if 'Accuracy_priorita' in metriche:
                self.acc_prio_label.config(text=f"{metriche['Accuracy_priorita']:.1%}")
                self.scrivi_log(f"Priorità - Accuracy: {metriche['Accuracy_priorita']:.1%}")

            if 'F1-Score_priorita' in metriche:
                self.f1_prio_label.config(text=f"{metriche['F1-Score_priorita']:.1%}")
                self.scrivi_log(f"Priorità - F1 macro: {metriche['F1-Score_priorita']:.1%}")
            self.scrivi_log("Batch completato.")
        except Exception as e:
            self.stato_batch.config(text="Errore nel batch.",foreground='red')
            self.scrivi_log(f"Errore batch: {e}")
            messagebox.showerror("Errore Batch",str(e))

    # Previsione di un singolo ticket
    def ticket_singolo(self, titolo, descrizione):
        modello_categoria, modello_priorita = self.carica_modelli()
        if modello_categoria is None or modello_priorita is None: 
            return "Errore_pkl", "Errore_pkl", 0.0

        # Unione di titolo e descrizione
        corpus_ticket = correggi_testo(titolo + ' ' + descrizione)
        corpus_ticket = corpus_ticket.lower().strip()

        if not corpus_ticket:
            return "Testo_Mancante", "N/A", 0.0

        # Predizione della categoria
        categoria = modello_categoria.predict([corpus_ticket])[0]
        # Predizione della priorità
        priorita = modello_priorita.predict([corpus_ticket])[0]
        # Calcolo della confidenza
        probabilita = modello_priorita.predict_proba([corpus_ticket])[0]
        confidenza = max(probabilita)
        return categoria, priorita, confidenza

if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()