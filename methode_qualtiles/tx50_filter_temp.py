import xarray as xr
import numpy as np


# 1. Chargement des fichiers
cor = xr.open_dataset('/home/florent/Documents/ENM_3A/Tx50/methode_qualtiles/COR_percentile95_tasmax.nc')
brut = xr.open_dataset('/home/florent/Documents/ENM_3A/Tx50/methode_qualtiles/BRUT_pers_95.nc')

tas_cor = cor["tasmax"]
tas_brut = brut["tasmax"]

# Kelvin to Celsius if needed
if tas_cor.max() > 200:
    tas_cor = tas_cor - 273.15
if tas_brut.max() > 100:
    tas_brut = tas_brut - 273.15

# Mask T > 50°C in COR
mask = tas_cor > 40
idx = np.argwhere(mask.values)

results = []

biais = 0
RMSE = 0

for it, iy, ix in idx:
    time = tas_cor.time.values[it]
    lat = cor["lat"].isel(y=iy, x=ix).values
    lon = cor["lon"].isel(y=iy, x=ix).values
    val_cor = float(tas_cor.isel(time=it, y=iy, x=ix).values)
    val_brut = float(tas_brut.isel(time=it, j=iy, i=ix).values)
    biais += (val_cor - val_brut)
    RMSE += (val_cor - val_brut)**2
    results.append((time, lat, lon, val_cor, val_brut))



for r in results:
    print(f">>> Point COR: {r[3]:.2f}°C | Point BRUT: {r[4]:.2f}°C | time={r[0]} | lat={r[1]:.4f} | lon={r[2]:.4f}")


print("----- Résultats globaux -----")
n_points = len(results)
biais = biais / n_points
RMSE = np.sqrt(RMSE / n_points)
print(f"Biais global: {biais:.2f}°C")
print(f"RMSE global: {RMSE:.2f}°C")
cor.close()
brut.close()