import xarray as xr

file_1 = "/home/florent/Documents/ENM_3A/Tx50/Tx50/data/brut/txx_NorESM1-M_WRF381P.nc"
file_2 = "/home/florent/Documents/ENM_3A/Tx50/Tx50/data/cor/txx_NorESM1-M_WRF381P(1).nc"
output_name = "difference_tasmax_corrigee.nc"

try:
    # 1. Ouverture des fichiers
    ds1 = xr.open_dataset(file_1)
    ds2 = xr.open_dataset(file_2)
    
    # 2. Identification des variables
    # On récupère l'objet DataArray complet pour garder les métadonnées
    da1 = ds1['tasmax'] if 'tasmax' in ds1 else ds1['tasmaxAdjust']
    da2 = ds2['tasmax'] if 'tasmax' in ds2 else ds2['tasmaxAdjust']
    
    print(f"Variable 1 shape: {da1.shape}")
    print(f"Variable 2 shape: {da2.shape}")

    # 3. Vérification de compatibilité de taille brute
    if da1.shape != da2.shape:
        print("ERREUR FATALE : Les dimensions brutes (Time, X, Y) ne correspondent pas.")
    else:
        # --- CORRECTION ICI ---
        # On utilise .values pour extraire les tableaux Numpy bruts
        # Cela contourne la vérification des coordonnées de xarray
        raw_diff = da1.values - da2.values
        
        # 4. Reconstruction d'un DataArray xarray propre
        # On utilise les coordonnées du premier fichier comme référence
        diff_da = xr.DataArray(
            data=raw_diff,
            coords=da1.coords,
            dims=da1.dims,
            name='difference'
        )
        
        # Ajout des métadonnées
        diff_da.attrs['description'] = f"Difference calculée : {da1.name} - {da2.name}"
        diff_da.attrs['units'] = da1.attrs.get('units', 'unknown')

        # 5. Sauvegarde
        diff_da.to_netcdf(output_name)
        print(f"Succès ! Fichier '{output_name}' généré (sans explosion de mémoire).")

except Exception as e:
    print(f"Erreur : {e}")