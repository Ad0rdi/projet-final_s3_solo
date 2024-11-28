# Fichier pour la pseudo carte
from pyproj import Transformer
import customtkinter as ctk
import tkinter as tk
import fiona
import shapely
from shapely.geometry import shape, Polygon, MultiPolygon

"""
Les données pour la carte proviennent du site gouvernemental du Canada
https://ouvert.canada.ca/data/fr/dataset/a883eb14-0c0e-45c4-b8c4-b54c4a819edb/resource/1b0a85fc-272b-49c7-b165-b2ba380c48fe


#### Il faut les télécharger et mettre le dossier "lpr_000b16a_f" dans le même dossier que ce fichier


"""

# Définir le CRS projeté (PROJCS) et le CRS géographique (GEOGCS)
lambert_crs = """
    PROJCS["PCS_Lambert_Conformal_Conic",
    GEOGCS["GCS_North_American_1983",
        DATUM["D_North_American_1983",
            SPHEROID["GRS_1980",6378137.0,298.257222101]],
        PRIMEM["Greenwich",0.0],
        UNIT["Degree",0.0174532925199433]],
    PROJECTION["Lambert_Conformal_Conic"],
    PARAMETER["False_Easting",6200000.0],
    PARAMETER["False_Northing",3000000.0],
    PARAMETER["Central_Meridian",-91.86666666666666],
    PARAMETER["Standard_Parallel_1",49.0],
    PARAMETER["Standard_Parallel_2",77.0],
    PARAMETER["Latitude_Of_Origin",63.390675],
    UNIT["Meter",1.0]]
"""
geo_crs = "EPSG:4326"  # WGS84

# Créer un transformateur
transformer = Transformer.from_crs(lambert_crs, geo_crs, always_xy=True)


