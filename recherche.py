# Groupe-Widget de recherche et ses fonctionnalités
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import MainApp

import math
import pandas as pd
import difflib
import customtkinter as ctk
import tkinter as tk


# Classe principale
class SearchWidget(ctk.CTkFrame):
    def __init__(self, data, master: 'MainApp' = None):
        super().__init__(master)
        self.master: 'MainApp' = master

        self.content = tk.StringVar()
        self.content.trace("w", self.on_text_change)
        self.after_id = None
        self.load_delay=250 # ms

        self.data = data.drop(columns='type_observation', errors='ignore').reset_index(drop=True)
        self.search_data = self.data[['nom_commun', 'especes']]
        self.results_data = None
        self.label_collection = []

        # Variables de pagination
        self.nb_page = 1
        self.current_page = 1
        self.nb_res_par_page = 7

        self.configure(height=self.master.winfo_screenheight() - 200, width=5, bg_color="white", fg_color="white")
        self.label_page = None
        self.display_label = None
        self.resultats = None

        # buttons
        self.button_left = None
        self.button_right = None

        self.create_widgets()

    def on_text_change(self, *args):
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.after_id = self.after(self.load_delay, self.search, self.content.get())

    # Fonction qui recherche dans le dataframe
    def search(self, text=None, ):

        # Si la recherche est lancée à partir d'un changement de texte, relancer la recherche à partir du début du dataframe.
        if text is not None:  # Si pas de texte, c'est qu'on change de page
            self.results_data = pd.DataFrame(columns=self.data.columns)
            text = text.strip()
            if text == "" or text == "Rechercher":
                self.label_page.configure(text="-")
                self.resultats.destroy()
                self.frame()
                self.button_left.configure(state=tk.DISABLED)
                self.button_right.configure(state=tk.DISABLED)
                return

            #Filtre les résultats selon le texte entré
            min_sim_ratio = 0.8  # ratio minimal de similitude des deux strings
            masque = self.search_data.map(lambda x: text.lower() in x.lower() or difflib.SequenceMatcher(a=x.lower(), b=text.lower()).quick_ratio() >= min_sim_ratio )
            results = self.search_data[masque.any(axis=1)].reset_index(drop=False)
            self.results_data = self.data.iloc[results['index']]

            self.nb_page = math.ceil(self.results_data.shape[0] / self.nb_res_par_page)
            self.current_page = 1

        list_results = []

        start = (self.current_page - 1) * 7
        for i, row in self.results_data[start:].iterrows():
            # print(nb, ";", i, " : ", row['nom_commun'], " - ", row['especes'])
            list_results.append(row)
            if len(list_results) >= self.nb_res_par_page:
                break
        self.display(list_results)

    # Création des widgets
    def create_widgets(self):
        self.grid(row=0, column=0, padx=20, pady=5, sticky="n")
        self.pack_propagate(False)

        # Label recherche
        top_label = ctk.CTkLabel(self, text="Rechercher :                    ", bg_color="white", text_color="black")
        top_label.pack(side=tk.TOP)

        # Entry du champ de recherche
        champ = ctk.CTkEntry(self, textvariable=self.content, bg_color="white", text_color="black", fg_color="white")
        champ.pack()

        # Crée le frame de résultats
        self.frame()

        # Frame du menu pour changer de page
        pagemenu = ctk.CTkFrame(self, bg_color="white", fg_color="white")
        pagemenu.pack(side=tk.BOTTOM)

        # Bouton pour retourner au début
        self.button_left = ctk.CTkButton(pagemenu, text="<-", command=self.bt_gauche, width=30)
        self.button_left.grid(row=0, column=0, sticky="n", padx=20)

        # Bouton pour aller à la page suivante
        self.button_right = ctk.CTkButton(pagemenu, text="->", command=self.bt_droite, width=30)
        self.button_right.grid(row=0, column=2, sticky="n", padx=20)

        # Label qui affiche le numéro de page
        self.label_page = ctk.CTkLabel(pagemenu, text="1", bg_color="white", fg_color="white", text_color="black")
        self.label_page.grid(row=0, column=1, sticky="n", padx=5)

        # Label qui affiche infos supplémentaires
        self.display_label = ctk.CTkLabel(self.master, text="", compound="left", justify="left", anchor="w", fg_color="white")
        self.display_label.configure(text="Date : AAAA-MM-JJ\nPlan d'eau :\nRégion : \nLatitude : Y, Longitude X\nNom latin :\nEspèce :",
                                     bg_color="white", text_color="black")
        self.display_label.grid(row=0, column=1, sticky="n", padx=5)

    # Fonction d'affichage des résultats
    def display(self, results):
        # Rafraîchissement
        self.master.carte.del_waypoint()
        self.resultats.destroy()

        text_page = str(self.current_page) + "/" + str(self.nb_page)
        self.label_page.configure(text=text_page)


        if self.current_page < self.nb_page:
            self.button_right.configure(state=tk.ACTIVE)
        else:
            self.button_right.configure(state=tk.DISABLED)

        if self.current_page > 1:
            self.button_left.configure(state=tk.ACTIVE)
        else:
            self.button_left.configure(state=tk.DISABLED)

        self.label_collection = []
        self.frame()

        # #Crée un widget label pour chacun des résultats
        for i, result in enumerate(results):
            res_label = ResultLabel(info=result, display=self.displayresult, carte=self.master.carte, master=self.resultats)
            self.label_collection.append(res_label)
            self.label_collection[i].pack(side=tk.TOP, fill="x")

    # Fonction qui crée le frame des résultats
    def frame(self):
        self.resultats = ctk.CTkFrame(self, width=280, height=1000, bg_color="white", fg_color="white")
        self.resultats.pack_propagate(False)
        self.resultats.pack(expand=1, fill="both")

    # Fonction event callback du bouton gauche
    def bt_gauche(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.search()

    # Fonction event callback du bouton droite
    def bt_droite(self):
        if self.nb_page == "..." or self.current_page < self.nb_page:
            self.current_page += 1
            self.search()

    # Fonction qui rafraîchit le dataframe
    def reload_data(self):
        self.data = self.master.data.drop(columns='type_observation', errors='ignore').reset_index(drop=True)
        self.search_data = self.data[['nom_commun', 'especes']]

    # Fonction qui affiche les informations détaillées du résultat cliqué dans le label
    def displayresult(self, line):
        tab = ""
        tab += "Date : " + str(line['date']) + "\n"
        tab += "Plan d'eau : " + str(line['nom_plan_eau']) + "\n"
        tab += "Région : " + str(line['region']) + "\n"
        tab += "Latitude : " + str(line['latitude']) + ", Longitude : " + str(line['longitude']) + "\n"
        tab += "Groupe : " + str(line['groupe']) + "\n"
        tab += "Nom latin : " + str(line['especes']) + "\n"
        tab += "Espèce : " + str(line['nom_commun'])
        self.display_label.configure(text=tab, text_color="black")


# Classe de un label résultat
class ResultLabel(ctk.CTkFrame):
    def __init__(self, info, display, carte, master=None):
        super().__init__(master)
        self.master = master
        self.display = display
        self.carte = carte
        self.info = info

        title = ctk.CTkLabel(self, text=info['nom_commun'], text_color="black", font=("Helvetica", 15, "bold"))
        subtitle = ctk.CTkLabel(self, text=info['especes'], text_color="gray25", font=("Helvetica", 12, "italic"))
        text = info['region'] + " - " + info['date']
        text = ctk.CTkLabel(self, text=text, text_color="black", font=("Helvetica", 10, "italic"))
        title.grid(row=0, column=0, pady=(4, 0))
        subtitle.grid(row=1, column=0)
        text.grid(row=2, column=0, pady=(0, 4))

        self.grid_columnconfigure(0, weight=1)
        self.configure(bg_color="white", fg_color="transparent", border_color="black", border_width=2)

        for child in self.winfo_children():
            child.bind("<ButtonRelease-1>", command=lambda event: self.on_res_click(self.info))
            child.bind("<Enter>", self.on_hover)
            child.bind("<Leave>", self.on_leave)
        self.bind("<Enter>", self.on_hover) # for testing
        self.bind("<Leave>", self.on_leave)

    def on_res_click(self, line):
        self.display(line)
        try:
            lon = float(line['longitude'])
            lat = float(line['latitude'])
        except TypeError:
            self.carte.del_waypoint()
            return
        self.carte.set_waypoint(lon, lat)

    def on_hover(self, event):
        # self.configure(bg_color="gray75")
        self.configure(border_color="maroon", border_width=3)
    def on_leave(self, event):
        # self.configure(bg_color="white")
        self.configure(border_color="black", border_width=2)
