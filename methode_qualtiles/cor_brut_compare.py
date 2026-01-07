import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm

persentile_val = 999

# 1. Chargement des fichiers
ds_brut = xr.open_dataset('/home/florent/Documents/ENM_3A/Tx50/methode_qualtiles/BRUT_pers_'+str(persentile_val)+'.nc')
ds_cor = xr.open_dataset('/home/florent/Documents/ENM_3A/Tx50/methode_qualtiles/COR_percentile'+str(persentile_val)+'_tasmax.nc')

persentile_val = persentile_val/10
# 2. Calcul des moyennes temporelles (on réduit la dimension 'time')
# Cela crée une carte 2D de la température moyenne pour les jours extrêmes
mean_brut = ds_brut['tasmax'].mean(dim='time')
mean_cor = ds_cor['tasmax'].mean(dim='time')

# 3. Alignement des données
# BRUT utilise (j, i) et COR utilise (y, x). On extrait les valeurs numpy 
# pour s'affranchir des noms de dimensions si les grilles sont identiques.
data_brut = mean_brut.values
data_cor = mean_cor.values

# 4. Calcul des métriques spatiales
# Différence : BRUT - COR
diff = data_cor - data_brut

# Biais : moyenne de la différence
biais = np.nanmean(diff)

# RMSE : racine carrée de la moyenne des carrés de la différence
rmse = np.sqrt(np.nanmean(diff**2))

print(f"--- Résultats de la comparaison ---")
print(f"Biais moyen (BRUT - COR) : {biais:.4f} °C")
print(f"RMSE (Erreur quadratique) : {rmse:.4f} °C")

# 5. Visualisation de la carte de différence
plt.figure(figsize=(12, 7))
#plt.imshow(diff, cmap='RdBu_r', origin='lower', vmin=-5, vmax=5)
#plt.colorbar(label='Différence de Température (°C)')

cmap = cm.get_cmap('RdBu_r').copy()
cmap.set_over('black')   # couleur pour valeurs > vmax


im = plt.imshow(
    diff,
    cmap=cmap,
    origin='lower',
    vmin=-5,
    vmax=5
)

plt.colorbar(
    im,
    label='Différence de Température (°C)',
    extend='both'  # montre les flèches aux extrémités
)

plt.title('Effets de la correction de biais : Moyenne(COR) - Moyenne(BRUT)\n(Pas de temps filtrés au percentile '+str(persentile_val)+')')
plt.xlabel('Longitude (indice)')
plt.ylabel('Latitude (indice)')

# Sauvegarde de la carte
#plt.savefig('comparaison_brut_cor.png')
plt.show()