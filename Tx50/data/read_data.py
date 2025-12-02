import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import os
import sys

# --- 1. Définition des noms de fichiers et variables ---
FILE_A = "C:\\Users\\flore\\Documents\\cours\\N7_ENM_3A\\Projet_Tx50\\Tx50\\data\\brut\\txx_CNRM-CM5_ALADIN63.nc"        # Contient 'tasmax'
FILE_B = "C:\\Users\\flore\\Documents\\cours\\N7_ENM_3A\\Projet_Tx50\\Tx50\\data\\cor\\txx_CNRM-CM5_ALADIN63(3).nc"     # Contient 'tasmaxAdjust'
VAR_A = 'tasmax'
VAR_B = 'tasmaxAdjust'

print(f"--- Préparation de la cartographie : {VAR_A} vs {VAR_B} ---")

# --- 2. Chargement des données et renommage ---
def load_and_rename(filepath, var_name):
    """Charge un fichier netCDF et renomme la variable cible."""
    if not os.path.exists(filepath):
        print(f"ERREUR: Le fichier n'existe pas : {filepath}")
        return None
    try:
        ds = xr.open_dataset(filepath)
        # Sélection et renommage pour une manipulation facile
        da = ds[var_name].rename(f"{var_name}_data")
        ds.close() # Fermer l'accès au fichier après avoir extrait la variable
        return da
    except Exception as e:
        print(f"ERREUR lors du chargement de {filepath} ou sélection de {var_name}: {e}")
        return None

# Charger les DataArrays
da_a = load_and_rename(FILE_A, VAR_A)
da_b = load_and_rename(FILE_B, VAR_B)

if da_a is None or da_b is None:
    print("\nImpossible de continuer l'analyse.")
    sys.exit(1)

# --- 3. Calcul de la moyenne temporelle ---

# La variable tasmax est généralement 3D (time, lat, lon).
# On calcule la moyenne sur la dimension 'time' pour obtenir une carte 2D.
print("\nCalcul de la moyenne temporelle pour chaque variable...")
try:
    mean_a = da_a.mean(dim='time')
    mean_b = da_b.mean(dim='time')
except Exception as e:
    print(f"ERREUR: Impossible de calculer la moyenne sur la dimension 'time'. Vérifiez les dimensions de vos variables. {e}")
    print(f"Dimensions de {VAR_A}: {da_a.dims}")
    print(f"Dimensions de {VAR_B}: {da_b.dims}")
    sys.exit(1)

# --- 4. Calcul de la différence et de la métrique d'alignement ---

# Aligner les deux DataArrays avant la soustraction.
# xarray le fait automatiquement, mais on s'assure que les coordonnées sont cohérentes.
# On soustrait 'Original' (A) de 'Ajusté' (B) : Différence = Ajusté - Original
# On renomme cette variable pour la différencier dans la figure.
difference = (mean_b - mean_a).rename('Difference')

print(f"Plage de la différence (max - min) : {difference.max().item():.2f} - {difference.min().item():.2f}")

# Déterminer l'unité pour l'affichage
units = da_a.attrs.get('units', 'K') # Par défaut en Kelvin, unité standard en netCDF

# --- 5. Création de la Figure de Cartographie ---

# Déterminer l'étendue commune des données pour la colormap
# On utilise le minimum et le maximum global sur les deux moyennes
vmin_data = min(mean_a.min().item(), mean_b.min().item())
vmax_data = max(mean_a.max().item(), mean_b.max().item())

# Créer la figure avec 3 sous-graphiques (1 ligne, 3 colonnes)
fig, axes = plt.subplots(
    nrows=1, ncols=3, 
    figsize=(18, 6),
    # On suppose que vos données utilisent une projection basée sur lat/lon 
    # ou une projection spécifique que Cartopy peut reconnaître.
    # Si le chargement échoue, il faudra ajuster le projection 'proj'.
    subplot_kw={'projection': ccrs.PlateCarree()} 
)
plt.suptitle(f"Comparaison des Moyennes Temporelles de Température Maximale ({units})", fontsize=16, y=1.05)

# ----------------- PANNEAU 1 : tasmax (Original) -----------------
ax1 = axes[0]
ax1.coastlines()
ax1.set_title(f"A) Moyenne de {VAR_A} (Original)")
# Tracer les données. Utiliser les coordonnées lat/lon du DataArray
mean_a.plot.pcolormesh(
    ax=ax1, 
    transform=ccrs.PlateCarree(),
    vmin=vmin_data, 
    vmax=vmax_data, 
    cmap='Reds', # Utiliser une colormap pour la température
    cbar_kwargs={'label': f'Température moyenne ({units})'}
)
ax1.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

# ----------------- PANNEAU 2 : tasmaxAdjust (Ajusté) -----------------
ax2 = axes[1]
ax2.coastlines()
ax2.set_title(f"B) Moyenne de {VAR_B} (Ajusté)")
# Utiliser les mêmes vmin/vmax pour une comparaison visuelle équitable
mean_b.plot.pcolormesh(
    ax=ax2, 
    transform=ccrs.PlateCarree(),
    vmin=vmin_data, 
    vmax=vmax_data, 
    cmap='Reds',
    cbar_kwargs={'label': f'Température moyenne ({units})'}
)
ax2.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

# ----------------- PANNEAU 3 : Différence (Ajusté - Original) -----------------
ax3 = axes[2]
ax3.coastlines()
ax3.set_title(f"C) Différence (Ajusté - Original)")
# Utiliser une colormap divergente (comme 'coolwarm') pour la différence
# et centrer la colormap sur zéro (symétrique)
max_abs_diff = np.abs(difference).max().item()
difference.plot.pcolormesh(
    ax=ax3, 
    transform=ccrs.PlateCarree(),
    vmin=-max_abs_diff, 
    vmax=max_abs_diff, 
    cmap='coolwarm', 
    cbar_kwargs={'label': f'Différence ({units})'}
)
ax3.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

# ----------------- Affichage -----------------
plt.tight_layout(rect=[0, 0, 1, 0.95]) # Ajuster pour laisser de la place au suptitle
plt.show()

print("\nAffichage de la carte de comparaison terminé.")