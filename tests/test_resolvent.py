import numpy as np 
from spectral_discovery.spectral.resolvent import resolvent_norm

def test_resolvent_small(): 
    A = np.array([[1.0, 2.0], [0.0, 3.0]]) 
    z = 10.0 
    rn = resolvent_norm(A, z) 
    assert rn > 0