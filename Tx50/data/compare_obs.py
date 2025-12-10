import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd

# --- CONFIGURATION ---
base_path = "/home/florent/Documents/ENM_3A/Tx50/Tx50/data/"
path_brut = os.path.join(base_path, "brut/")
path_cor = os.path.join(base_path, "cor/")
path_obs = os.path.join(base_path, "obs/")
path_out = os.path.join(base_path, "plots_rmse/")

os.makedirs(path_out, exist_ok=True)

file_obs = "txx_France-Metro_SAFRAN_year_1959-2024.nc"

model_files = [
    "txx_CNRM-CM5_ALADIN63.nc",
    "txx_CNRM-CM5_HadREM3-GA7-05.nc",
    "txx_EC-EARTH_HadREM3-GA7-05.nc",
    "txx_EC-EARTH_RACMO22E.nc",
    "txx_EC-EARTH_RCA4.nc",
    "txx_HadGEM2-ES_ALADIN63.nc",
    "txx_HadGEM2-ES_CCLM4-8-17.nc",
    "txx_HadGEM2-ES_HadREM3-GA7-05.nc",
    "txx_HadGEM2-ES_RegCM4-6.nc",
    "txx_IPSL-CM5A-MR_HIRHAM5.nc",
    "txx_IPSL-CM5A-MR_RCA4.nc",
    "txx_MPI-ESM-LR_CLMcom-CCLM4-8-17.nc",
    "txx_MPI-ESM-LR_RegCM4-6.nc",
    "txx_MPI-ESM-LR_REMO2009.nc",
    "txx_NorESM1-M_HIRHAM5.nc",
    "txx_NorESM1-M_REMO2015.nc",
    "txx_NorESM1-M_WRF381P.nc"
]

def to_year_index(da):
    """
    Force l'index temporel à devenir une simple liste d'années (integers).
    Gère les formats datetime64, cftime, etc.
    """
    if 'time' not in da.coords:
        return da
    
    try:
        # Essayer d'extraire l'année via l'accesseur .dt (marche pour datetime et cftime)
        years = da.time.dt.year
        # On remplace la coordonnée 'time' par ces entiers
        da = da.assign_coords(time=years)
    except Exception:
        # Si ça échoue (ex: déjà des entiers ou format bizarre), on ne touche pas
        # ou on tente une conversion brutale si c'est des nombres
        pass
        
    return da

def load_and_clean(path, filename):
    """Charge, convertit en °C, et force l'index temps en Années."""
    full_path = os.path.join(path, filename)
    if not os.path.exists(full_path):
        return None
    
    try:
        ds = xr.open_dataset(full_path, decode_times=True, use_cftime=True)
        var_name = next((v for v in ['tasmax', 'tx', 'tasmaxAdjust'] if v in ds), None)
        if not var_name: return None
        
        da = ds[var_name]
        
        # 1. Conversion °C
        if da.mean() > 200: da = da - 273.15
        
        # 2. Simplification du temps -> Années (Entiers)
        da = to_year_index(da)
        
        return da
    except Exception as e:
        print(f"Err loading {filename}: {e}")
        return None

def compute_rmse_robust(da_model, da_obs):
    """Calcule le RMSE sur les années communes uniquement."""
    
    # 1. Trouver les années communes (Intersection des sets)
    years_model = set(da_model.time.values)
    years_obs = set(da_obs.time.values)
    common_years = sorted(list(years_model.intersection(years_obs)))
    
    if not common_years:
        print("   ! Pas d'années communes (Vérifiez les formats dates).")
        return None, None

    # 2. Sélectionner uniquement ces années
    da_m = da_model.sel(time=common_years)
    da_o = da_obs.sel(time=common_years)
    
    # 3. Harmonisation Spatiale (Renommage des dims du modèle vers l'obs)
    # On enlève 'time' pour trouver les dims spatiales
    dims_o = [d for d in da_o.dims if d != 'time']
    dims_m = [d for d in da_m.dims if d != 'time']
    
    if len(dims_o) == 2 and len(dims_m) == 2:
        rename_dict = {dims_m[0]: dims_o[0], dims_m[1]: dims_o[1]}
        da_m = da_m.rename(rename_dict)
    
    # 4. Forcer les coordonnées spatiales exactes (pour éviter erreur d'alignement flottant)
    # On suppose que la grille est la même
    da_m = da_m.assign_coords({dims_o[0]: da_o[dims_o[0]], dims_o[1]: da_o[dims_o[1]]})
    
    # 5. Calcul Diff et RMSE
    diff = da_m - da_o
    rmse = np.sqrt((diff**2).mean(dim=dims_o))
    
    return common_years, rmse.values

# --- MAIN ---

print("Chargement OBS...")
da_obs = load_and_clean(path_obs, file_obs)
# Sécurité : on ne garde que 1959-2024 si le fichier est plus large
if da_obs is not None:
    da_obs = da_obs.sel(time=slice(1959, 2024))

if da_obs is None: exit("Echec Obs")

for filename in model_files:
    print(f"\nTraitement : {filename}")
    da_brut = load_and_clean(path_brut, filename)
    da_cor = load_and_clean(path_cor, filename)
    
    if da_brut is None or da_cor is None:
        print("   -> Fichier manquant.")
        continue
        
    try:
        # Calculs
        years_b, rmse_b = compute_rmse_robust(da_brut, da_obs)
        years_c, rmse_c = compute_rmse_robust(da_cor, da_obs)
        
        if rmse_b is None:
            print("   -> Echec calcul RMSE Brut.")
            continue

        # Plot
        plt.figure(figsize=(10, 5))
        plt.plot(years_b, rmse_b, label='Brut (Model - Obs)', color='red', linestyle='--', alpha=0.7)
        
        if rmse_c is not None:
            plt.plot(years_c, rmse_c, label='Corrigé (Model - Obs)', color='blue', linewidth=2)
        else:
            print("   -> Attention: Pas de RMSE corrigé calculé.")

        model_clean = filename.replace('txx_', '').replace('.nc', '')
        plt.title(f"RMSE Annuel Spatial\n{model_clean}")
        plt.xlabel("Année")
        plt.ylabel("RMSE (°C)")
        plt.legend()
        plt.grid(True, linestyle=':', alpha=0.5)
        
        out = os.path.join(path_out, f"RMSE_{model_clean}.png")
        plt.savefig(out, bbox_inches='tight')
        plt.close()
        print(f"   -> OK : {out}")
        
    except Exception as e:
        print(f"   -> CRASH : {e}")