# main.py
import customtkinter as ctk
import tkinter as tk
from recherche import SearchWidget
from dataframe import create_dataframe, save_dataframe
from pseudo_carte import PseudoCarte
from ajout_observation import addObsWidget

file_path = "BD_EAE_faunique_Quebec.csv"

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()-75}+{-10}+{0}")
        self.configure(fg_color="white")
        self.data = create_dataframe(file_path)
        self.title("Aqua-Inva")
        self.carte = PseudoCarte(data=self.data, master=self)
        self.search_widget = None
        self.addObs = None
        self.graph = None
        self.create_menu()
        self.show_accueil()
        self.rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Sauvegarde les données avant de fermer l'application"""
        save_dataframe(self.data, file_path)
        self.destroy()

    def show_accueil(self):
        self.clear_main_frame()
        self.search_widget = SearchWidget(self.data, master=self)
        self.search_widget.grid(row=0, column=0, padx=10, sticky="nsew")
        self.carte.grid(row=0, column=1, padx=10, sticky="nsew")
        self.addObs = addObsWidget(master=self)
        self.addObs.place(x=1450, y=60, anchor='ne')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=5)
        self.columnconfigure(2, weight=0)

    def show_graph(self):
        self.clear_main_frame()
        graph_func = self.carte.get_graph_function()
        if not graph_func:
            label = ctk.CTkLabel(self, text="Aucune donnée n'a été sélectionnée", font=ctk.CTkFont(size=20),text_color="black")
            label.grid(row=0, column=1, padx=10, sticky="nsew")
            self.columnconfigure(0, weight=1)
            self.columnconfigure(1, weight=1)
            self.columnconfigure(2, weight=1)
            return
        label = ctk.CTkLabel(self, text="Chargement...", font=ctk.CTkFont(size=20),text_color="black")
        label.place(x=self.winfo_width() / 2.5, y=self.winfo_height() / 3, anchor='center')
        self.update()
        graph = graph_func(master=self)
        graph.grid(row=0, column=0, padx=10, sticky="nsew")
        label.destroy()
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)

    def create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)
        menu_bar.add_command(label="Accueil", command=self.show_accueil)
        menu_bar.add_command(label="Graphique", command=self.show_graph)

    def clear_main_frame(self):
        for widget in self.winfo_children():
            if  isinstance(widget, PseudoCarte):
                widget.grid_remove()
            else:
                widget.destroy()
        self.create_menu()

if __name__ == "__main__":
    app = MainApp()
    app.wm_iconbitmap('Aqua-inva_minimalistic.ico')
    app.mainloop()