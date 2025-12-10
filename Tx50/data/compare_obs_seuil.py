import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import warnings

# Optionnel : Supprimer la catégorie de warning spécifique au cas où xarray est ancienne/modifiée
# warnings.filterwarnings("ignore", category=DeprecationWarning) 

# --- CONFIGURATION ---
base_path = "/home/florent/Documents/ENM_3A/Tx50/Tx50/data/"
path_brut = os.path.join(base_path, "brut/")
path_cor = os.path.join(base_path, "cor/")
path_obs = os.path.join(base_path, "obs/")
# Dossier mis à jour pour refléter le nouveau seuil
path_out = os.path.join(base_path, "plots_rmse_bias_gt35/") 

os.makedirs(path_out, exist_ok=True)

# SEUIL DE TEMPÉRATURE : 35.0°C
TEMP_THRESHOLD = 35.0

file_obs = "txx_France-Metro_SAFRAN_year_1959-2024.nc"

model_files = [
    "txx_CNRM-CM5_ALADIN63.nc", "txx_CNRM-CM5_HadREM3-GA7-05.nc",
    "txx_EC-EARTH_HadREM3-GA7-05.nc", "txx_EC-EARTH_RACMO22E.nc",
    "txx_EC-EARTH_RCA4.nc", "txx_HadGEM2-ES_ALADIN63.nc",
    "txx_HadGEM2-ES_CCLM4-8-17.nc", "txx_HadGEM2-ES_HadREM3-GA7-05.nc",
    "txx_HadGEM2-ES_RegCM4-6.nc", "txx_IPSL-CM5A-MR_HIRHAM5.nc",
    "txx_IPSL-CM5A-MR_RCA4.nc", "txx_MPI-ESM-LR_CLMcom-CCLM4-8-17.nc",
    "txx_MPI-ESM-LR_RegCM4-6.nc", "txx_MPI-ESM-LR_REMO2009.nc",
    "txx_NorESM1-M_HIRHAM5.nc", "txx_NorESM1-M_REMO2015.nc",
    "txx_NorESM1-M_WRF381P.nc"
]

# --- FONCTIONS UTILES ---

def to_year_index(da):
    """Force l'index temporel en années (integers)."""
    if 'time' not in da.coords: return da
    try:
        years = da.time.dt.year
        return da.assign_coords(time=years)
    except Exception: return da

def load_and_clean(path, filename):
    """Charge, convertit en °C et simplifie le temps. Correction du DeprecationWarning."""
    full_path = os.path.join(path, filename)
    if not os.path.exists(full_path): return None
    try:
        # CORRECTION : Suppression de 'use_cftime=True'
        ds = xr.open_dataset(full_path, decode_times=True) 
        var_name = next((v for v in ['tasmax', 'tx', 'tasmaxAdjust'] if v in ds), None)
        if not var_name: return None
        da = ds[var_name]
        if da.mean() > 200: da = da - 273.15
        return to_year_index(da)
    except Exception: return None

def align_spatial_and_rename(da, target_dims, target_coords):
    """Identifie les dims spatiales de da et les renomme pour matcher target_dims."""
    spatial_dims = [d for d in da.dims if d != 'time']
    if len(spatial_dims) != 2: return None
    
    mapping = {spatial_dims[0]: target_dims[0], spatial_dims[1]: target_dims[1]}
    da = da.rename(mapping)
    
    # Forçage des coordonnées pour permettre l'arithmétique pixel à pixel
    da = da.assign_coords({target_dims[0]: target_coords[0], target_dims[1]: target_coords[1]})
    return da

# --- FONCTION DE CALCUL ---

def compute_metrics_filtered(da_model, da_obs, da_filter_ref, threshold=TEMP_THRESHOLD):
    """Calcule le RMSE et le Biais filtrés."""
    
    # 1. Intersection temporelle
    common_years = sorted(list(set(da_model.time.values) & set(da_obs.time.values) & set(da_filter_ref.time.values)))
    if not common_years: return None, None, None

    # Sélection
    da_m = da_model.sel(time=common_years)
    da_o = da_obs.sel(time=common_years)
    da_ref = da_filter_ref.sel(time=common_years)
    
    # 2. Harmonisation Spatiale
    dims_o = [d for d in da_o.dims if d != 'time']
    coords_o = [da_o[dims_o[0]], da_o[dims_o[1]]]
    
    da_m = align_spatial_and_rename(da_m, dims_o, coords_o)
    da_ref = align_spatial_and_rename(da_ref, dims_o, coords_o)
    
    if da_m is None or da_ref is None: return None, None, None

    # 3. Masquage et Calcul
    mask = da_ref >= threshold
    diff = da_m - da_o
    diff_masked = diff.where(mask)
    
    # Calcul du Biais
    bias = diff_masked.mean(dim=dims_o, skipna=True)
    
    # Calcul du RMSE
    rmse = np.sqrt((diff_masked**2).mean(dim=dims_o, skipna=True))
    
    return common_years, rmse.values, bias.values

