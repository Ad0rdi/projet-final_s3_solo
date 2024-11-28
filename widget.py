import tkinter as tk

class StarCheckbox(tk.Canvas):
    def __init__(self, master=None,default=False, size=50,callback=None, **kwargs):
        super().__init__(master, highlightthickness=0,width=size, height=size, **kwargs)
        self.size = size
        self.checked = default
        self.star_id = None
        self.callback = callback
        self.bind("<Button-1>", self.toggle)
        self.draw_star()

    def draw_star(self):
        points = [
            self.size * 0.5, self.size * 0.1,
            self.size * 0.6, self.size * 0.4,
            self.size * 0.9, self.size * 0.4,
            self.size * 0.65, self.size * 0.6,
            self.size * 0.75, self.size * 0.9,
            self.size * 0.5, self.size * 0.7,
            self.size * 0.25, self.size * 0.9,
            self.size * 0.35, self.size * 0.6,
            self.size * 0.1, self.size * 0.4,
            self.size * 0.4, self.size * 0.4
        ]
        color = "yellow" if self.checked else "white"
        self.star_id = self.create_polygon(points, outline="black", fill=color, width=2)

    def toggle(self, event): #Callback du click
        self.checked = not self.checked
        fill_color = "yellow" if self.checked else "white"
        self.itemconfig(self.star_id, fill=fill_color)
        if self.callback: self.callback(self.checked)

    def get(self): #Permet de récupérer la valeur du checkbox
        return self.checked

    def set(self, value): #Permet de changer la valeur du checkbox
        self.checked = value
        self.draw_star()