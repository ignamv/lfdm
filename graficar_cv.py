
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from os import sys

datos = np.genfromtxt(sys.argv[1])
plt.plot(datos[:, 0], datos[:, 1]*1e12)
plt.xlabel('Vg [V]')
plt.ylabel('Cg [pF]')
plt.show()
