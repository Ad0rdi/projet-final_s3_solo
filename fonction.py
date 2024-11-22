import numpy as np
import tkinter as tk
import math

def map_range(x, in_min, in_max, out_min, out_max):
    return out_min + (((x - in_min) / (in_max - in_min)) * (out_max - out_min))

def getDistanceFromLatLonInKm(lat1,lon1,lat2,lon2) :
    R = 6371 # Radius of the earth in km
    dLat = deg2rad(lat2-lat1)  # deg2rad below
    dLon = deg2rad(lon2-lon1)
    a =    math.sin(dLat/2) * math.sin(dLat/2) +    math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) *    math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c # Distance in km
    return d

def deg2rad(deg):
  return deg * (np.pi/180)

def popup(title, text):
    """Affiche une popup avec un message
    Toujours centrée sur l'écran"""
    popup = tk.Toplevel()
    popup.title(title)
    # popup.geometry(f"{50+len(text)*8}x100+{popup.winfo_screenwidth() // 2}+{popup.winfo_screenheight() // 2}")
    label = tk.Label(popup,text=text, font=("Arial", 12))
    label.pack(pady=20)
    close_button = tk.Button(popup, text="OK", command=popup.destroy)
    close_button.pack(pady=10)

    popup.update_idletasks()
    popup.geometry(f"{popup.winfo_reqwidth()}x{popup.winfo_reqheight()}+{popup.winfo_screenwidth() // 2 - popup.winfo_reqwidth() // 2}+{popup.winfo_screenheight() // 2 - popup.winfo_reqheight() // 2}")

    popup.wait_window()

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_color):
    return '#{:02x}{:02x}{:02x}'.format(*rgb_color)

def add_colors(hex_color1, hex_color2):
    rgb1 = hex_to_rgb(hex_color1)
    rgb2 = hex_to_rgb(hex_color2)
    added_rgb = tuple(min(255, c1 + c2) for c1, c2 in zip(rgb1, rgb2))
    return rgb_to_hex(added_rgb)

def darken_color(hex_color, amount=30):
    rgb = hex_to_rgb(hex_color)
    darkened_rgb = tuple(max(0, c - amount) for c in rgb)
    return rgb_to_hex(darkened_rgb)