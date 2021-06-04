import numpy as np


def is_sym(A, rtol=1e-5, atol=1e-8):
    return np.allclose(A, A.T, rtol=rtol, atol=atol)


def create_tridiagonal(diag, diag_lower, diag_upper=None):
    if diag_upper is None:
        diag_upper = diag_lower

    return np.diag(diag) + np.diag(diag_lower, -1) + np.diag(diag_upper, 1)


def get_max_band(A):
    m = []
    for j in range(A.shape[1]):
        col = A[:, j]
        m.append(np.max(np.abs(np.where(col != 0)[0] - j)))

    return np.max(m)


def get_banded_sym_lower(A):
    n = A.shape[0]
    max_band = get_max_band(A)

    A_band = np.empty((max_band + 1, n))
    for j in range(n):
        m = min(max_band + 1, (n - j))
        A_band[:m, j] = A[j:(j + m), j]

    return A_band
