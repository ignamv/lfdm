from hp8112a import HP8112A

def pulso(inst, largo, signo=1, **kwargs):
    """Manda un pulso de largo arbitrario

    signo puede ser 1 o -1
    Los argumentos adicionales configuran el generador. Ejemplo:
        
    >>> pulso(inst, Q_(10, 's'), signo=-1, trailing_edge=Q_(2, 'ms'))
    """
    inst.trigger_mode = 'trigger'
    # Esto genera una transición rápida 
    inst.complement = signo
