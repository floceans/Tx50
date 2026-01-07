import xarray as xr
import numpy as np

# --- CONFIGURATION ---
FILE_IN = "/home/florent/Documents/ENM_3A/Tx50/methode_qualtiles/tasmaxAdjust_COR_CNRM-CERFACS-CNRM-CM5_historical_r1i1p1_CNRM-ALADIN63_v2_MF-ADAMONT-SAFRAN-1980-2011_day_19510101-20051231.nc"
FILE_OUT = "COR_=percentile999_tasmax.nc"
VAR_NAME = "tasmaxAdjust"
VAR_OUT = "tasmax"
PERCENTILE = 99.9  # On garde les 5% des jours les plus chauds

def filtrer_par_percentile(input_file, output_file, var_name, var_out, percentile_val):
    print(f"Ouverture du fichier : {input_file}")
    ds = xr.open_dataset(input_file)
    
    # 1. Calcul du maximum spatial pour chaque pas de temps
    spatial_dims = [d for d in ds[var_name].dims if d != 'time']
    max_par_jour = ds[var_name].max(dim=spatial_dims)
    
    # 2. Calcul du seuil percentile
    seuil_calcule = max_par_jour.quantile(percentile_val / 100.0)
    print(f"Seuil calculé pour le {percentile_val}e percentile : {seuil_calcule.values:.2f}")

    # 3. Masque temporel
    mask = max_par_jour >= seuil_calcule

    # 4. Sélection
    ds_filtered = ds.sel(time=mask)

    # 5. Renommage de la variable pour la sortie
    ds_filtered = ds_filtered.rename({var_name: var_out})
    
    nb_dates = len(ds_filtered.time)
    print(f"Filtrage terminé : {nb_dates} pas de temps conservés.")
    
    print(f"Écriture du fichier : {output_file}...")
    ds_filtered.to_netcdf(output_file)
    print("Opération réussie.")

if __name__ == "__main__":
    filtrer_par_percentile(FILE_IN, FILE_OUT, VAR_NAME, VAR_OUT, PERCENTILE)
