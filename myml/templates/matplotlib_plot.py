# Description: Simple matplotlib line and scatter plots
import matplotlib.pyplot as plt
plt.plot(x, y, marker="o", label="data")
plt.xlabel("X"); plt.ylabel("Y"); plt.title("Data visualization")
plt.legend(); plt.grid(True); plt.show()
