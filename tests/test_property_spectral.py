import numpy as np
from numpy.linalg import eigvals, svd
import numpy as np
from hypothesis import given, strategies as st, settings
from hypothesis.extra.numpy import arrays, array_shapes
from spectral_discovery.spectral.resolvent import resolvent_norm
from spectral_discovery.spectral.pseudospectrum import _sigma_min_of_shift

# Small matrix sizes for fast Hypothesis tests
@settings(max_examples=40, deadline=None)
@given(n=st.integers(min_value=1, max_value=4), seed=st.integers(min_value=0, max_value=10000))
def test_eigenvalues_invariant_under_similarity(n, seed):
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    # build random invertible S via random matrix + identity scaling
    S = rng.normal(size=(n, n)) + rng.standard_normal() * 1j
    # ensure invertible by adding n*I
    S = S + n * np.eye(n)
    Sinv = np.linalg.inv(S)
    B = Sinv @ A @ S
    evA = np.sort_complex(eigvals(A))
    evB = np.sort_complex(eigvals(B))
    # compare sorted eigenvalues
    np.testing.assert_allclose(evA, evB, atol=1e-6, rtol=1e-6)

@settings(max_examples=40, deadline=None)
@given(n=st.integers(min_value=1, max_value=4), seed=st.integers(min_value=0, max_value=10000))
def test_singular_values_invariant_under_unitary(n, seed):
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n, n))
    # build orthogonal matrix via QR
    Q, _ = np.linalg.qr(rng.normal(size=(n, n)))
    P, _ = np.linalg.qr(rng.normal(size=(n, n)))
    U = Q
    V = P
    sA = np.sort(np.linalg.svd(A, compute_uv=False))
    sB = np.sort(np.linalg.svd(U @ A @ V, compute_uv=False))
    np.testing.assert_allclose(sA, sB, atol=1e-6, rtol=1e-6)

@settings(max_examples=40, deadline=None)
@given(n=st.integers(min_value=1, max_value=5), real_shift=st.floats(min_value=0.1, max_value=5.0), imag_shift=st.floats(min_value=-2.0, max_value=2.0), seed=st.integers(min_value=0, max_value=2000))
def test_resolvent_sigma_relation(n, real_shift, imag_shift, seed):
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n, n))
    z = complex(real_shift, imag_shift)
    # sigma_min computed by pseudospectrum helper should be consistent with resolvent_norm
    smin = _sigma_min_of_shift(A, z)
    rn = resolvent_norm(A, z)
    if smin <= 0:
        assert rn == float('inf') or np.isinf(rn)
    else:
        np.testing.assert_allclose(1.0 / smin, rn, rtol=1e-6, atol=1e-8)
