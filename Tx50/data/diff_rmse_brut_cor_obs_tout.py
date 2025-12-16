import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings

# warnings.filterwarnings("ignore", category=DeprecationWarning)

# =========================================================
# CONFIGURATION
# =========================================================

base_path = "/home/florent/Documents/ENM_3A/Tx50/Tx50/data/"

path_brut = os.path.join(base_path, "brut/")
path_cor  = os.path.join(base_path, "cor/")
path_obs  = os.path.join(base_path, "obs/")
path_out  = os.path.join(base_path, "plots_rmse_bar/")

os.makedirs(path_out, exist_ok=True)

TEMP_THRESHOLD =30

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

# =========================================================
# FONCTIONS UTILITAIRES
# =========================================================

def to_year_index(da):
    """Force l'axe temporel en années."""
    if 'time' not in da.coords:
        return da
    try:
        return da.assign_coords(time=da.time.dt.year)
    except Exception:
        return da


def load_and_clean(path, filename):
    """Charge un NetCDF, convertit en °C et simplifie le temps."""
    full_path = os.path.join(path, filename)
    if not os.path.exists(full_path):
        return None

    try:
        ds = xr.open_dataset(full_path, decode_times=True)
        var_name = next((v for v in ['tasmax', 'tx', 'tasmaxAdjust'] if v in ds), None)
        if var_name is None:
            return None

        da = ds[var_name]
        if da.mean() > 200:
            da = da - 273.15

        return to_year_index(da)

    except Exception:
        return None


def align_spatial(da, da_ref):
    """Aligne les dimensions spatiales de da sur da_ref."""
    dims_ref = [d for d in da_ref.dims if d != 'time']
    dims_da  = [d for d in da.dims if d != 'time']

    if len(dims_ref) != 2 or len(dims_da) != 2:
        return None

    da = da.rename({dims_da[0]: dims_ref[0], dims_da[1]: dims_ref[1]})
    da = da.assign_coords({
        dims_ref[0]: da_ref[dims_ref[0]],
        dims_ref[1]: da_ref[dims_ref[1]]
    })

    return da


# =========================================================
# CALCUL RMSE FILTRÉ
# =========================================================

def compute_rmse_filtered(da_model, da_obs, da_filter, threshold):
    """RMSE spatial moyen annuel, filtré par da_filter > threshold."""
    
    years = sorted(set(da_model.time.values)
                   & set(da_obs.time.values)
                   & set(da_filter.time.values))
    
    if not years:
        return None

    da_m = da_model.sel(time=years)
    da_o = da_obs.sel(time=years)
    da_f = da_filter.sel(time=years)

    da_m = align_spatial(da_m, da_o)
    da_f = align_spatial(da_f, da_o)

    if da_m is None or da_f is None:
        return None

    mask = da_f >= threshold
    diff = (da_m - da_o).where(mask)

    rmse_year = np.sqrt((diff ** 2).mean(dim=[d for d in diff.dims if d != 'time'],
                                             skipna=True))

    return np.nanmean(rmse_year.values)


# =========================================================
# MAIN
# =========================================================

print("Chargement observations...")
da_obs = load_and_clean(path_obs, file_obs)
if da_obs is None:
    raise RuntimeError("Impossible de charger les observations")

da_obs = da_obs.sel(time=slice(1959, 2024))

models_names = []
rmse_brut = []
rmse_cor  = []

for filename in model_files:
    print(f"\n--- {filename} ---")

    da_b = load_and_clean(path_brut, filename)
    da_c = load_and_clean(path_cor,  filename)

    if da_b is None or da_c is None:
        print(" -> Fichier manquant ou invalide")
        continue

    rmse_b = compute_rmse_filtered(da_b, da_obs, da_c, TEMP_THRESHOLD)
    rmse_c = compute_rmse_filtered(da_c, da_obs, da_c, TEMP_THRESHOLD)

    if rmse_b is None or rmse_c is None:
        print(" -> Calcul RMSE impossible")
        continue

    model_name = filename.replace("txx_", "").replace(".nc", "")

    models_names.append(model_name)
    rmse_brut.append(rmse_b)
    rmse_cor.append(rmse_c)

    print(f" -> RMSE brut = {rmse_b:.2f} °C | RMSE corrigé = {rmse_c:.2f} °C")


# =========================================================
# BARPLOT FINAL
# =========================================================

x = np.arange(len(models_names))
width = 0.4

plt.figure(figsize=(15, 6))

plt.bar(x - width/2, rmse_brut, width, label="RMSE Brut vs Obs",
        color="red", alpha=0.6)

plt.bar(x + width/2, rmse_cor, width, label="RMSE Corrigé vs Obs",
        color="blue", alpha=0.8)

plt.xticks(x, models_names, rotation=30, ha="right")
plt.ylabel("RMSE moyen spatial (°C)")
plt.title(f"RMSE moyen (Tx_cor > {TEMP_THRESHOLD}°C)")
plt.legend()
plt.grid(axis="y", alpha=0.3)

out_file = os.path.join(path_out, "RMSE_BAR_GT30_ALL_MODELS.png")
plt.savefig(out_file, bbox_inches="tight")
plt.plot()

print("\n--- Terminé : barplot RMSE généré ---")
