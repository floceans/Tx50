import xarray as xr
import numpy as np
import os
import sys

# --- 1. Définition des noms de fichiers ---
FILE_A = "C:\\Users\\flore\\Documents\\cours\\N7_ENM_3A\\Projet_Tx50\\Tx50\\data\\brut\\txx_CNRM-CM5_ALADIN63.nc"        # Contient 'tasmax'
FILE_B = "C:\\Users\\flore\\Documents\\cours\\N7_ENM_3A\\Projet_Tx50\\Tx50\\data\\cor\\txx_CNRM-CM5_ALADIN63(3).nc"     # Contient 'tasmaxAdjust'

# Les noms de variables dans vos fichiers
VAR_A = 'tasmax'
VAR_B = 'tasmaxAdjust'
# Nom unifié pour la comparaison
COMPARISON_VAR_NAME = 'tasmax_unifie'

print(f"--- Correction d'erreur et comparaison des fichiers : {FILE_A} et {FILE_B} ---")
print("-" * 50)

# --- 2. Fonction pour charger les données et gérer les erreurs ---
def load_netcdf(filepath):
    """Charge un fichier netCDF et gère les erreurs."""
    if not os.path.exists(filepath):
        print(f"ERREUR: Le fichier n'existe pas : {filepath}")
        return None
    try:
        ds = xr.open_dataset(filepath)
        return ds
    except Exception as e:
        print(f"ERREUR lors du chargement de {filepath}: {e}")
        return None

ds_a = load_netcdf(FILE_A)
ds_b = load_netcdf(FILE_B)

if ds_a is None or ds_b is None:
    print("\nImpossible de continuer car un ou plusieurs fichiers n'ont pas pu être chargés.")
    sys.exit(1)

# --- 3. Renommage et sélection des DataArrays pour la comparaison ---

# Renommer la variable de température maximale dans chaque Dataset
# pour lui donner un nom commun pour la comparaison, puis extraire l'Array.
try:
    # Fichier A : Renommage de 'tasmax'
    var_a = ds_a[VAR_A].rename(COMPARISON_VAR_NAME)
    print(f" Variable '{VAR_A}' du Fichier A sélectionnée.")
    
    # Fichier B : Renommage de 'tasmaxAdjust'
    var_b = ds_b[VAR_B].rename(COMPARISON_VAR_NAME)
    print(f" Variable '{VAR_B}' du Fichier B sélectionnée.")

except KeyError as e:
    print(f"ERREUR: La variable attendue n'est pas présente dans l'un des fichiers : {e}")
    print("Variables Fichier A:", list(ds_a.data_vars.keys()))
    print("Variables Fichier B:", list(ds_b.data_vars.keys()))
    sys.exit(1)

print("-" * 50)

# --- 4. Comparaison des variables unifiées ---

print(f"\n## Comparaison des données de température unifiées ('{COMPARISON_VAR_NAME}')")

# a) Comparaison de la structure (Dimensions et Coordonnées)
# Note : Nous ignorons les attributs ici car nous avons déjà renommé la variable.
# xarray aligne automatiquement les données basées sur les coordonnées (temps, lat, lon, etc.)
# lors des opérations arithmétiques.

# Vérification de l'égalité simple (y compris les attributs/coordonnées)
data_identical = var_a.equals(var_b)

if data_identical:
    print(f"\n Les données de la variable '{COMPARISON_VAR_NAME}' sont **parfaitement identiques** entre les deux fichiers.")
else:
    print(f"\n Les données de la variable '{COMPARISON_VAR_NAME}' ne sont **PAS identiques**.")

    # Calcul et affichage des différences
    
    try:
        # La soustraction dans xarray aligne les données sur les coordonnées communes
        difference = var_a - var_b
        
        # Statistiques de la différence
        max_abs_diff = np.nanmax(np.abs(difference.values))
        mean_diff = np.nanmean(difference.values)
        std_diff = np.nanstd(difference.values)
        
        # Tentative d'obtenir l'unité
        units = var_a.attrs.get('units', 'unités inconnues')
        
        print("\n--- Statistiques des différences (Fichier A - Fichier B) ---")
        print(f"  * Différence absolue maximale : {max_abs_diff:.6f} {units}")
        print(f"  * Différence moyenne : {mean_diff:.6f} {units}")
        print(f"  * Écart-type des différences : {std_diff:.6f} {units}")
        print("------------------------------------------------------------")

        if max_abs_diff < 1e-6:
            print("   (La différence est très faible, elle pourrait être due à une erreur de précision de virgule flottante.)")
        
        # Afficher le nombre de points qui diffèrent (en utilisant une tolérance)
        # Note : On utilise np.isclose pour les comparaisons avec des nombres flottants
        diff_count = np.sum(~np.isclose(var_a.values, var_b.values, equal_nan=True))
        total_points = var_a.size
        print(f"  * Nombre de points de données différents : {diff_count} sur {total_points} ({diff_count/total_points*100:.2f}%)")

    except Exception as e:
        print(f"   Impossible de calculer les différences de données (problème de dimensions/coordonnées) : {e}")

# --- 5. Affichage des informations sur les dimensions ---
print("\n## Informations sur les dimensions des données :")
print(f"Dimensions Fichier A ({VAR_A}): {var_a.dims}")
print(f"Dimensions Fichier B ({VAR_B}): {var_b.dims}")


# --- 6. Fermeture des fichiers ---
ds_a.close()
ds_b.close()
print("\nOpération terminée et fichiers netCDF fermés.")