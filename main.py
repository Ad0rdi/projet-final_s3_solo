#Le fichier main

import customtkinter as ctk
import tkinter as tk

class MainApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+{-10}+{0}")
        self.state("zoomed")
        self.title("Application pêche invasive")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()