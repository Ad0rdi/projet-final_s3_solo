
import matplotlib.pyplot as plt
from customtkinter import CTkFrame, CTkFont
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from quebec_info import region_info

from fonction import getDistanceFromLatLonInKm
import pandas as pd
import customtkinter as ctk


class GraphEvolution(CTkFrame):
	def __del__(self):
		plt.close('all')

	def __init__(self, data: pd.DataFrame, center: tuple[float, float] = None, radius: float = None,
				 region_id: int = None, master=None):
		super().__init__(master)
		self.configure(bg_color="white", fg_color="white")

		wanted_data = pd.DataFrame(columns=data.columns)
		if ((center and radius) is not None) and region_id is None:  # Si on a un centre et un rayon
			x, y = center
			for i in range(0, data.shape[0]):  # Pour chaque ligne du dataframe vérifie si la distance est inférieure au rayon
				element = data.iloc[i]
				lon, lat = element["longitude"], element["latitude"]
				dist = getDistanceFromLatLonInKm(x, y, lon, lat)
				if dist and dist <= radius:
					wanted_data.loc[len(wanted_data)] = element

		elif region_id is not None and (center is None and radius is None):  # Si on a un id de région
			region = region_info[region_id]
			for i in range(0, data.shape[0]):  # Pour chaque ligne du dataframe vérifie si la région est la bonne
				element = data.iloc[i]
				if element["region"] == region:
					wanted_data.loc[len(wanted_data)] = element

		else:  # Si le match n'est pas possible afficher une erreur
			raise ValueError("Nécessite un centre et un rayon ou un id de région")
		self.data = wanted_data
		self.create_graph()

	# Fonction pour créer le graphique
	def create_graph(self):
		plt.close('all')
		plt.figure(figsize=(5, 4))

		data = {key: 0 for key in self.data['nom_commun'].unique()} # Créer un dictionnaire avec les espèces comme clé

		for line in self.data['nom_commun']:  # Compte le nombre d'occurences de chaque espèce
			data[line] += 1
		if not data:
			text = ctk.CTkLabel(self, text="Aucune donnée à afficher pour cette région", font=CTkFont(size=20), text_color="black")
			text.pack(expand=True)
			return

		# Graphique en camembert pour afficher le nombre d'occurences de chaque espèce
		plt.pie(data.values(), labels=[value for value in data.keys()])
		plt.legend([f"{key} : {value}" for key, value in data.items()], bbox_to_anchor=(1.15, 1), loc='upper left')
		plt.title('Nombre d\'observation des espèces dans la région sélectionnée')

		canvas = FigureCanvasTkAgg(plt.gcf(), master=self)
		canvas.draw()
		canvas.get_tk_widget().pack(fill="both", expand=1)


# Test
if __name__ == "__main__":
	from dataframe import create_dataframe

	app = ctk.CTk()
	app.geometry(f"{app.winfo_screenwidth()}x{app.winfo_screenheight()}+{0}+{0}")
	app.title("Application pêche invasive")
	datas = create_dataframe("BD_EAE_faunique_Quebec.csv")

	# from_region = GraphEvolution(datas, 1, app)

	# Test graph_from_radius
	# GraphEvolution(data=datas, center=(45.5, -73.5),radius=5, master=app)
	#
	# Test graph_from_region
	# GraphEvolution(data=datas, region_id=9, master=app)
	#
	app.mainloop()
