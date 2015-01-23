from lantz import Driver, Feat, Action, Q_
import re

class MetaTest(type(Driver)):
    
    def __new__(cls, classname, bases, class_dict):
        def f(self):
            return 3
        my_feats = {}
        def unit_processors(units):
            units = Q_(units)
            def get(raw):
                return Q_(raw.lower().replace('v', 'V'))
            def set(value):
                return '{:~e}'.format(value.to(units))
            return (get, set)

        for command, attrs in class_dict['settings'].items():
            def setter(self, value):
                cmd = command + str(value)
                self.log_debug('Mando "{}"'.format(cmd))
            def getter(self):
                self.log_debug('Quiero "{}"'.format(command))
                return 33
            limits = attrs.get('limits')
            if limits is None:
                procs = None
            else:
                procs = [unit_processors(limits[0])]
            feat = Feat(read_once=True, fget=getter, fset=setter, procs=procs,
                    values=attrs.get('values'))
            my_feats[attrs['name']] = feat
            attrs['feat'] = feat

        class_dict.update(my_feats)
        return super().__new__(cls, classname, bases, class_dict)

class TestDriv(Driver, metaclass=MetaTest):

    def __init__(self):
        super().__init__()

    def initialize(self):
        self.read_settings()

    command_re = re.compile(r'([A-Z]+ ?)([^A-Z].*)')
    @Action()
    def read_settings(self):
        """Set feat caches from instrument values"""
        recv = 'M1,CT0,T1,W2,SM0,L0,C0,D1,BUR 0001 #,PER 1.00 MS,DBL 200 US,'\
              'DEL 65.0 NS,DTY 50%,WID 100 US,LEE 10.0 NS,TRE 10.0 NS,'\
              'HIL +1.00 V,LOL +0.00 V,'
        parts = recv.split(',')[:-1]
        for part in parts:
            command, value = self.command_re.match(part).groups()
            attrs = self.settings.get(command)
            if attrs is None:
                continue
            feat = attrs['feat']
            feat.set_cache(self, feat.post_get(value, self))

    settings = {
            'M': dict(name='trigger_mode', values=dict(normal='1',
            trigger='2', gate='3', ewid='4', ebur='5')),
            'PER ': dict(name='period', limits=(Q_(20, 'ns'), Q_(950, 'ms')))
            }

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    inst = TestDriv(3, '4', hola='no')
    inst.initialize()
    print(inst.read_settings())
    print(inst.recall())
    inst.period = Q_(3,'s')
