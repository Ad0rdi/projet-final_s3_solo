# Filtres pour la recherche
from array import array

import customtkinter as ctk
import tkinter as tk
import pandas as pd
import time
from customtkinter import CTkFrame
from darkdetect import theme

from dataframe import create_dataframe
from fonction import hex_to_rgb, add_colors, darken_color


# Fenêtre de filtre pour la recherche
class FiltreRecherche(ctk.CTkToplevel):
    def __init__(self, data: 'pd.DataFrame', master=None, callback=None):
        super().__init__(master)
        self.overrideredirect(True)  # Enlève les bordures de la fenêtre
        self.configure(fg_color="white")
        self.callback = callback
        self.date = None
        self.plan_eau = None
        self.region = None

        self.create_widgets(data=data)

        self.rezise()

    def rezise(self):
        """Centre la fenêtre dans l'écran"""
        self.geometry((
            f"{self.winfo_reqwidth()}x{self.winfo_reqheight()}+{self.winfo_screenwidth() // 2 - self.winfo_reqwidth() // 2}+{self.winfo_screenheight() // 2 - self.winfo_reqheight() // 2}"))

    def create_widgets(self, data):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=2)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Bouton pour fermer la fenêtre
        quitter = ctk.CTkButton(self, text="x", command=self.destroy, bg_color="transparent", fg_color="salmon",hover_color="#f8321b", text_color="black", width=30,
                                height=30, font=ctk.CTkFont(size=15, family="monospace"))
        quitter.place(relx=1.0, x=-10, y=10, anchor='ne')  # Positionner en haut à droite
        titre = ctk.CTkLabel(self, text="Filtres", font=ctk.CTkFont(size=20), text_color="black")
        titre.grid(row=0, column=0, columnspan=2, pady=10)

        # Création des widgets de filtre
        self.date = TimeRangeSelector(data['date'], self)
        self.date.grid(row=1, column=0, columnspan=2, pady=10)

        self.plan_eau = SelectorFromList(self, data=data['nom_plan_eau'], title="Plans d'eau", theme_color="#80dbf5")
        self.plan_eau.grid(row=2, column=0, pady=10)

        self.region = SelectorFromList(self, data=data['region'], title="Region", theme_color="#51b755")
        self.region.grid(row=2, column=1, pady=10)

        # Bouton pour appliquer les filtres
        apply = ctk.CTkButton(self, text="Appliquer", command=self.filter, bg_color="transparent", fg_color="lightblue", hover_color="#9bc1cd",text_color="black")
        apply.grid(row=3, column=0, columnspan=2, pady=10)

    def filter(self):
        """Applique les filtres et ferme la fenêtre"""
        filters = {
            "date": self.date.get(),
            "plan_eau": self.plan_eau.get(),
            "region": self.region.get()
        }
        self.callback(filters)
        self.destroy()

# Widget de sélection de plage de date
class TimeRangeSelector(ctk.CTkFrame):
    def __init__(self, data, master=None, **kwargs):
        """Crée un widget pour sélectionner une plage de date selon les données passées en paramètre"""
        super().__init__(master, **kwargs)
        self.configure(bg_color="transparent", fg_color="#f58080")

        titre = ctk.CTkLabel(self, text="Date", font=ctk.CTkFont(size=15), text_color="snow")
        titre.pack(side="top")

        sliders = ctk.CTkFrame(self)
        sliders.configure(bg_color="transparent", fg_color="transparent")
        sliders.pack(side="top", pady=10)
        min_value = tk.IntVar(value=data.min()[:4])
        max_value = tk.IntVar(value=data.max()[:4])

        self.slider_min = ctk.CTkSlider(sliders, variable=min_value, from_=min_value.get(), to=max_value.get(), orientation="horizontal",
                                        fg_color="snow", progress_color="white", number_of_steps=max_value.get() - min_value.get(),
                                        command=lambda event: self.update_date_slider(event, "min"))
        self.slider_min.pack(side="top")

        self.slider_max = ctk.CTkSlider(sliders, variable=max_value, from_=min_value.get(), to=max_value.get(), orientation="horizontal",
                                        fg_color="white", progress_color="snow", number_of_steps=max_value.get() - min_value.get(),
                                        command=lambda event: self.update_date_slider(event, "max"))
        self.slider_max.pack(side="bottom")

        self.date_text = ctk.CTkLabel(self, text=f"{int(min_value.get())} - {int(max_value.get())}", font=ctk.CTkFont(size=15), text_color="snow")
        self.date_text.pack(side="top", pady=10)

    def update_date_slider(self, event, qui):
        """Met à jour le texte de la plage de date"""
        if qui == "min" and self.slider_min.get() > self.slider_max.get():
            self.slider_max.set(self.slider_min.get())
        elif qui == "max" and self.slider_max.get() < self.slider_min.get():
            self.slider_min.set(self.slider_max.get())
        self.date_text.configure(text=f"{int(self.slider_min.get())} - {int(self.slider_max.get())}")

    def get(self):
        """Récupère la plage de date sélectionnée"""
        return {"min": self.slider_min.get(), "max": self.slider_max.get()}

