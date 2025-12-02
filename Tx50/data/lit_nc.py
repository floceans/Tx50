import netCDF4
import os

# Nom du fichier NetCDF (doit être dans le même répertoire que le script Python)
# Remplacez "txx_CNRM-CM5_ALADIN63.nc" par le chemin complet si le fichier est ailleurs.
fichier_netcdf = "C:\\Users\\flore\\Documents\\cours\\N7_ENM_3A\\Projet_Tx50\\Tx50\\data\\cor\\txx_CNRM-CM5_ALADIN63(3).nc"

try:
    # 1. Ouvrir le fichier NetCDF en mode lecture
    with netCDF4.Dataset(fichier_netcdf, 'r') as nc_file:
        print(f"--- Variables trouvées dans le fichier : {fichier_netcdf} ---")
        
        # 2. Afficher la liste des variables
        # La propriété 'variables' est un dictionnaire de toutes les variables du fichier.
        noms_variables = list(nc_file.variables.keys())
        print("Noms des variables :", noms_variables)
        print("-" * 50)
        
        # 3. Afficher les détails (dimensions, unités, etc.) de chaque variable
        for nom_var in noms_variables:
            variable = nc_file.variables[nom_var]
            print(f"Variable : {nom_var}")
            print(f"  Type de données : {variable.dtype}")
            print(f"  Dimensions : {variable.dimensions}")
            
            # Afficher les attributs si disponibles (comme 'units', 'long_name', etc.)
            for attr_name in variable.ncattrs():
                print(f"  {attr_name}: {variable.getncattr(attr_name)}")
            print("-" * 50)

except FileNotFoundError:
    print(f"Erreur : Le fichier '{fichier_netcdf}' n'a pas été trouvé. Assurez-vous qu'il est dans le bon répertoire.")
except Exception as e:
    print(f"Une erreur s'est produite lors de la lecture du fichier : {e}")