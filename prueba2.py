import visa

rm = visa.ResourceManager()
inst = rm.open_resource('GPIB0::11::INSTR')

