import pandas as pd
from fonction import popup

def create_dataframe(file_path):
    """Crée un dataframe à partir d'un fichier .csv"""
    data= pd.read_csv(file_path,delimiter=",")
    data = data.drop(columns=['type_observation','references','code_observation'], errors='ignore') # Supprime les colonnes inutiles
    data = data.dropna() # Supprime les lignes avec des valeurs manquantes
    if 'favoris' not in data.columns: #Si le cv est neuf, ajoute la colonne favoris
        data = data.assign(favoris=False)
    return data

def save_dataframe(data, file_path):
    """Sauvegarde un dataframe dans un fichier .csv"""
    while True: # Tant que le fichier est ouvert, demande de le fermer
        try:
            data.to_csv(file_path, sep=",", index=False, encoding='utf-8')
            break
        except Exception as e: # Si le fichier est ouvert, affiche une erreur
            popup("Erreur", "Erreur lors de la sauvegarde des données\nFermez le fichier de données avant de continuer")
