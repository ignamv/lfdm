import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from os import sys

datos = np.genfromtxt(sys.argv[1])
plt.loglog(datos[:, 0], datos[:, 1], 'x')
plt.xlabel('I [A]')
plt.ylabel('V [V]')
plt.show()
