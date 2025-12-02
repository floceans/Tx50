import pandas as pd

# Charger le fichier
df = pd.read_csv("Tableau_Tx50 - Feuille 1.csv")

# Nettoyage des niveaux de réchauffement
df["warming"] = (
    df["Niv. réchauffement"]
    .astype(str)
    .str.replace("°C", "", regex=False)
    .str.strip()
)

# Nettoyage T_max (certaines valeurs utilisent la virgule)
df["T_max"] = (
    df["T_max"]
    .astype(str)
    .str.replace(",", ".")
)
df["T_max"] = pd.to_numeric(df["T_max"], errors="coerce")

# Conversion des points >45 et >50
df["Pts T>45"] = pd.to_numeric(df["Pts T>45"], errors="coerce")
df["Pts T>50"] = pd.to_numeric(df["Pts T>50"], errors="coerce")

# Calcul des moyennes + nombre de cas
grouped = (
    df.groupby("warming")
      .agg(
          T_max=("T_max", "mean"),
          Pts_T45=("Pts T>45", "mean"),
          Pts_T50=("Pts T>50", "mean"),
          count=("T_max", "count")
      )
      .reset_index()
)

print(grouped)
