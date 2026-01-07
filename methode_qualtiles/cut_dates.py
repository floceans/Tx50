import xarray as xr
import numpy as np

# =========================
# CHEMINS DES FICHIERS
# =========================
A_path = "/home/florent/Documents/ENM_3A/Tx50/methode_qualtiles/COR_=percentile95_tasmax.nc"
B_path = "/home/florent/Documents/ENM_3A/Tx50/methode_qualtiles/tasmax_BRUT_CNRM-CERFACS-CNRM-CM5_historical_r1i1p1_CNRM-ALADIN63_day_19510101-20051231.nc"
out_path = "BRUT_=pers_95.nc"


time_var = "time"

# =========================
# OUVERTURE
# =========================
ds_A = xr.open_dataset(A_path)
ds_B = xr.open_dataset(B_path)

# =========================
# MASQUE TEMPOREL
# =========================
# True là où le temps de B existe dans A
mask = ds_B[time_var].isin(ds_A[time_var])

# On conserve uniquement les pas de temps valides
ds_B_cut = ds_B.where(mask, drop=True)

# =========================
# SAUVEGARDE
# =========================
ds_B_cut.to_netcdf(out_path)

ds_A.close()
ds_B.close()
