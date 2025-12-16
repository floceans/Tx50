import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os

# =========================================================
# CONFIGURATION
# =========================================================

base_path = "/home/florent/Documents/ENM_3A/Tx50/Tx50/data/"

path_brut = os.path.join(base_path, "brut/")
path_cor  = os.path.join(base_path, "cor/")
path_obs  = os.path.join(base_path, "obs/")
path_out  = os.path.join(base_path, "plots_rmse_diff_thresholds/")

os.makedirs(path_out, exist_ok=True)

THRESHOLDS = np.arange(30, 51, 1)

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
# FONCTIONS
# =========================================================

def to_year_index(da):
    try:
        return da.assign_coords(time=da.time.dt.year)
    except Exception:
        return da


def load_and_clean(path, filename):
    full_path = os.path.join(path, filename)
    if not os.path.exists(full_path):
        return None

    ds = xr.open_dataset(full_path, decode_times=True)
    var = next((v for v in ['tasmax', 'tx', 'tasmaxAdjust'] if v in ds), None)
    if var is None:
        return None

    da = ds[var]
    if da.mean() > 200:
        da = da - 273.15

    return to_year_index(da)


def align_spatial(da, da_ref):
    dims_ref = [d for d in da_ref.dims if d != 'time']
    dims_da  = [d for d in da.dims if d != 'time']

    da = da.rename({dims_da[0]: dims_ref[0], dims_da[1]: dims_ref[1]})
    da = da.assign_coords({
        dims_ref[0]: da_ref[dims_ref[0]],
        dims_ref[1]: da_ref[dims_ref[1]]
    })
    return da


def compute_rmse_filtered(da_model, da_obs, da_filter, threshold):

    years = sorted(set(da_model.time.values)
                   & set(da_obs.time.values)
                   & set(da_filter.time.values))
    if not years:
        return np.nan

    da_m = align_spatial(da_model.sel(time=years), da_obs)
    da_o = da_obs.sel(time=years)
    da_f = align_spatial(da_filter.sel(time=years), da_obs)

    mask = da_f >= threshold
    diff = (da_m - da_o).where(mask)

    rmse_year = np.sqrt((diff ** 2).mean(
        dim=[d for d in diff.dims if d != 'time'], skipna=True))

    return np.nanmean(rmse_year.values)

# =========================================================
# MAIN
# =========================================================

print("Chargement observations...")
da_obs = load_and_clean(path_obs, file_obs).sel(time=slice(1959, 2024))

rmse_diff = {}

for filename in model_files:
    model_name = filename.replace("txx_", "").replace(".nc", "")
    print(f"\n--- {model_name} ---")

    da_b = load_and_clean(path_brut, filename)
    da_c = load_and_clean(path_cor,  filename)

    if da_b is None or da_c is None:
        continue

    diffs = []

    for th in THRESHOLDS:
        rmse_b = compute_rmse_filtered(da_b, da_obs, da_c, th)
        rmse_c = compute_rmse_filtered(da_c, da_obs, da_c, th)
        diffs.append(rmse_b - rmse_c)

    rmse_diff[model_name] = diffs

# =========================================================
# PLOT FINAL : point + label gras + anti-chevauchement
# =========================================================

plt.figure(figsize=(13, 7))

label_positions = []  # mémoriser les y déjà utilisées
min_dy = 0.15         # séparation verticale minimale (°C)

colors = plt.cm.tab20(np.linspace(0, 1, len(rmse_diff)))  # palette 20 couleurs

for (model, diffs), c in zip(rmse_diff.items(), colors):
    y = np.array(diffs)
    x = THRESHOLDS

    # Tracer la courbe
    plt.plot(x, y, linewidth=1.5, alpha=0.8, color=c)

    # Dernier point valide
    valid = np.where(~np.isnan(y))[0]
    if len(valid) == 0:
        continue

    i_end = valid[-1]
    x_end = x[i_end]
    y_end = y[i_end]

    # Point coloré
    plt.scatter(x_end, y_end, color=c, s=30, zorder=5)

    # Anti-chevauchement vertical
    y_label = y_end
    while any(abs(y_label - y0) < min_dy for y0 in label_positions):
        y_label += min_dy
    label_positions.append(y_label)

    # Label en gras
    plt.text(
        x_end + 0.3, y_label,
        model,
        fontsize=9,
        fontweight='bold',
        verticalalignment='center',
        color=c
    )

plt.axhline(0, color='black', linewidth=1)
plt.xlabel("Seuil Tx (°C)")
plt.ylabel("ΔRMSE = RMSE(brut) − RMSE(corrigé) (°C)")
plt.title("Gain de RMSE de la correction en fonction du seuil Tx")
plt.grid(alpha=0.3)

plt.xlim(THRESHOLDS[0], THRESHOLDS[-1] + 5)

plt.tight_layout()

out_fig = os.path.join(path_out, "RMSE_DIFF_vs_THRESHOLD_POINT_LABEL.png")
plt.savefig(out_fig, dpi=200)
plt.close()

print("\n--- Figure ΔRMSE avec point + label gras générée ---")