# --- EXÉCUTION MAIN ---

print("Chargement OBS...")
da_obs = load_and_clean(path_obs, file_obs)
if da_obs is not None: da_obs = da_obs.sel(time=slice(1959, 2024))

if da_obs is None: exit("Echec chargement Obs.")

for filename in model_files:
    print(f"\n--- Modèle : {filename} ---")
    da_brut = load_and_clean(path_brut, filename)
    da_cor = load_and_clean(path_cor, filename)
    
    if da_brut is None or da_cor is None: continue
        
    try:
        # Calcul des métriques Brut (filtré par Corrigé > 35°C)
        years_b, rmse_b, bias_b = compute_metrics_filtered(da_brut, da_obs, da_cor)
        
        # Calcul des métriques Corrigé (filtré par Corrigé > 35°C)
        years_c, rmse_c, bias_c = compute_metrics_filtered(da_cor, da_obs, da_cor)
        
        if rmse_b is None: 
            print(" -> Calcul des métriques impossible après alignement/filtrage.")
            continue
            
        model_clean = filename.replace('txx_', '').replace('.nc', '')
        
        # 1. --- PLOT RMSE ---
        plt.figure(figsize=(10, 5))
        
        plt.plot(years_b, rmse_b, label='Brut vs Obs', color='red', linestyle='--', alpha=0.6)
        plt.plot(years_c, rmse_c, label='Corrigé vs Obs', color='blue', linewidth=2)
        
        plt.axhline(y=np.nanmean(rmse_b), color='r', linestyle=':', linewidth=1, alpha=0.5)
        plt.axhline(y=np.nanmean(rmse_c), color='b', linestyle=':', linewidth=1, alpha=0.8)
        
        plt.title(f"RMSE Annuel Spatial (Tx_cor > {TEMP_THRESHOLD}°C)\nModèle : {model_clean}")
        plt.ylabel("RMSE (°C)")
        plt.xlabel("Année")
        plt.legend(loc='upper left')
        plt.grid(True, alpha=0.3)
        
        out_rmse = os.path.join(path_out, f"RMSE_GT35_{model_clean}.png")
        plt.savefig(out_rmse, bbox_inches='tight')
        plt.close()

        # 2. --- PLOT BIAIS ---
        plt.figure(figsize=(10, 5))
        
        plt.plot(years_b, bias_b, label='Brut (Biais)', color='red', linestyle='--', alpha=0.6)
        plt.plot(years_c, bias_c, label='Corrigé (Biais)', color='blue', linewidth=2)
        
        plt.axhline(0, color='black', linewidth=0.8, linestyle='-') 
        plt.axhline(y=np.nanmean(bias_b), color='r', linestyle=':', linewidth=1, alpha=0.5)
        plt.axhline(y=np.nanmean(bias_c), color='b', linestyle=':', linewidth=1, alpha=0.8)

        plt.title(f"Biais Annuel Moyen Spatial (Tx_cor > {TEMP_THRESHOLD}°C)\nModèle : {model_clean}")
        plt.ylabel("Biais (Modèle - Obs) [°C]")
        plt.xlabel("Année")
        plt.legend(loc='upper left')
        plt.grid(True, alpha=0.3)
        
        out_bias = os.path.join(path_out, f"BIAIS_GT35_{model_clean}.png")
        plt.savefig(out_bias, bbox_inches='tight')
        plt.close()
        
        print(f" -> OK. Graphiques RMSE et Biais générés (Seuil {TEMP_THRESHOLD}°C).")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f" -> CRASH : {e}")

print("\n--- Traitement (RMSE + Biais, Tx > 35°C) terminé ---")