class Carte(ctk.CTkFrame):
    """
    Affiche une carte de la région de Canada Autocentrée et redimensionnable
    La carte apparait après 1 seconde
    """

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.canvas = tk.Canvas(self, bg="#d0e4f5")
        self.canvas.pack(expand=True, fill='both')

        # Les polygones de la carte
        self.area_threshold = 500_000_000  # Grandeur minimale d'un polygone
        self.simplification_threshold = 0.05  # Seuil de simplification (un plus gros chiffre = plus simplifié)
        self.real_polygons = []
        self.poly_properties = []
        self.simplified_map = []

        # Les limites de la carte (pour le scaling)
        self.max_x = -52.61940850384606
        self.min_x = -141.01807315762784
        self.max_y = 83.13550252435944
        self.min_y = 41.68143542498606

        # Calcule scale et offset des polygones
        self.scale = 1
        self.min_scale = 1
        self.max_scale = 1120  # Tu vas peut-être devoir changer ça
        self.offset_x = 0
        self.offset_y = 0
        self.move_center = ()

        need_simplify = True  # Si la carte simplifiée doit être enregistrée pour la prochaine fois
        file_to_open = "lpr_000b16a_f/lpr_000b16a_f.shp"

        try:  # Si la carte a déjà été simplifié prendre la prendre
            fiona.open("lpr_000b16a_f/simplified.shp")
            file_to_open = "lpr_000b16a_f/simplified.shp"
            need_simplify = False
        except Exception as e:  # Si la carte n'a pas été simplifié, laisser faire
            pass

        if need_simplify:
            schema = None  # Utile pour la sauvegarde
            with fiona.open(file_to_open) as data:
                schema = data.schema
                for feature in data:
                    recent_poly = []
                    geom = shape(feature['geometry'])

                    if isinstance(geom, Polygon):
                        # Convertir les coordonnées du polygone
                        exterior_coords = [convert_coords(coord) for coord in geom.exterior.coords]
                        if geom.area >= self.area_threshold:  # Si la forme est trop petite, ne pas la garder (surement une île)
                            self.poly_properties.append(feature.properties)  # Garder les propriété pour l'enregistrement
                            recent_poly.append(exterior_coords)
                    elif isinstance(geom, MultiPolygon):
                        for poly in geom.geoms:
                            # Convertir les coordonnées de chaque polygone
                            exterior_coords = [convert_coords(coord) for coord in poly.exterior.coords]
                            if poly.area >= self.area_threshold:  # Si la forme est trop petite, ne pas la garder (surement une île)
                                self.poly_properties.append(feature.properties)  # Garder les propriété pour l'enregistrement
                                recent_poly.append(exterior_coords)

                    # Créer les polygones transformés
                    for poly in recent_poly:
                        self.real_polygons.append(Polygon(poly))

            # Sauvegarde le fichier pour la prochaine fois
            with fiona.open("lpr_000b16a_f/simplified.shp", "w", "ESRI Shapefile", schema=schema, crs=geo_crs) as output:
                for i, poly in enumerate(self.real_polygons):
                    output.write({
                        "type": "Feature",
                        "properties": self.poly_properties[i],
                        "geometry": {"type": "Polygon", "coordinates": [poly.exterior.coords]}
                    })

        else:  # S'il y a déjà une version simplifiée
            with fiona.open(file_to_open) as data:
                for feature in data:
                    recent_poly = []
                    geom = shape(feature['geometry'])

                    if isinstance(geom, Polygon):
                        # Convertir les coordonnées du polygone
                        exterior_coords = geom.exterior.coords
                        recent_poly.append(exterior_coords)
                        self.poly_properties.append(feature.properties)  # Garder les propriétés
                    elif isinstance(geom, MultiPolygon):
                        for poly in geom.geoms:
                            # Convertir les coordonnées de chaque polygone
                            exterior_coords = poly.exterior.coords
                            recent_poly.append(exterior_coords)
                            self.poly_properties.append(feature.properties)  # Garder les propriétés

                    # Créer les polygones transformés
                    for poly in recent_poly:
                        self.real_polygons.append(Polygon(poly))

            # # auto min max pour savoir les vrai min et max qu'il devrai avoir par default
            # for poly in self.real_polygons:
            #     for x, y in poly.exterior.coords:
            #         if x > self.max_x:
            #             self.max_x = x
            #         if x < self.min_x:
            #             self.min_x = x
            #         if y > self.max_y:
            #             self.max_y = y
            #         if y < self.min_y:
            #             self.min_y = y
            #
            # print("Réel min max")
            # print("x", self.min_x, self.max_x)
            # print("y", self.min_y, self.max_y)

        self.save_simple_map()  # Crée une version simplifiée de la carte pour l'affichage
        self.after(1000, self.rezoom)  # Affiche la carte au début
        self.master.bind("<KeyPress>", self.key_pressed)  # 'c' pour recentrer la carte
        self.canvas.bind("<MouseWheel>", self.on_scroll)  # Scroll pour zoomer la carte
        self.canvas.bind("<B1-Motion>", self.begin_drag)  # Déplacer la carte
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)  # Fin du déplacement

    def begin_drag(self, event):
        self.canvas.unbind("<B1-Motion>")
        self.canvas.bind("<B1-Motion>", self.drag)
        self.move_center = (event.x, event.y)

    def drag(self, event):
        x, y = self.move_center[0], self.move_center[1]
        diff_x, diff_y = event.x - x, event.y - y
        self.canvas.move("all", diff_x, diff_y)
        self.move_center = (event.x, event.y)
        self.offset_x += diff_x
        self.offset_y += diff_y

    def end_drag(self, event):
        self.canvas.unbind("<B1-Motion>")
        self.canvas.bind("<B1-Motion>", self.begin_drag)
        self.move_center = ()

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
        self.offset_x = (self.canvas.winfo_width() - (self.max_x - self.min_x) * (self.scale - (self.scale * 0.35))) / 2
        self.offset_y = (self.canvas.winfo_height() - (self.max_y - self.min_y) * self.scale) / 2
        self.draw()

    def save_simple_map(self):
        """Sauvegarde une version simplifiée de la carte"""
        self.simplified_map = []
        for i, poly in enumerate(self.real_polygons):
            self.simplified_map.append(poly.simplify(self.simplification_threshold))

    def on_scroll(self, event):
        scale_facteur = 1.1 if event.delta > 0 else 0.9
        if not (self.min_scale <= self.scale * scale_facteur <= self.max_scale):
            return

        # Calculer le changement de offset_x et offset_y
        self.offset_x = (self.offset_x - event.x) * scale_facteur + event.x
        self.offset_y = (self.offset_y - event.y) * scale_facteur + event.y
        self.scale *= scale_facteur
        self.canvas.scale("all", event.x, event.y, scale_facteur, scale_facteur)  # Scale les objets

    def move_poly(self, poly):
        """Déplace un polygone et le scale et retourne une liste de points"""
        points = []
        for x, y in poly.exterior.coords:
            # Agrandir et placer les polygones
            px = (x - self.min_x) * (self.scale - (self.scale * 0.35)) + self.offset_x
            py = (self.max_y - y) * self.scale + self.offset_y
            points.append((px, py))
        return points

    def draw(self):
        """Afficher la carte"""
        self.canvas.delete("all")
        for i, poly in enumerate(self.simplified_map):  # Crée les polygones
            points = self.move_poly(poly)
            polygon_id = self.canvas.create_polygon(points, fill="white", outline="black", width=2)
            self.canvas.tag_bind(polygon_id, "<ButtonRelease-1>", self.on_polygon_click)

    def on_polygon_click(self, event):
        if not self.move_center:  # Si on ne bouge pas la carte
            x, y = self.screen_pos_to_lon_lat(event.x, event.y)  # Convertir la position de la souris en coordonnées
            nom = self.nom_from_coords(coords=(x, y))  # Trouver la région administrative
            show_popup(nom)  # Affiche les infos

    def screen_pos_to_lon_lat(self, x, y):
        lon = ((x - self.offset_x) / (self.scale - (self.scale * 0.35))) + self.min_x
        lat = -(((y - self.offset_y) / self.scale) - self.max_y)
        return lon, lat

    def nom_from_coords(self, coords):
        """Renvoie la région administrative et son nom à partir de coordonnées"""
        x, y = coords
        for i, poly in enumerate(self.real_polygons):
            if poly.contains(shapely.Point(x, y)):
                nom = self.poly_properties[i]['PRANOM']
                return nom
        return None


def show_popup(nom):
    popup = tk.Toplevel()
    popup.title("Information région")

    title = tk.Label(popup,
                     text=f"Information région #{nom}",
                     font=("Arial", 20))
    title.pack(pady=20, side='top')

    label = tk.Label(popup,
                     text=f"Tu as cliqué sur la région administrative #{nom}",
                     font=("Arial", 12))
    label.pack(pady=20, side='top')

    # Grandeur automatique selon la grandeur du texte
    popup.geometry(
        f"{(len(nom) + 43)*9}x{popup.winfo_reqheight() + 10}+{popup.winfo_screenwidth() // 2 - 100}+{popup.winfo_screenheight() // 2 - 100}")
    close_button = tk.Button(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=10)


def convert_coords(coord):
    """Convertit une coordonnée (x, y) du système PROJCS vers GEOGCS."""
    lon, lat = transformer.transform(coord[0], coord[1])
    return lon, lat


# Exemple d'utilisation
if __name__ == "__main__":
    app = ctk.CTk()
    app.geometry(f"{app.winfo_screenwidth()}x{app.winfo_screenheight()}+{0}+{0}")
    app.title("Carte du canada")

    carte = Carte(master=app)
    carte.pack(expand=True, fill='both')

    app.mainloop()
