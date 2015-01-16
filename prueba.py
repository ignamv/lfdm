import visa

rm = visa.ResourceManager()
insts = rm.list_resources()
print(insts)
print('Opening {}'.format(insts[0]))
inst = rm.open_resource(insts[0])
