import numpy as np
from lantz import Q_
#from pint import UnitRegistry
#Q_ = UnitRegistry().Quantity

def logspace(initial, final, points_per_decade):
    initial = Q_(initial)
    units = initial.units
    initial = initial.magnitude
    final = Q_(final).to(units).magnitude
    ret = np.power(10, np.arange(
        points_per_decade * np.log10(initial),
        points_per_decade * np.log10(final) + 1) / points_per_decade)
    if ret[-1] - final > final * .01:
        ret = ret[:-1]
    if units:
        return Q_(ret, units)
    else:
        return ret

def linspace(initial, final, points):
    initial = Q_(initial)
    units = initial.units
    initial = initial.magnitude
    final = Q_(final).to(units).magnitude
    ret = np.linspace(initial, final, points)
    if units:
        return Q_(ret, units)
    else:
        return ret

def arange(initial, final, increment):
    initial = Q_(initial)
    units = initial.units
    initial = initial.magnitude
    final = Q_(final).to(units).magnitude
    increment = Q_(increment).to(units).magnitude
    ret = np.arange(initial / increment, final / increment + 1) * increment
    if units:
        return Q_(ret, units)
    else:
        return ret