# Widget de sélection de liste
class SelectorFromList(ctk.CTkFrame):
    def __init__(self, master=None, data=None, title=None, theme_color="#6e6e6e", **kwargs):
        """Crée un widget pour sélectionner des valeurs dans une liste\nSelon les données passées en paramètre"""
        super().__init__(master, **kwargs)

        self.configure(bg_color="transparent", fg_color=theme_color)
        self.loading=ctk.CTkLabel(self,text="Chargement...",font=ctk.CTkFont(size=15),text_color="snow",bg_color="black")

        if title: # Si un titre est passé en paramètre, l'afficher
            titre = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=15), text_color=darken_color(theme_color, 100))
            titre.pack(side="top")

        self.update_request = None
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Rechercher...", textvariable=self.search_var,
                                         fg_color=add_colors(theme_color, "#606060"), text_color=darken_color(theme_color, 100))
        self.search_entry.pack(side="top", fill="x", padx=10, pady=10)
        self.search_var.trace("w", self.updated)

        # Conteneur pour la liste des valeurs
        self.listbox_frame = ctk.CTkFrame(self, bg_color=theme_color)
        self.listbox_frame.pack(side="top", fill="both", expand=True)

        self.scrollbar = ctk.CTkScrollbar(self.listbox_frame, orientation="vertical")
        self.scrollbar.pack(side="right", fill="y")

        self.switch_frame = ctk.CTkFrame(self.listbox_frame)
        self.switch_frame.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(self.switch_frame, yscrollcommand=self.scrollbar.set, bg=theme_color)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Enter>", self.bind_scroll)
        self.canvas.bind("<Leave>", self.unbind_scroll)
        self.scrollbar.configure(command=self.canvas.yview)

        # Conteneur des choix
        self.inner_frame = ctk.CTkFrame(self.canvas, fg_color=theme_color)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw", width=self.canvas.winfo_reqwidth())

        self.master.rezise()
        self.switches = {}
        self.after(50,self.load_switches, data, theme_color) # Charger les valeurs en arrière plan

    def load_switches(self, data, theme_color,start=0):
        """Charge les valeurs en packets de 10"""
        for i,name in enumerate(sorted(set(data.values))[start:]): # Pour chaque valeur en partant de start
            switch = ctk.CTkSwitch(self.inner_frame, text=name, bg_color=darken_color(theme_color,150),text_color=add_colors(theme_color,"0c0c0c"),state=tk.DISABLED)
            self.switches[name]=switch
            if i>9: # Quand il a plus de 10 valeurs attendre 10 ms avant de charger les prochaines.
                self.after(10,self.load_switches,data,theme_color,start+i+1)
                break
        else: # Quand il n'y a plus de valeurs à charger
            self.loading.destroy() # Enlever le label de chargement
            self.update_list()
            self.master.rezise()
            for switch in self.switches.values(): # Activer les switchs
                switch.configure(state=tk.NORMAL)

        if start <10: # Après avoir chargé les 10 premières valeurs charger les autres en arrirère plan
            self.update_list()
            self.loading.place(x=self.winfo_reqwidth() / 2, y=self.winfo_reqheight() / 2, anchor='center')
            self.loading.tkraise()

    def updated(self, *args): # Met à jour la liste des valeurs lorsque la recherche est modifiée
        if self.update_request:
            self.after_cancel(self.update_request)
        self.after(250, self.update_list)

    def update_list(self): # Met à jour la liste des valeurs selon la recherche
        search_term = self.search_var.get().lower()
        for name, switch in self.switches.items():
            if not switch.get():
                switch.pack_forget()
            if search_term in name.lower():
                switch.pack(side="top", fill="x", padx=10, pady=5)

        self.inner_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def bind_scroll(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def unbind_scroll(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def get(self):
        """Récupère les valeurs qui sont sélectionnées"""
        result = []
        for name, switch in self.switches.items():
            if switch.get():
                result.append(name)
        return result if result else None


# Exemple d'utilisation
if __name__ == "__main__":
    data_frame = create_dataframe("BD_EAE_faunique_Quebec.csv")
    root = ctk.CTk()
    root.geometry("800x600")
    root.configure(bg_color="white")
    FiltreRecherche(data_frame, master=root)
    root.mainloop()
