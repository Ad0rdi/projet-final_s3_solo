# Fichier pour la pseudo carte
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import MainApp

import customtkinter as ctk
import tkinter as tk
from tkinter.constants import HORIZONTAL
import fiona
import shapely
from shapely.geometry import shape, Polygon, MultiPolygon, Point
from functools import partial

from graph_evolution import GraphEvolution
from quebec_info import region_info

color = ["blue", "darkorange", "indigo", "yellow", "purple", "orange", "brown", "pink", "teal", "plum", "coral", "orchid",
         "lime", "skyblue", "navy", "darkgreen", "yellowgreen"]

poly_id_to_reg = {0: 11, 1: 2, 2: 10, 3: 17, 4: 14, 5: 7, 6: 15, 7: 16, 8: 8, 9: 6, 10: 5, 11: 13, 12: 1, 13: 12, 14: 4,
                  15: 3, 16: 9, 17: 9, 18: 9}


class PseudoCarte(ctk.CTkFrame):
    """
    Affiche une carte de la région de Québec Autocentrée et redimensionnable
    La carte apparait au premier mouvement de la souris
    Appeler *rezoom()* peu aider à afficher la carte en début
    *save_simple_map()* comme qualité maximal de la carte
    """

    def __init__(self, data, master:'MainApp'=None):
        super().__init__(master)
        self.master:'MainApp'=master
        self.data = data
        self.graph = None
        self.canvas = ctk.CTkCanvas(self,bg="#d0e4f5",)
        self.canvas.pack(expand=True, fill='both')

        # Les polygones de la carte
        self.real_polygons = []
        self.poly_color = []
        self.poly_region = []
        self.simplified_map = []
        self.poly_id = []

        # waypoint
        grandeur = 25
        circle = Point(0, -grandeur * 2.5).buffer(grandeur)
        triangle = Polygon([(-grandeur / 2, -grandeur * 2), (grandeur / 2, -grandeur * 2), (0, 0)])
        self.waypoint = circle.union(triangle)
        self.waypoint_color = "red"
        self.waypoint_pos = None

        # Les limites de la carte (pour le scaling)
        self.max_x = -56.934926885456164
        self.min_x = -79.76532426607646
        self.max_y = 62.58246570128598
        self.min_y = 44.99135832579372

        # Calcule scale et offset des polygones
        self.scale = 1
        self.min_scale = 1
        self.max_scale = 1
        self.offset_x = 0
        self.offset_y = 0
        self.move_center = ()

        # Position du clic
        self.x = "Non précisé"
        self.y = "Non précisé"
        self.region = "Inconnue"

        # type de clic (region/rayon)
        self.click_frame = ctk.CTkFrame(self, fg_color="white",border_color="black",border_width=2)
        self.click_frame.place(x=170, y=90, anchor='c')
        self.click_var = tk.StringVar(value="Info")
        self.click_info = ctk.CTkRadioButton(self.click_frame, text="Information par région", variable=self.click_var, value="Info",text_color="black")
        self.click_info.grid(row=0, column=0, sticky='ew', padx=5,pady=5)
        self.click_label = ctk.CTkLabel(self.click_frame, text="Type de clic pour le graphique", font=ctk.CTkFont(size=12),text_color="black")
        self.click_label.grid(row=1, column=0, sticky='w', padx=5,pady=5)
        self.click_region = ctk.CTkRadioButton(self.click_frame, text="Par region", variable=self.click_var,
                                               value="Region",text_color="black")
        self.click_region.grid(row=2, column=0, sticky='ew',padx=5,pady=5)
        self.click_frame_rayon = ctk.CTkFrame(self.click_frame, fg_color="white")
        self.click_frame_rayon.grid(row=3, column=0, sticky='ew', padx=5,pady=5)
        self.click_rayon = ctk.CTkRadioButton(self.click_frame_rayon, text="Par rayon (km)", variable=self.click_var,
                                              value="Rayon",text_color="black")
        self.click_rayon.grid(row=0, column=0, sticky='nsew')
        self.click_rayon_radius = tk.IntVar(value=1)
        self.click_rayon_size = tk.Scale(self.click_frame_rayon, from_=1, to=200, orient=HORIZONTAL,
                                         variable=self.click_rayon_radius, length=150)
        self.click_rayon_size.grid(row=0, column=1, sticky='nsew')
        self.click_radius_id = None
        self.click_radius_old = 1

        with fiona.open("quebec_region_SHP/simplified_map.shp") as data:
            for feature in data:
                recent_poly = []

                geom = shape(feature['geometry'])
                if isinstance(geom, Polygon):
                    exterior_coords = list(geom.exterior.coords)
                    recent_poly.append(exterior_coords)
                    self.poly_color.append(color[int(feature['properties']['RES_CO_REG']) - 1])
                    self.poly_region.append(feature['properties']['RES_CO_REG'])
                elif isinstance(geom, MultiPolygon):
                    for poly in geom.geoms:
                        exterior_coords = list(poly.exterior.coords)
                        recent_poly.append(exterior_coords)
                        self.poly_color.append(color[int(feature['properties']['RES_CO_REG']) - 1])
                        self.poly_region.append(feature['properties']['RES_CO_REG'])

                # créer les polygones
                for poly in recent_poly:
                    self.real_polygons.append(Polygon(poly))

        self.save_simple_map()
        self.master.bind("<KeyPress>", self.key_pressed)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Motion>", self.moved)
        self.canvas.bind("<B1-Motion>", self.begin_drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

    def begin_drag(self, event):
        self.canvas.unbind("<B1-Motion>")
        self.canvas.bind("<B1-Motion>", self.drag)
        self.move_center = (event.x, event.y)

    def drag(self, event):
        x, y = self.move_center[0], self.move_center[1]
        diff_x, diff_y = event.x - x, event.y - y
        for ids in self.canvas.find_all():
            self.canvas.move(ids, diff_x, diff_y)
        self.move_center = (event.x, event.y)
        self.offset_x += diff_x
        self.offset_y += diff_y

    def end_drag(self, event):
        self.canvas.unbind("<B1-Motion>")
        self.canvas.bind("<B1-Motion>", self.begin_drag)
        self.move_center = ()

    def moved(self, event):
        # Pour afficher la carte en début si elle est pas déjà là
        self.rezoom()
        self.canvas.unbind("<Motion>")

    def key_pressed(self, event):
        if event.char == "c":
            self.rezoom()

    def rezoom(self):
        """Rezoom la carte pour qu'elle soit centrée et remplisse l'écran"""
        # Calcule agrandissement et déplacement des polygones
        scale_x = self.canvas.winfo_width() / (self.max_x - self.min_x)
        scale_y = self.canvas.winfo_height() / (self.max_y - self.min_y)
        self.scale = min(scale_x, scale_y) * 0.8  # Marge de bordure
        self.min_scale = self.scale
        self.max_scale = 1120
        self.offset_x = (self.canvas.winfo_width() - (self.max_x - self.min_x) * (self.scale-(self.scale*0.35))) / 2
        self.offset_y = (self.canvas.winfo_height() - (self.max_y - self.min_y) * self.scale) / 2
        self.draw()

    def save_simple_map(self):
        """Sauvegarde une version simplifiée de la carte"""
        self.simplified_map = []
        for i, poly in enumerate(self.real_polygons):
            self.simplified_map.append(poly.simplify(0.001))

    def on_scroll(self, event):
        scale_facteur = 1.1 if event.delta > 0 else 0.9
        if not (self.min_scale <= self.scale * scale_facteur <= self.max_scale):
            return

        # Calculer le changement de offset_x et offset_y
        self.offset_x = (self.offset_x - event.x) * scale_facteur + event.x
        self.offset_y = (self.offset_y - event.y) * scale_facteur + event.y

        # Appliquer la mise à l'échelle
        self.canvas.scale('all', event.x, event.y, scale_facteur, scale_facteur)
        self.scale *= scale_facteur

    def move_poly(self, poly, scale=None):
        if not scale:
            scale = self.scale
        points = []
        for x, y in poly.exterior.coords:
            # Agrandir et placer les polygones
            px = (x - self.min_x) * (scale - (scale * 0.35)) + self.offset_x
            py = (self.max_y - y) * scale + self.offset_y
            points.append((px, py))
        return points

    def draw(self):
        """Afficher la carte"""
        self.canvas.delete("all")
        for i, poly in enumerate(self.simplified_map):
            points = self.move_poly(poly)
            polygon_id = self.canvas.create_polygon(points, fill=self.poly_color[i], outline="black", width=2)
            self.canvas.tag_bind(polygon_id, "<ButtonRelease-1>", self.on_polygon_click)

        if self.waypoint_pos:
            points = []
            x, y = self.waypoint_pos
            x = (float(x)  - self.min_x) * (self.scale - (self.scale * 0.35)) + self.offset_x
            y = (self.max_y - float(y)) * self.scale + self.offset_y
            for point in self.waypoint.exterior.coords:
                px, py = point
                px += float(x)
                py += float(y)
                points.append((px, py))

            ids = self.canvas.create_polygon(points, fill=self.waypoint_color, outline="white", width=5)
            self.canvas.tag_bind(ids, "<ButtonRelease-1>", self.on_polygon_click)
            ids = self.canvas.create_polygon(points, fill=self.waypoint_color, outline="black", width=2)
            self.canvas.tag_bind(ids, "<ButtonRelease-1>", self.on_polygon_click)

    def on_polygon_click(self, event):
        if not self.move_center:
            self.x, self.y = self.screen_pos_to_lon_lat(event.x, event.y)
            region_id, self.region = self.region_from_coords(coords=(self.x, self.y))
            if region_id:
                if self.click_var.get() == "Info":
                    show_popup(region_id)
                    return
                self.canvas.update()
                if self.click_var.get() == "Region":
                    self.graph = partial(GraphEvolution, data=self.data, region_id=region_id)
                elif self.click_var.get() == "Rayon":
                    self.graph_by_radius(event)
                self.master.show_graph()

    def graph_by_radius(self,event):
        x, y = event.x,event.y
        x, y = self.screen_pos_to_lon_lat(x, y)
        self.graph = partial(GraphEvolution, data=self.data, center=(x, y), radius=self.click_rayon_radius.get())

    def set_waypoint(self, lon, lat):
        self.waypoint_pos = (lon, lat)
        self.draw()

    def del_waypoint(self):
        self.waypoint_pos = None
        self.draw()

    def screen_pos_to_lon_lat(self, x, y):
        lon = ((x - self.offset_x) / (self.scale - (self.scale * 0.35))) + self.min_x
        lat = -(((y - self.offset_y) / self.scale) - self.max_y)
        return lon, lat

    def region_from_coords(self, coords):
        """Renvoie la région administrative et son nom à partir de coordonnées"""
        x,y = coords
        for i, poly in enumerate(self.real_polygons):
            if poly.contains(shapely.Point(x,y)):
                region = self.poly_region[i]
                return region, region_info[region]
        return None

    def get_graph_function(self):
        return self.graph


def show_popup(poly_region):
    popup = tk.Toplevel()
    popup.title("Information région")
    popup.geometry(f"500x200+{popup.winfo_screenwidth() // 2 - 100}+{popup.winfo_screenheight() // 2 - 100}")

    title = tk.Label(popup,
                     text = f"{region_info[poly_region]}",
                     font = ("Arial", 20))
    title.pack(pady=20,side='top')

    label = tk.Label(popup,
                     text=f"Tu as cliqué sur la région administrative #{poly_region}",
                     font=("Arial", 12))
    label.pack(pady=20,side='top')

    close_button = tk.Button(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=10)