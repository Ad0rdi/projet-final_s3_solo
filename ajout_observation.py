#Groupe-Widget d'ajout d'observation et ses fonctionnalités

import customtkinter as ctk
import tkinter as tk
from datetime import date

#Classe principale
class addObsWidget(ctk.CTkFrame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.configure(fg_color="transparent")

        #Initialisation des widgets
        self.mainButton = None
        self.eauNomEntry=None
        self.habitatEntry=None
        self.groupeEntry=None
        self.latinEntry=None
        self.nomEntry=None

        self.create_mainwidget()

    #Création du widget bouton de base
    def create_mainwidget(self):
        self.mainButton = ctk.CTkButton(self, text="Ajouter observation", command=self.clickedAddfirst, width=30)
        self.mainButton.grid(row=0,column=0)

    #Si le bouton est cliqué une première fois
    def clickedAddfirst(self):
        self.create_form()

    #Création des widgets du formulaire
    def create_form(self):
        self.mainButton.destroy()
        self.configure(bg_color="transparent", fg_color="transparent")

        self.eauNomEntry = ctk.CTkEntry(self, placeholder_text="* Nom du plan d'eau",text_color="black",bg_color="transparent",fg_color="white")
        self.eauNomEntry.grid(row=0,column=0)
        self.habitatEntry = ctk.CTkEntry(self, placeholder_text="Type d'habitat",text_color="black",bg_color="transparent",fg_color="white")
        self.habitatEntry.grid(row=1,column=0)
        self.groupeEntry = ctk.CTkEntry(self, placeholder_text="Groupe",text_color="black",bg_color="transparent",fg_color="white")
        self.groupeEntry.grid(row=2,column=0)
        self.latinEntry = ctk.CTkEntry(self, placeholder_text="Nom latin",text_color="black",bg_color="transparent",fg_color="white")
        self.latinEntry.grid(row=3,column=0)
        self.nomEntry = ctk.CTkEntry(self, placeholder_text="* Nom commun",text_color="black",bg_color="transparent",fg_color="white")
        self.nomEntry.grid(row=4,column=0)

        self.mainButton = ctk.CTkButton(self, text="Ajouter observation", command=self.clickedAddsec, width=30, bg_color="transparent")
        self.mainButton.grid(row=5,column=0)

    #Si le bouton est cliqué une seconde fois
    def clickedAddsec(self):
        self.master.carte.click_var.set("Info")

        #Vérification des champs
        if self.eauNomEntry.get()=="":
            self.popup("Erreur", "Veuillez entrer un plan d'eau")
            return
        if self.nomEntry.get()=="":
            self.popup("Erreur", "Veuillez entrer un nom d'espèce")
            return
        
        self.popup("Choisir une localisation", "Veuillez cliquez sur la carte à l'endroit où l'espèce a été observée") #Appel popup localisation
        self.mainButton.configure(command=self.clickedAddthird) #Changer pour attendre un clic après avoir eu la localisation

    #Si le bouton est cliqué une troisième fois
    def clickedAddthird(self):
        #Aller chercher les informations de la carte
        x = self.master.carte.x
        y = self.master.carte.y
        region = self.master.carte.region

        #Ajout de la ligne

        #Plaçage de buffers si jamais ces champs sont vides
        if self.habitatEntry.get()!="": habitat=self.habitatEntry.get()
        else: habitat = "Non spécifié"
        if self.groupeEntry.get()!="": groupe=self.groupeEntry.get()
        else: groupe = "Non spécifié"
        if self.latinEntry.get()!="": latin=self.latinEntry.get()
        else: latin = "Non spécifié"

        #Ajout de la ligne
        self.master.data.loc[len(self.master.data)]=[str(date.today()), self.eauNomEntry.get(), habitat, region, y, x, groupe, latin, self.nomEntry.get(), "Ajouté par utilisateur via Aqua-Inva"]
        try:
            self.master.data.to_csv("BD_EAE_faunique_Quebec.scsv", index=False, sep=';',encoding='latin1') #Sauvegarde
        except ValueError as e : #Si pandas ne peut pas sauvegarder le dataframe dans le csv, ça veut dire que le csv est ouvert ailleurs
            self.popup("Erreur", "Le fichier de données est ouvert ailleurs, veuillez le fermer")
            self.refresh()

        self.popup("Succès!", "L'observation a été ajoutée à la base de données avec succès!")
        self.refresh() #Rafraîchissement

    #Fonction de rafraîchissement
    def refresh(self):
        self.master.search_widget.reloadData() 

        #Rafraîchissement des champs
        self.eauNomEntry.destroy()
        self.habitatEntry.destroy()
        self.groupeEntry.destroy()
        self.latinEntry.destroy()
        self.nomEntry.destroy()

        #Rafraîchissement du bouton
        self.mainButton.destroy()
        self.create_mainwidget()

    #Pour afficher un popup
    def popup(self, title, text):
        popup = tk.Toplevel()
        popup.title(title)
        popup.geometry(f"{50+len(text)*8}x100+{popup.winfo_screenwidth() // 2}+{popup.winfo_screenheight() // 2}")
        label = tk.Label(popup,text=text, font=("Arial", 12))
        label.pack(pady=20)
        close_button = tk.Button(popup, text="OK", command=popup.destroy)
        close_button.pack(pady=10)
