# Groupe-Widget de recherche et ses fonctionnalités
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # Pour vérifier les types
	from main import MainApp

import math
import difflib
import pandas as pd
import tkinter as tk
import customtkinter as ctk
from widget import StarCheckbox
from filters import FiltreRecherche
from picture_api import PictureApi


# Classe principale
class SearchWidget(ctk.CTkFrame):
	def __init__(self, data, master: 'MainApp' = None):
		super().__init__(master)
		self.master: 'MainApp' = master

		# String de la recherche
		self.content = tk.StringVar()
		self.content.trace("w", self.on_text_change)
		self.after_id = None
		self.load_delay = 250  # ms de délai avant de lancer la recherche

		# Data et résultats
		self.data: pd.DataFrame = data.drop(columns='type_observation', errors='ignore').reset_index(drop=True)
		self.search_data = self.data[['nom_commun', 'especes']]
		self.results_data = None
		self.resultats = None
		self.label_collection = []

		# Variables de pagination
		self.nb_page = 1
		self.current_page = 1
		self.nb_res_par_page = 7
		self.label_page = None

		self.display_label = None
		self.configure(height=self.master.winfo_screenheight() - 200, width=5, bg_color="white", fg_color="white")

		# Buttons
		self.button_left = None
		self.button_right = None

		# Filtres
		self.filtre_frame = None
		self.filtres = None
		self.filtre_current = {"date": {'min': int(data['date'].min()[:4]), 'max': int(data['date'].max()[:4])}, "plan_eau": [],
							   "region": []}  # Filtres actuels pour la recherche
		self.afficher_tout_bouton = None
		self.marqueur_stop = False  # Variable pour arrêter l'affichage des marqueurs
		self.filtre_bouton = None
		self.filtre_reset = None

		self.create_widgets()

	def on_text_change(self, *args):  # Callback du changement de texte
		# Appeler la fonction de recherche si le texte n'a pas changé depuis self.load_delay ms
		if self.after_id is not None:
			self.after_cancel(self.after_id)
		self.after_id = self.after(self.load_delay, self.search, self.content.get())

	# Fonction qui recherche dans le dataframe
	def search(self, text=None, ):  # Calcule les résultats de la recherche

		# Si la recherche est lancée à partir d'un changement de texte, relancer la recherche à partir du début du dataframe.
		if text is not None:  # Si pas de texte, c'est qu'on change de page
			self.results_data = pd.DataFrame(columns=self.data.columns)  # Copie vide du dataframe pour les résultats
			text = text.strip()  # Enlève les espaces inutiles

			self.master.carte.del_marqueur()  # Supprime les marqueurs déjà affichés
			self.marqueur_stop = True  # Arrête l'affichage des marqueurs
			self.afficher_tout_bouton.configure(state=tk.NORMAL)
			self.filtre_bouton.configure(state=tk.NORMAL)

			# Filtre les résultats selon le texte entré
			min_sim_ratio = 0.8  # ratio minimal de similitude des deux strings
			# Chaque m_ est un différent filtre pour les résultats
			m_rechercher = self.search_data.map(
				lambda x: text.lower() in x.lower() or difflib.SequenceMatcher(a=x.lower(), b=text.lower()).quick_ratio() >= min_sim_ratio)
			m_date = self.data['date'].apply(lambda x: self.filtre_current['date']['min'] <= int(x[:4]) <= self.filtre_current['date']['max'])
			m_eau = self.data['nom_plan_eau'].isin(self.filtre_current['plan_eau'])
			m_region = self.data['region'].isin(self.filtre_current['region'])

			# Filtre les résultats selon les filtres actuels
			results = self.data[m_rechercher.any(axis=1) & m_date & (m_eau if self.filtre_current['plan_eau'] else True) & (
				m_region if self.filtre_current['region'] else True)].reset_index(drop=False)
			self.results_data = self.data.iloc[results['index']].reset_index(drop=False)

			self.nb_res_par_page = max(self.resultats.winfo_height() // 120, 1)  # Calcule le nb de résultats par page selon la grandeur
			self.nb_page = math.ceil(self.results_data.shape[0] / self.nb_res_par_page)  # Calcule le nb de pages
			self.current_page = 1

			if self.results_data.empty:  # Si aucun résultat, désactive les boutons de navigation
				self.afficher_tout_bouton.configure(state=tk.DISABLED)
				self.filtre_bouton.configure(state=tk.DISABLED)

		list_results = []

		start = (self.current_page - 1) * self.nb_res_par_page  # Début de la page
		for i, row in self.results_data[start:].iterrows():
			list_results.append(row)
			if len(list_results) >= self.nb_res_par_page:  # Si on a assez de résultats quitter
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

		# Bouton afficher tout
		self.afficher_tout_bouton = ctk.CTkButton(self.filtre_frame, text="Afficher tout", command=self.afficher_tout_resultats, bg_color="white",
												  fg_color="#1faab5", hover_color="#19828a", text_color="#150a05", text_color_disabled="#3f6f3f")
		self.afficher_tout_bouton.pack()
		self.afficher_tout_bouton.configure(state=tk.DISABLED)

		# Bouton filtre
		self.filtre_bouton = ctk.CTkButton(self.filtre_frame, text="Filtres",
										   command=lambda: FiltreRecherche(self.data, master=self, callback=self.filtre_callback), bg_color="white",
										   fg_color="#1faab5", hover_color="#19828a", text_color="#150a05", text_color_disabled="#3f6f3f")
		self.filtre_bouton.pack()
		self.filtre_bouton.configure(state=tk.DISABLED)

		# Crée le frame de résultats
		self.frame()

		# Frame du menu pour changer de page
		page_menu = ctk.CTkFrame(self, bg_color="white", fg_color="white")
		page_menu.pack(side=tk.BOTTOM)

		# Bouton pour aller a la page précédente
		self.button_left = ctk.CTkButton(page_menu, text="<-", command=self.bt_gauche, width=30)
		self.button_left.grid(row=0, column=0, sticky="n", padx=20)

		# Bouton pour aller à la page suivante
		self.button_right = ctk.CTkButton(page_menu, text="->", command=self.bt_droite, width=30)
		self.button_right.grid(row=0, column=2, sticky="n", padx=20)

		# Label qui affiche le numéro de page
		self.label_page = ctk.CTkLabel(page_menu, text="...", bg_color="white", fg_color="white", text_color="black")
		self.label_page.grid(row=0, column=1, sticky="n", padx=5)

		# Label qui affiche infos supplémentaires
		self.display_label = ctk.CTkLabel(self.master, text="", compound="left", justify="left", anchor="w", fg_color="white")
		self.display_label.configure(text="Date : AAAA-MM-JJ\nPlan d'eau :\nRégion : \nLatitude : Y, Longitude X\nNom latin :\nEspèce :",
									 bg_color="white", text_color="black")
		self.display_label.grid(row=0, column=1, sticky="n", padx=5)

		self.after(1_000, self.search, "")  # Lance une recherche vide pour afficher tous les résultats

	# Fonction d'affichage des résultats
	def display(self, results):
		# Rafraîchissement
		self.master.carte.del_waypoint()
		self.resultats.destroy()

		# Affichage du numéro de page
		if self.nb_page == 0:
			text_page = "..."
		else:
			text_page = str(self.current_page) + "/" + str(self.nb_page)
		self.label_page.configure(text=text_page)

		if self.current_page < self.nb_page:  # Si on est pas à la dernière page, on active le bouton de droite
			self.button_right.configure(state=tk.ACTIVE)
		else:
			self.button_right.configure(state=tk.DISABLED)

		if self.current_page > 1:  # Si on est pas à la première page, on active le bouton de gauche
			self.button_left.configure(state=tk.ACTIVE)
		else:
			self.button_left.configure(state=tk.DISABLED)

		self.label_collection = []
		self.frame()

		# Crée un widget label pour chacun des résultats
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
		if self.nb_page != 0 and self.current_page < self.nb_page:
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

	def modify_favoris(self, line_id, state):  # Fonction qui modifie l'état de favoris d'une ligne
		self.results_data.at[self.results_data[self.results_data['index'] == line_id].index[0], 'favoris'] = state
		self.data.at[line_id, 'favoris'] = state
		self.master.data.at[line_id, 'favoris'] = state

	def filtre_callback(self, filtres):  # Fonction qui applique les filtres
		if self.filtre_reset:
			self.filtre_reset.destroy()
		self.filtre_reset = ctk.CTkButton(self.filtre_frame, text="Réinitialiser", command=self.reset_filtres, bg_color="white",
										  fg_color="#1f6aa5",
										  text_color="snow")
		self.filtre_reset.pack()
		if not filtres['region']:
			filtres['region'] = []
		if not filtres['plan_eau']:
			filtres['plan_eau'] = []
		self.filtre_current = filtres
		self.search(text=self.content.get())

	def reset_filtres(self):  # Fonction qui réinitialise les filtres
		self.filtre_current = {"date": {'min': int(self.data['date'].min()[:4]), 'max': int(self.data['date'].max()[:4])}, "plan_eau": [],
							   "region": []}
		self.search(text=self.content.get())
		self.filtre_reset.destroy()

	def afficher_tout_resultats(self, start=0):  # Fonction qui affiche tous les résultats avec des marqueurs sur la carte
		if start == 0:  # Si on est dans la première boucle
			self.master.carte.del_marqueur()  # On supprime les marqueurs déjà affichés
			self.text_marq = ctk.CTkLabel(self.master, text="Affichage de tous les résultats...", font=("Helvetica", 15, "bold"), text_color="black")
			self.text_marq.place(x=self.master.winfo_width() / 2.5, y=self.master.winfo_height() / 3, anchor='center')
			self.text_marq.tkraise()  # Mettre au dessus
			self.marqueur_stop = False  # On autorise l'affichage des marqueurs
			self.afficher_tout_bouton.configure(state=tk.DISABLED)  # Impossible de relancer l'affichage quand il est en cours

		if not self.marqueur_stop:
			for i, result in enumerate(self.results_data[start:].iterrows()):
				lon = result[1]["longitude"]
				lat = result[1]["latitude"]
				self.master.carte.add_marqueur(lon, lat)
				if i > 10:  # Si on a affiché 10 marqueurs, on attend 100ms avant de continuer (pour moins de lag)
					self.after(100, self.afficher_tout_resultats, start + i + 1)
					break
			else:  # Si on a fini d'afficher les marqueurs
				self.text_marq.destroy()
				text = ctk.CTkLabel(self.master, text="Marqueurs chargés", font=("Helvetica", 30, "bold"), text_color="black")
				text.place(x=self.master.winfo_width() / 2.5, y=self.master.winfo_height() / 3, anchor='center')
				text.tkraise()
				self.after(2_000, text.destroy)  # On enlève le texte après 2s (pour que l'utilisateur sache que c'est fini)
				self.afficher_tout_bouton.configure(state=tk.NORMAL)  # On réactive le bouton pour afficher tous les résultats


class DetailLabel(ctk.CTkToplevel):
	def __init__(self, info, master=None):
		super().__init__(master)
		self.overrideredirect(True)
		self.master = master
		self.info = info
		self.title(f"Détails de l'observation : {self.info['nom_commun']} ")
		self.configure(bg_color="white", fg_color="white", borderwidth=2, relief="solid")
		self.create_widgets()

		# Donner la bonne forme et placer au centre
		self.update_idletasks()
		width = self.winfo_reqwidth()
		height = self.winfo_reqheight()
		master = self.master.master.master.master  # On remonte 4 fois pour arriver à la fenêtre principale
		self.geometry(f"{width}x{height}+{master.winfo_width() // 2 - width // 2}+{master.winfo_height() // 2 - height // 2}")

	def create_widgets(self):
		frame = ctk.CTkFrame(self, bg_color="white", fg_color="white")
		frame.pack(expand=True, fill="both")
		frame.columnconfigure(0, weight=2)
		frame.columnconfigure(1, weight=1)
		frame.rowconfigure(0, weight=0)
		frame.rowconfigure(1, weight=1)

		# Titre
		titre = ctk.CTkLabel(frame, text=self.info['nom_commun'], font=("Helvetica", 15, "bold"), bg_color="white", fg_color="snow",
							 text_color="#1f6aa5")
		titre.grid(row=0, column=0, pady=10, padx=10)

		# Fermer l'info
		fermer = ctk.CTkButton(frame, text="Fermer", command=self.destroy, bg_color="white", fg_color="black", width=100)
		fermer.grid(row=0, column=1, pady=10, padx=10, sticky="e")

		# Affichage des informations
		tab = ""
		tab += "Date : " + str(self.info['date']) + "\n"
		tab += "Plan d'eau : " + str(self.info['nom_plan_eau']) + "\n"
		tab += "Région : " + str(self.info['region']) + "\n"
		tab += "Latitude : " + str(self.info['latitude']) + ", Longitude : " + str(self.info['longitude']) + "\n"
		tab += "Groupe : " + str(self.info['groupe']) + "\n"
		tab += "Nom latin : " + str(self.info['especes']) + "\n"
		tab += "Espèce : " + str(self.info['nom_commun'])
		# self.display_label.configure(text=tab, text_color="black")
		label = ctk.CTkLabel(frame, text=tab, text_color="black")
		label.grid(row=1, column=0, pady=10, padx=10)
		image_label = PictureApi(title=self.info['especes'], master=frame)
		image_label.grid(row=1, column=1, pady=10, padx=10)


# Classe de un label résultat
class ResultLabel(ctk.CTkFrame):
	def __init__(self, info, display, carte, callback_fav=None, master=None):
		super().__init__(master)
		self.master = master
		self.callback_fav = callback_fav
		self.display = display
		self.carte = carte
		self.info = info
		self.clicked = False

		title = ctk.CTkLabel(self, text=info['nom_commun'], text_color="black", font=("Helvetica", 15, "bold"),
							 wraplength=130)
		subtitle = ctk.CTkLabel(self, text=info['especes'], text_color="gray25", font=("Helvetica", 12, "italic"),
								wraplength=120)
		text = info['region'] + " - " + info['date']
		text = ctk.CTkLabel(self, text=text, text_color="black", font=("Helvetica", 10, "italic"))
		title.grid(row=0, column=0, pady=(4, 0), columnspan=2)
		subtitle.grid(row=1, column=0, columnspan=2)
		text.grid(row=2, column=0, pady=(0, 4), columnspan=2)

		# Étoile de favoris
		etoile = StarCheckbox(self, default=info['favoris'], callback=self.on_star_click, size=30)
		etoile.grid(row=1, column=1, padx=5)

		# i d'information
		info = ctk.CTkButton(self, text="i", bg_color="white", fg_color="grey75", hover_color="black", text_color="white",
							 command=lambda: DetailLabel(self.info, self), font=("Helvetica", 10, "bold"), corner_radius=10, width=20, height=20)
		info.grid(row=0, column=1, padx=5)

		self.grid_columnconfigure(0, weight=1)
		self.configure(bg_color="white", fg_color="transparent", border_color="black", border_width=2)

		for child in self.winfo_children():
			if not isinstance(child, StarCheckbox):  # Si on clique sur l'étoile, on ne veut pas que ça affiche les infos
				child.bind("<ButtonRelease-1>", command=lambda event: self.on_res_click(self.info))
			child.bind("<Enter>", self.on_hover)
			child.bind("<Leave>", self.on_leave)
		self.bind("<ButtonRelease-1>", lambda event: self.on_res_click(self.info))
		self.bind("<Enter>", self.on_hover)
		self.bind("<Leave>", self.on_leave)

	def on_res_click(self, line):
		#Reset la couleur des autres labels
		for label in self.master.master.label_collection:
			if label!=self:
				label.click(False)
				label.configure(border_color="black", border_width=2)
		self.clicked=True
		self.display(line)
		try:
			lon = float(line['longitude'])
			lat = float(line['latitude'])
		except TypeError:  # Si les coordonnées ne sont pas des nombres, on ne peut pas les afficher
			self.carte.del_waypoint()
			return
		self.carte.set_waypoint(lon, lat)

	def click(self,state):
		self.clicked = state
		if not state:
			self.configure(border_color="black", border_width=2)

	def on_hover(self, event):  # Fonction qui change la couleur du cadre lorsqu'on passe la souris dessus
		self.configure(border_color="maroon", border_width=3)

	def on_leave(self, event):  # Fonction qui remet la couleur du cadre à la normale
		if not self.clicked:
			self.configure(border_color="black", border_width=2)
		else:
			self.configure(border_color="#1419af", border_width=3)

	def on_star_click(self, event):  # Fonction qui appelle le callback de favoris
		if self.callback_fav:
			self.callback_fav(self.info['index'], event)
