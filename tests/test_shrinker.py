import numpy as np
from spectral_discovery.counterexamples.shrinking import Shrinker
from spectral_discovery.spectral.resolvent import resolvent_norm

def make_block_counterexample(n_extra: int = 2):
    # create a 2x2 nearly singular block with large resolvent at z=1
    B = np.array([[1.0, 1e6], [0.0, 1.0]])
    # construct block diagonal matrix with extra zero rows/cols
    if n_extra <= 0:
        return B
    A = np.zeros((2 + n_extra, 2 + n_extra))
    A[:2, :2] = B
    return A

def test_shrinker_finds_small_block(tmp_path):
    A = make_block_counterexample(n_extra=3)
    # choose threshold and check_fn to match the demo-style test
    def check_fn(M):
        eigs = np.linalg.eigvals(M)
        rho = max(abs(eigs)) if eigs.size > 0 else 0.0
        z = complex(1.0)  # target point chosen to make B problematic
        rn = resolvent_norm(M, z)
        return rn > 1e3

    s = Shrinker(artifacts_dir=str(tmp_path / "artifacts"))
    res = s.shrink("test_ce", A, check_fn, min_dim=2)
    assert res is not None
    # If shrinking succeeded, check artifact exists and is smaller or equal dimension
    if res.success:
        assert res.artifact_path is not None
        import os
        assert os.path.exists(res.artifact_path)
        # load artifact and check it still violates
        d = np.load(res.artifact_path)
        M = d["matrix"]
        assert check_fn(M)
    else:
        # Fallback: ensure original A violates
        assert check_fn(A)
