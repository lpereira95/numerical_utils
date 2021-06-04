import numpy as np


def is_sym(A, rtol=1e-5, atol=1e-8):
    return np.allclose(A, A.T, rtol=rtol, atol=atol)
