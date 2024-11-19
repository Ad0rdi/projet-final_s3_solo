import pandas as pd
from fonction import popup

def create_dataframe(file_path):
    """Crée un dataframe à partir d'un fichier .csv"""
    data= pd.read_csv(file_path,delimiter=",",encoding='latin1')
    data = data.drop(columns=['type_observation','references','code_observation'], errors='ignore')
    data = data.dropna()
    if 'favoris' not in data.columns:
        data = data.assign(favoris=False)
    return data

def save_dataframe(data, file_path):
    """Sauvegarde un dataframe dans un fichier .csv"""
    while True:
        try:
            data.to_csv(file_path, sep=",", index=False, encoding='latin1')
            break
        except Exception as e:
            popup("Erreur", "Erreur lors de la sauvegarde des données\nFermez le fichier de données avant de continuer")
