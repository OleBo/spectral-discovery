"""Spectral utilities: resolvent, pseudospectrum helpers."""
from __future__ import annotations
import numpy as np
from numpy.linalg import svd, norm
from typing import Tuple, Iterable, List


def resolvent_norm(A: np.ndarray, z: complex) -> float:
    """Compute ||(zI - A)^{-1}||_2 via smallest singular value of (zI - A).

    Returns +inf when singular matrix (or numerically singular).
    """
    M = z * np.eye(A.shape[0], dtype=A.dtype) - A
    # compute smallest singular value
    try:
        s = svd(M, compute_uv=False)
    except np.linalg.LinAlgError:
        return float("inf")
    if s.size == 0:
        return float("inf")
    smin = float(s[-1])
    if smin <= 0:
        return float("inf")
    return 1.0 / smin


def epsilon_pseudospectrum(A: np.ndarray, epsilon: float, grid: Iterable[complex]) -> List[complex]:
    """Return grid points z where sigma_min(zI - A) <= epsilon."""
    inside = []
    for z in grid:
        M = z * np.eye(A.shape[0], dtype=A.dtype) - A
        try:
            s = svd(M, compute_uv=False)
        except np.linalg.LinAlgError:
            inside.append(z)
            continue
        smin = float(s[-1])
        if smin <= epsilon:
            inside.append(z)
    return inside


def is_normal(A: np.ndarray, tol: float = 1e-8) -> bool:
    """Check if A*A^* == A^**A up to tolerance."""
    return norm(A.conj().T @ A - A @ A.conj().T, ord=2) <= tol


def departure_from_normality(A: np.ndarray) -> float:
    """Compute ||A^*A - AA^*||_F as a measure of non-normality."""
    return norm(A.conj().T @ A - A @ A.conj().T, ord="fro")
