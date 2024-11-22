# Groupe-Widget de recherche et ses fonctionnalités
from typing import TYPE_CHECKING

from filters import FiltreRecherche

if TYPE_CHECKING:
    from main import MainApp

import math
import pandas as pd
import difflib
import customtkinter as ctk
import tkinter as tk
from widget import StarCheckbox


# Classe principale
class SearchWidget(ctk.CTkFrame):
    def __init__(self, data, master: 'MainApp' = None):
        super().__init__(master)
        self.master: 'MainApp' = master

        self.content = tk.StringVar()
        self.content.trace("w", self.on_text_change)
        self.after_id = None
        self.load_delay = 250  # ms

        self.data: pd.DataFrame = data.drop(columns='type_observation', errors='ignore').reset_index(drop=True)
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

        # Filtres
        self.filtre_frame = None
        self.filtres = None
        self.filtre_current = {"date": {'min': int(data['date'].min()[:4]), 'max': int(data['date'].max()[:4])}, "plan_eau": [], "region": []}
        self.filtre_bouton = None
        self.filtre_reset = None

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

            self.filtre_bouton.configure(state=tk.NORMAL)

            # Filtre les résultats selon le texte entré
            min_sim_ratio = 0.8  # ratio minimal de similitude des deux strings
            m_rechercher = self.search_data.map(
                lambda x: text.lower() in x.lower() or difflib.SequenceMatcher(a=x.lower(), b=text.lower()).quick_ratio() >= min_sim_ratio)
            m_date = self.data['date'].apply(lambda x: self.filtre_current['date']['min'] <= int(x[:4]) <= self.filtre_current['date']['max'])
            m_eau = self.data['nom_plan_eau'].isin(self.filtre_current['plan_eau'])
            m_region = self.data['region'].isin(self.filtre_current['region'])
            results = self.data[m_rechercher.any(axis=1) & m_date & (m_eau if self.filtre_current['plan_eau'] else True) & (
                m_region if self.filtre_current['region'] else True)].reset_index(drop=False)
            self.results_data = self.data.iloc[results['index']].reset_index(drop=False)

            self.nb_page = math.ceil(self.results_data.shape[0] / self.nb_res_par_page)
            self.current_page = 1

            if self.results_data.empty:
                self.filtre_bouton.configure(state=tk.DISABLED)

        list_results = []

        start = (self.current_page - 1) * 7
        for i, row in self.results_data[start:].iterrows():
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

        # Bouton pour ouvrir les filtres
        self.filtre_frame = ctk.CTkFrame(self, bg_color="white", fg_color="white")
        self.filtre_frame.pack(side=tk.TOP)
        self.filtre_bouton = ctk.CTkButton(self.filtre_frame, text="Filtres",
                                           command=lambda: FiltreRecherche(self.data, master=self, callback=self.filtre_callback), bg_color="white",
                                           fg_color="#1faab5", hover_color="#19828a",text_color="#150a05",text_color_disabled="#3f6f3f")
        self.filtre_bouton.pack()
        self.filtre_bouton.configure(state=tk.DISABLED)

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
        self.search(text="")

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
            res_label = ResultLabel(info=result, display=self.displayresult, carte=self.master.carte, callback_fav=self.modify_favoris,
                                    master=self.resultats)
            self.label_collection.append(res_label)
            self.label_collection[i].pack(side=tk.TOP, fill="x", expand=True)

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

    def modify_favoris(self, line_id, state):
        self.results_data.at[self.results_data[self.results_data['index'] == line_id].index[0], 'favoris'] = state
        self.data.at[line_id, 'favoris'] = state
        self.master.data.at[line_id, 'favoris'] = state

    def filtre_callback(self, filtres):
        if not self.filtre_reset:
            self.filtre_reset = ctk.CTkButton(self.filtre_frame, text="Réinitialiser", command=self.reset_filtres, bg_color="white", fg_color="#1f6aa5",
                                              text_color="snow")
            self.filtre_reset.pack()
        if not filtres['region']:
            filtres['region'] = []
        if not filtres['plan_eau']:
            filtres['plan_eau'] = []
        self.filtre_current = filtres
        self.search(text=self.content.get())

    def reset_filtres(self):
        self.filtre_current = {"date": {'min': int(self.data['date'].min()[:4]), 'max': int(self.data['date'].max()[:4])}, "plan_eau": [],
                               "region": []}
        self.search(text=self.content.get())
        self.filtre_reset.destroy()


# Classe de un label résultat
class ResultLabel(ctk.CTkFrame):
    def __init__(self, info, display, carte, callback_fav=None, master=None):
        super().__init__(master)
        self.master = master
        self.callback_fav = callback_fav
        self.display = display
        self.carte = carte
        self.info = info

        title = ctk.CTkLabel(self, text=info['nom_commun'], text_color="black", font=("Helvetica", 15, "bold"))
        subtitle = ctk.CTkLabel(self, text=info['especes'], text_color="gray25", font=("Helvetica", 12, "italic"))
        text = info['region'] + " - " + info['date']
        text = ctk.CTkLabel(self, text=text, text_color="black", font=("Helvetica", 10, "italic"))
        title.grid(row=0, column=0, pady=(4, 0), columnspan=2)
        subtitle.grid(row=1, column=0, columnspan=2)
        text.grid(row=2, column=0, pady=(0, 4), columnspan=2)

        etoile = StarCheckbox(self, default=info['favoris'], callback=self.on_star_click, size=30)
        etoile.grid(row=1, column=1, padx=5)

        self.grid_columnconfigure(0, weight=1)
        self.configure(bg_color="white", fg_color="transparent", border_color="black", border_width=2)

        for child in self.winfo_children():
            if not isinstance(child, StarCheckbox):
                child.bind("<ButtonRelease-1>", command=lambda event: self.on_res_click(self.info))
            child.bind("<Enter>", self.on_hover)
            child.bind("<Leave>", self.on_leave)
        self.bind("<ButtonRelease-1>", lambda event: self.on_res_click(self.info))
        self.bind("<Enter>", self.on_hover)
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
        self.configure(border_color="maroon", border_width=3)

    def on_leave(self, event):
        self.configure(border_color="black", border_width=2)

    def on_star_click(self, event):
        if self.callback_fav:
            self.callback_fav(self.info['index'], event)
