import pandas as pd
import matplotlib.pyplot as plt
import io

# 1. Préparation des données brutes
# Note: Les données sont séparées par des espaces ou des tabulations,
# et il manque une ligne d'en-tête explicite dans l'input initial.
# Je vais créer une chaîne de texte bien formatée pour une lecture facile.

data = """
Modèle écart_moyen écart_type écart_min écart_max
CNRM-ALADIN-2.5 3.22 2.53 -18.84 10.08
CRM-HADREM30 2.05 2.02 -13.64 13.99
EC-EARTH-HADREM3 -1.31 2.14 -11.86 12.78
EC-EARTH_RACMO22E -3.70 2.15 -21.81 7.55
EC-EARTH_RCA4 -2.29 2.23 -21.74 7.25
HadGEM2-ES_ALADIN63 -0.49 2.38 -18.26 9.75
HadGEM2-ES_CCLM4-8-17 2.01 2.03 -10.12 15.06
HadGEM2-ES_HadREM3-GA7-05 1.77 2.08 -10.51 14.90
HadGEM2-ES_RegCM4-6 1.27 1.91 -11.81 12.36
IPSL-CM5A-MR_RCA4 0.02 2.31 -21.74 10.25
MPI-ESM-LR_CLMcom-CCLM4-8-17 -1.03 2.42 -12.09 13.15
MPI-ESM-LR_RegCM4-6 0.12 2.26 -13.55 10.53
MPI-ESM-LR_REMO2009 -0.58 2.40 -13.54 14.60
NorESM1-M_HIRHAM5 -4.94 2.05 -24.90 5.29
NorESM1-M_REMO2015 -1.93 2.25 -17.49 10.93
NorESM1-M_WRF381P -1.33 1.79 -13.62 11.07
IPSL-CM5A-MR_HIRHAM5 -2.31 1.93 -24.75 8.11
"""

# 2. Lecture des données dans un DataFrame Pandas
# 'sep' est ajusté pour lire les espaces ou tabulations
df = pd.read_csv(io.StringIO(data), sep=r'\s+', engine='python')

# Utilisation de la colonne 'Modèle' comme index pour faciliter le tracé
df = df.set_index('Modèle')

# Liste des variables à tracer
variables = ['écart_moyen', 'écart_type', 'écart_min', 'écart_max']

# 3. Création des tracés (subplots)
# Création d'une figure avec 4 sous-graphiques (2 lignes, 2 colonnes)
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(14, 10))

# Aplatir l'array d'axes pour itérer facilement (axes est maintenant [ax1, ax2, ax3, ax4])
axes = axes.flatten()

# Définir une palette de couleurs distinctes
colors = plt.cm.get_cmap('tab20', len(df))

# Boucle sur chaque variable pour créer un tracé
for i, variable in enumerate(variables):
    ax = axes[i]
    
    # Tracer les données : une courbe (ou point) par modèle
    # On utilise un graphique en barres ou des points ici car l'axe des x est discret (les modèles)
    # Pour un tracé "courbe par modèle" dans un contexte discret comme celui-ci, 
    # une simple ligne de points ou un graphique en barres est plus approprié.
    
    # -------------------------------------------------------------
    # Option 1: Graphique en barres (souvent plus lisible pour des valeurs)
    # -------------------------------------------------------------
    df[variable].plot(kind='bar', ax=ax, color=colors.colors, legend=False)
    ax.set_title(f'Distribution de l\'{variable.replace("_", " ").title()}')
    ax.set_ylabel(variable.replace("_", " ").title())
    ax.set_xlabel('Modèle')
    ax.tick_params(axis='x', rotation=45) # Rotation des étiquettes des modèles pour la lisibilité
    ax.grid(axis='y', linestyle='--')
    
    # Si l'on préférait une ligne de points (plus près de la "courbe" demandée), remplacer la ligne `df[variable].plot(...)` par :
    # df[variable].plot(kind='line', style='o-', ax=ax, legend=False)
    # ax.set_xticks(range(len(df.index)))
    # ax.set_xticklabels(df.index, rotation=45, ha='right')
    
# Ajuster les sous-graphiques pour qu'ils ne se chevauchent pas
plt.tight_layout()

# Afficher le graphique
plt.show()

# 4. Affichage du DataFrame pour vérification (Optionnel)
print("\n--- Aperçu du DataFrame ---")
print(df)