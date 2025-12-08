import xarray as xr
import numpy as np
import matplotlib.pyplot as plt


file_1 = "/home/florent/Documents/ENM_3A/Tx50/Tx50/data/brut/txx_NorESM1-M_WRF381P.nc"
file_2 = "/home/florent/Documents/ENM_3A/Tx50/Tx50/data/cor/txx_NorESM1-M_WRF381P(1).nc"
output_name = "metrics_tasmax_corrigee_filtree.nc" # Changement de nom pour refléter le contenu



def plot_bool_hist(bool_list):
    """
    Affiche un histogramme du nombre de True cumulés selon l'index,
    et superpose la fonction exponentielle.
    """
    # Convertir booléens en 0/1
    counts = [int(b) for b in bool_list]

    # Cumul des True
    sum_counts = []
    s = 0
    for i in range(len(counts)):
        s += counts[i]
        sum_counts.append(s)

    # Création de l'histogramme
    plt.figure(figsize=(12,4))
    plt.bar(range(len(sum_counts)), sum_counts, color='skyblue', label='Cumul des True')

    # Superposer une fonction exponentielle
    x = np.arange(len(sum_counts))
    y_exp = np.exp(x / len(sum_counts))  # exponentielle normalisée pour s'adapter à la taille
    plt.plot(x, 1.1*(1.0265)**x, 'r-', linewidth=2, label='exp(x)')

    plt.xlabel('Index')
    plt.ylabel('True cumulés')
    plt.title('Histogramme des True cumulés avec fonction exp superposée')
    plt.legend()
    plt.show()



try:
    ds1 = xr.open_dataset(file_1)
    ds2 = xr.open_dataset(file_2)

    # Assurez-vous d'avoir les variables 'tasmax' ou 'tasmaxAdjust'
    da1 = ds1['tasmax'] if 'tasmax' in ds1 else ds1['tasmaxAdjust']
    da2 = ds2['tasmax'] if 'tasmax' in ds2 else ds2['tasmaxAdjust']

    # --- Étape 1: Harmonisation des coordonnées ---
    
    # Récupérer les dimensions du fichier source 1 (tasmax brut)
    dims_da1 = da1.dims
    # Assumer que les dimensions du fichier source 2 sont dans le même ordre
    rename_dict = {old: new for old, new in zip(da2.dims, dims_da1)}
    da2 = da2.rename(rename_dict)

    # Assigner des coordonnées numériques 'i' et 'j' pour assurer la compatibilité spatiale
    da2 = da2.assign_coords({
        "i": np.arange(da1.sizes.get("i", 0)),
        "j": np.arange(da1.sizes.get("j", 0))
    })
    
    # Assigner 'time' à da2 en utilisant celui de da1, pour être sûr de l'alignement
    if 'time' in da1.coords and 'time' in da2.coords:
        da2['time'] = da1['time']

    # --- Étape 2: Filtre temporel (condition : Tasmax du second fichier >= 45°C) ---
    
    # Dimensions spatiales, en supposant que 'time' est la première dimension
    # Si da2.dims est ('time', 'j', 'i'), spatial_dims sera ('j', 'i')
    spatial_dims = da2.dims[1:] 
    
    # Créer le masque : True pour tous les pas de temps où AU MOINS UN point spatial est >= 45
    # La conversion est supposée être en °C, si c'est en K, 45°C = 318.15 K. 
    # Je suppose ici que les données sont déjà en °C.
    mask_time = (da2 >= 318.15).any(dim=spatial_dims)

    print(mask_time)
    plot_bool_hist(mask_time.values.tolist())
    
    # Appliquer le filtre aux deux DataArray
    da1_filt = da1.sel(time=mask_time)
    da2_filt = da2.sel(time=mask_time)

    print(f"Nombre de pas de temps initiaux : {len(da1['time'])}")
    print(f"Nombre de pas de temps gardés par le filtre (> 45°C) : {mask_time.sum().item()}")

    # --- Étape 3: Calcul des métriques (Différence, Biais, EQM) ---
    
    # 3.1 Différence (Erreur)
    diff_da = da1_filt - da2_filt
    diff_da = diff_da.rename("difference")
    diff_da.attrs['description'] = "Difference (da1_brut - da2_corrige) pour les jours filtres (da2 >= 45°C)"

    # 3.2 Biais (Moyenne de l'erreur sur la dimension spatiale, ou moyenne temporelle si pas de dimensions spatiales)
    # Le biais est généralement la moyenne temporelle ou spatiale de la différence.
    # Ici, nous le calculons comme la moyenne spatiale de l'erreur pour chaque pas de temps filtré.
    bias_da = diff_da.mean(dim=spatial_dims)
    bias_da = bias_da.rename("bias")
    bias_da.attrs['description'] = "Biais (Moyenne spatiale de la différence) pour les jours filtres."

    # 3.3 Écart Quadratique Moyen (EQM / RMSE)
    # EQM pour chaque pas de temps, calculé sur les dimensions spatiales.
    # $RMSE = \sqrt{\frac{1}{N} \sum_{i} (da1 - da2)^2}$
    rmse_da = np.sqrt((diff_da**2).mean(dim=spatial_dims))
    rmse_da = rmse_da.rename("rmse")
    rmse_da.attrs['description'] = "Ecart Quadratique Moyen (RMSE) calculé spatialement pour chaque jour filtre."

    # --- Étape 4: Création du Dataset et Sauvegarde ---
    
    # Créer un Dataset qui contiendra les 3 DataArrays
    ds_output = xr.Dataset(
        data_vars={
            "difference": diff_da,
            "bias": bias_da,
            "rmse": rmse_da
        },
        coords={
            "time": da1_filt["time"],
            "i": da1_filt["i"] if "i" in da1_filt.coords else np.arange(da1_filt.sizes.get("i", 0)),
            "j": da1_filt["j"] if "j" in da1_filt.coords else np.arange(da1_filt.sizes.get("j", 0))
        }
    )

    ds_output.attrs['history'] = f"Calculé à partir de '{file_1}' et '{file_2}'."
    ds_output.attrs['comment'] = "Contient la différence (spatiale), le biais (moyen spatial), et le RMSE (moyen spatial) uniquement pour les pas de temps où Tasmax corrigé >= 45°C."

    ds_output.to_netcdf(output_name)
    print(f"\nSuccès ! Fichier '{output_name}' généré avec les variables : difference, bias, rmse.")

except Exception as e:
    print("\nErreur :", e)