biais = [-2.2,-2.4, -2.6]
rmse = [2.7, 2.9, 3.1]
p=[95, 99, 99.5]

seuil_p95 = 308.2
seuil_p99 = 311.7 #201 pas de temps
seuil_p995 = 312.9 #101 pas de temps

import matplotlib.pyplot as plt
plt.figure(figsize=(10,6))
plt.plot(p, biais, marker='o', label='Biais (°C)')
plt.plot(p, rmse, marker='o', label='RMSE (°C)')
plt.xticks(p)
plt.xlabel('Percentile utilisé pour le filtrage des dates (%)')
plt.ylabel('Valeur (°C)')
plt.title('Impact du choix du percentile sur le biais et le RMSE')
plt.legend()
plt.grid()
plt.show()