import os.path
import customtkinter as ctk
import wikipedia
import urllib.request
from PIL import Image


class PictureApi(ctk.CTkLabel):
	def __init__(self, title: str, master=None):
		super().__init__(master)
		self.configure(height=150, width=150)
		self.title = title.replace(".", "").strip()

		# Si la photo n'existe pas aller la chercher
		if not os.path.exists(f"pictures/{self.title.replace(" ", "_")}.jpg"):
			try:
				self.download_picture()
			except ValueError:
				self.configure(text="Aucune image n'est disponible", wraplength=120, text_color="black")
				return

		# Ouvrir l'image
		image = Image.open(f"pictures/{self.title.replace(" ", "_")}.jpg")
		image = ctk.CTkImage(image, size=(150, 150))
		self.configure(image=image, text="")

	def download_picture(self):
		page = wikipedia.page(title=self.title)  # Obtenir la page associée
		images = page.images  # Obtenir les images de la page

		for img in images:  # Prendre la première image qui possède le nom du titre
			if self.title.replace(" ", "_") in img and "jpg" in img:
				image = img
				break
		else:
			raise ValueError("Aucune image n'est disponible")

		urllib.request.urlretrieve(image, f"pictures/{self.title.replace(" ", "_")}.jpg")  # Enregistre l'image dans le fichier
