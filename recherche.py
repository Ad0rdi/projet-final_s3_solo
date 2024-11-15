#Groupe-Widget de recherche et ses fonctionnalités
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import MainApp

import customtkinter as ctk
import tkinter as tk

#Classe principale
class SearchWidget(ctk.CTkFrame):
    def __init__(self, data, master:'MainApp'=None):
        super().__init__(master)
        self.master:'MainApp' = master

        self.content = tk.StringVar()
        self.content.trace("w", lambda name, index,mode, var=self.content: self.changed(var))
        self.datasearch = data.drop(columns=['habitat','type_observation'], errors='ignore').to_numpy()
        self.label_collection = []
        self.text = ""
        self.x = 0
        self.y = 0
        self.max = False
        self.nb_page = 1
        self.configure(height=self.master.winfo_screenheight()-200,width=5, bg_color="white",fg_color="white")
        self.label_page=None
        self.display_label = None
        self.resultats = None

        #buttons
        self.button_left = None
        self.button_right = None

        self.create_widgets()

    #Fonction qui recherche dans le dataframe
    def search(self, text, side):
        results=[]

        if self.text!="" and self.text!=" ": #S'assure qu'il y a une entrée dans le champ
            if side==0: #Si la recherche est lancée à partir d'un changement de texte, relancer la recherche à partir du début du dataframe
                self.x=0
                self.y=0
                self.nb_page = 1
                self.max = False

            if side>=0: #Si la recherche se fait en avant
                i = 0
                #self.y=0
                for line in self.datasearch[self.y:]: #Parcoure chaque colonne du dataframe
                    i+=1
                    j = 0
                    for case in line: #Parcoure chaque case de la colonne
                        case = str(case) #Transforme en string pour le upper()
                        j+=1
                        if text.upper() in case.upper(): #Si la recherche se trouve dans la case
                            results.append(line)
                            if len(results)>=20: #Limite à 20 résultats
                                self.x+=j
                                self.y+=i
                                self.display(results)
                                return

                self.max = True     
                self.display(results)

    #Fonction event callback du widget entry qui réagit quand le texte change
    def changed(self, event):
        self.text = event.get()
        if self.text!="" and self.text!=" ": self.search(self.text, 0) #S'assure qu'il y a une entrée dans le champ
        else:
            self.label_page.configure(text="-")
            self.max = True 
            self.resultats.destroy()
            self.frame()

    #Création des widgets
    def create_widgets(self):
        self.grid(row=0, column=0, padx=20, pady=5, sticky="n")
        self.pack_propagate(False)
        
        #Label recherche
        top_label = ctk.CTkLabel(self, text = "Rechercher :                    ", bg_color="white",text_color="black")
        top_label.pack(side=tk.TOP)

        #Entry du champ de recherche
        champ = ctk.CTkEntry(self, placeholder_text="Rechercher", textvariable=self.content, bg_color="white",text_color="black",fg_color="white")
        champ.pack()

        #Crée le frame de résultats
        self.frame()

        #Frame du menu pour changer de page
        pagemenu = ctk.CTkFrame(self, bg_color="white",fg_color="white")
        pagemenu.pack(side=tk.BOTTOM)

        #Bouton pour retourner au début
        self.button_left = ctk.CTkButton(pagemenu, text="|<-", command=self.gauche, width=30)
        self.button_left.grid(row=0, column=0, sticky="n", padx=20)

        #Bouton pour aller à la page suivante
        self.button_right = ctk.CTkButton(pagemenu, text="->", command=self.droite, width=30)
        self.button_right.grid(row=0, column=2, sticky="n", padx=20)

        #Label qui affiche le numéro de page
        self.label_page = ctk.CTkLabel(pagemenu, text = "1", bg_color="white", fg_color="white", text_color="black")
        self.label_page.grid(row=0, column=1, sticky="n", padx=5)

        #Label qui affiche infos supplémentaires
        self.display_label = ctk.CTkLabel(self.master, text="", compound="left", justify="left", anchor="w", fg_color="white")
        self.display_label.configure(text="Date : AAAA-MM-JJ\nPlan d'eau :\nRégion : \nLatitude : Y, Longitude X\nNom latin :\nEspèce :", bg_color="white", text_color="black")
        self.display_label.grid(row=0, column=1, sticky="n", padx=5)

    #Fonction d'affichage des résultats
    def display(self, results):
        #Rafraîchissement
        self.master.carte.del_waypoint()
        self.resultats.destroy()
        if not self.max:
            self.label_page.configure(text=self.nb_page)
            self.button_right.configure(state=tk.ACTIVE)
        else: 
            self.label_page.configure(text="Max")
            self.button_right.configure(state=tk.DISABLED)

        self.label_collection=[]
        self.frame()

        #Crée un widget label pour chacun des résultats
        for i, result in enumerate(results):
            for j, case in enumerate(result):
                 if str(self.text).upper() in str(case).upper():
                    res_label = ResultLabel(smalltext=result[j], bigtext = result, display=self.displayresult,carte=self.master.carte, master=self.resultats)
                    self.label_collection.append(res_label)
                    self.label_collection[i].pack(expand=True,side=tk.TOP)

    #Fonction qui crée le frame des résultats
    def frame(self):
        self.resultats = ctk.CTkFrame(self, width=280, height=1000, border_width=2, border_color="black", bg_color="white",fg_color="gray75")
        self.resultats.pack_propagate(False)
        self.resultats.pack(expand=1,fill="both")

    #Fonction event callback du bouton gauche
    def gauche(self):
        if self.nb_page>1:
            self.nb_page = 1
            self.max = False
            self.search(self.text, 0)

    #Fonction event callback du bouton droite
    def droite(self):
        if not self.max:
            self.nb_page +=1
            self.search(self.text, 1)

    #Fonction qui rafraîchit le dataframe
    def reloadData(self):
        self.datasearch = self.master.data.drop(columns=['habitat','type_observation']).to_numpy()

    #Fonction qui affiche les informations détaillées du résultat cliqué dans le label
    def displayresult(self, line):
        tab = ""
        tab += "Date : "+ str(line[0])+ "\n"
        tab += "Plan d'eau : "+ str(line[1])+ "\n"
        tab += "Région : "+ str(line[2])+ "\n"
        tab += "Latitude : "+ str(line[3])+ ", Longitude : "+ str(line[4])+"\n"
        tab += "Groupe : "+ str(line[5])+"\n"
        tab += "Nom latin : "+ str(line[6])+ "\n"
        tab += "Espèce : "+ str(line[7])
        self.display_label.configure(text=tab, text_color="black")

#Classe de un label résultat
class ResultLabel(ctk.CTkLabel):
    def __init__(self, smalltext, bigtext, display,carte, master=None):
        super().__init__(master)
        self.master = master
        self.display = display
        self.carte=carte
        self.smalltext = smalltext
        self.bigtext = bigtext

        self.configure(text=smalltext, fg_color="white", width=197,text_color="black")
        self.bind("<ButtonRelease-1>", command=lambda event:self.on_res_click(self.bigtext))

    def on_res_click(self, line):
        self.display(line)
        try:
            line4=float(line[4])
            line3 = float(line[3])
        except TypeError:
            self.carte.del_waypoint()
            return
        self.carte.set_waypoint(line4,line3)
