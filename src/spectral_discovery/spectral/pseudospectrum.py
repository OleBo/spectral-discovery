"""Pseudospectrum utilities.

Primary membership test uses smallest singular value:
    z ∈ Λ_ε(A) iff sigma_min(zI - A) <= ε

Provides a grid-based membership test and a simple adaptive refinement
that samples additional points around boundary candidates.

Notes:
- grid is expected to be a 1D array-like of complex numbers (e.g., flatten(meshgrid))
- adaptive refinement is conservative and designed for Phase 1 use.
"""
from __future__ import annotations
import numpy as np
from numpy.linalg import svd
from typing import Iterable, List, Optional, Tuple
import math


def _sigma_min_of_shift(A: np.ndarray, z: complex) -> float:
    """Compute smallest singular value of zI - A robustly."""
    M = z * np.eye(A.shape[0], dtype=A.dtype) - A
    try:
        s = svd(M, compute_uv=False)
    except np.linalg.LinAlgError:
        return 0.0
    if s.size == 0:
        return 0.0
    return float(s[-1])


def resolvent_norm_from_sigma(smin: float) -> float:
    if smin <= 0:
        return float("inf")
    return 1.0 / smin


def resolvent_norm(A: np.ndarray, z: complex) -> float:
    """Utility: compute ||(zI - A)^{-1}||_2 via sigma_min."""
    smin = _sigma_min_of_shift(A, z)
    return resolvent_norm_from_sigma(smin)


def epsilon_pseudospectrum(
    A: np.ndarray,
    epsilon: float,
    grid: Iterable[complex],
    adaptive: bool = True,
    refine_iters: int = 2,
    refine_threshold: float = 0.5,
) -> List[complex]:
    """Return the subset of grid points that belong to the epsilon-pseudospectrum.

    Parameters
    - A: (n,n) matrix
    - epsilon: membership threshold
    - grid: iterable of complex points (1D)
    - adaptive: whether to perform adaptive refinement around boundary points
    - refine_iters: number of refinement iterations
    - refine_threshold: relative band around epsilon to consider boundary (0..1)

    Returns:
    - list of grid points (subset of input grid) that satisfy sigma_min(zI-A) <= epsilon
    """
    pts = np.asarray(list(grid), dtype=complex)
    if pts.size == 0:
        return []

    # compute sigma_min for all points
    smins = np.empty(pts.shape, dtype=float)
    for i, z in enumerate(pts):
        smins[i] = _sigma_min_of_shift(A, z)

    inside_mask = smins <= float(epsilon)
    inside_pts = list(pts[inside_mask].tolist())

    if not adaptive:
        return inside_pts

    # estimate a characteristic spacing of the grid to guide local refinements
    # compute pairwise differences to nearest neighbor roughly by sampling
    def _estimate_spacing(arr: np.ndarray) -> float:
        if arr.size < 2:
            return 1.0
        # compute distances to nearest neighbor by random sampling
        sample = arr if arr.size <= 200 else np.random.choice(arr, size=200, replace=False)
        dists = []
        for z in sample:
            others = np.setdiff1d(arr, np.array([z]))
            if others.size == 0:
                continue
            dists.append(np.min(np.abs(others - z)))
        if not dists:
            return 1.0
        return float(np.median(dists))

    spacing = _estimate_spacing(pts)

    # adaptive refinements: around points where sigma_min near epsilon
    boundary_mask = (smins > epsilon) & (smins <= epsilon * (1.0 + refine_threshold))
    # also include points slightly below epsilon to expand contour
    boundary_mask |= (smins <= epsilon) & (smins >= epsilon * max(0.0, 1.0 - refine_threshold))

    candidate_points = pts[boundary_mask]
    refined_points = []

    for it in range(refine_iters):
        new_candidates = []
        r = spacing * (0.5 ** (it + 1))
        # sample small local grids around each candidate
        for zc in candidate_points:
            # 8-point circular neighborhood + center
            angles = np.linspace(0, 2 * math.pi, 9)[:-1]
            for theta in angles:
                zp = zc + r * complex(math.cos(theta), math.sin(theta))
                # evaluate sigma_min
                smin_zp = _sigma_min_of_shift(A, zp)
                if smin_zp <= epsilon:
                    refined_points.append(zp)
                else:
                    # if near boundary, include for next round of refinement
                    if smin_zp <= epsilon * (1.0 + refine_threshold):
                        new_candidates.append(zp)
        candidate_points = np.asarray(new_candidates, dtype=complex)
        # stop early if no new candidates
        if candidate_points.size == 0:
            break

    # merge refined points into inside_pts (avoid duplicates via set of rounded complex)
    def _uniq(points: Iterable[complex], tol: float = 1e-12):
        seen = set()
        out = []
        for z in points:
            key = (round(z.real, 12), round(z.imag, 12))
            if key not in seen:
                seen.add(key)
                out.append(z)
        return out

    all_inside = list(inside_pts) + list(refined_points)
    return _uniq(all_inside)
