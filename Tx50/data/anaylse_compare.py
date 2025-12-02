import xarray as xr
import numpy as np
import os

# --- Configuration ---
# Le nom de votre fichier NetCDF
FILENAME = "/home/florent/Documents/ENM_3A/Tx50/Tx50/nc_diff_brut_cor/difference_tasmax_txx_IPSL-CM5A-MR_HIRHAM5.nc"
# Le nom de la variable de température à l'intérieur du fichier (souvent 'tasmax' ou 'TMAX')
# Si le code échoue, vérifiez ce nom en affichant la structure (voir l'étape 3)
VARIABLE_NAME = "difference"

def calculer_statistiques(filename, variable_name):
    """
    Charge le fichier NetCDF, calcule les statistiques descriptives
    de la variable spécifiée et affiche les résultats.
    """
    if not os.path.exists(filename):
        print(f"ERREUR: Le fichier '{filename}' n'a pas été trouvé.")
        print("Veuillez vous assurer que le fichier est dans le même répertoire que ce script.")
        return

    try:
        # 1. Chargement et inspection du fichier
        print(f"--- Chargement du fichier {filename} ---")
        ds = xr.open_dataset(filename)
        
        if variable_name not in ds:
            print(f"ERREUR: La variable '{variable_name}' n'est pas présente dans le fichier.")
            print("\nVariables disponibles :", list(ds.keys()))
            print("Veuillez mettre à jour la valeur de VARIABLE_NAME dans le code.")
            return

        # Sélection de la variable (qui représente l'écart de température)
        difference_data = ds[variable_name]
        
        # 2. Calcul des statistiques
        print("\n--- Calcul des statistiques globales ---")
        
        # Calcul de l'écart moyen global sur toutes les dimensions (temps, lat, lon)
        ecart_moyen = difference_data.mean().item()
        
        # Autres statistiques
        ecart_type = difference_data.std().item()
        minimum = difference_data.min().item()
        maximum = difference_data.max().item()

        # Unités (tentative de récupération, sinon par défaut à K)
        try:
            units = difference_data.attrs['units']
        except (KeyError, AttributeError):
            units = "K (Kelvin) ou °C" # Hypothèse courante pour les modèles climatiques
            
        # 3. Affichage des résultats
        print("\n=============================================")
        print(f"STATISTIQUES DESCRIPTIVES de l'écart ({variable_name})")
        print("=============================================")
        
        # Affichage de l'Écart Moyen
        print(f"1. Écart Moyen : {ecart_moyen:+.4f} {units}")
        if ecart_moyen > 0:
            print("   -> L'écart est globalement POSITIF (Réchauffement ou 1ère carte plus chaude).")
        elif ecart_moyen < 0:
            print("   -> L'écart est globalement NÉGATIF (Refroidissement ou 2ème carte plus chaude).")
        else:
            print("   -> L'écart moyen est proche de zéro.")

        print(f"2. Écart Type (Variabilité) : {ecart_type:.4f} {units}")
        print(f"3. Valeur Minimum : {minimum:.4f} {units} (L'écart de refroidissement le plus fort)")
        print(f"4. Valeur Maximum : {maximum:.4f} {units} (L'écart de réchauffement le plus fort)")
        print("=============================================\n")
        
    except Exception as e:
        print(f"Une erreur s'est produite lors du traitement du fichier : {e}")

# --- Exécution du programme principal ---
if __name__ == "__main__":
    calculer_statistiques(FILENAME, VARIABLE_NAME)
    
    # --- Étape facultative pour inspecter la structure ---
    # Si le code ne fonctionne pas, décommentez les lignes ci-dessous
    # pour voir toutes les variables disponibles dans le fichier.
    # print("\n--- STRUCTURE COMPLÈTE DU FICHIER NETCDF ---")
    # try:
    #     ds = xr.open_dataset(FILENAME)
    #     print(ds)
    # except:
    #     pass