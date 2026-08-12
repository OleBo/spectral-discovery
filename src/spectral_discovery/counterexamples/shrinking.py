"""Counterexample shrinking utilities.

Phase-1 safe shrinker: tries principal submatrices and rank truncations.
Records artifacts under artifacts/counterexamples and returns a summary.
"""
from __future__ import annotations
import numpy as np
from typing import Callable, Optional, Dict, Any, Tuple
from pathlib import Path
import numpy.linalg as la
import os
import json


class ShrinkResult:
    def __init__(self, success: bool, matrix: Optional[np.ndarray], artifact_path: Optional[str], metadata: Dict[str, Any]):
        self.success = success
        self.matrix = matrix
        self.artifact_path = artifact_path
        self.metadata = metadata


class Shrinker:
    def __init__(self, artifacts_dir: str = "artifacts/counterexamples"):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _save_artifact(self, ce_id: str, M: np.ndarray) -> str:
        p = self.artifacts_dir / f"{ce_id}.npz"
        np.savez_compressed(p, matrix=M)
        return str(p)

    def try_principal_submatrices(self, A: np.ndarray, check_fn: Callable[[np.ndarray], bool], min_dim: int = 2) -> Optional[np.ndarray]:
        """Try principal top-left k x k submatrices (k from n-1 down to min_dim)."""
        n = A.shape[0]
        for k in range(n - 1, min_dim - 1, -1):
            B = A[:k, :k].copy()
            if check_fn(B):
                return B
        return None

    def try_rank_truncation(self, A: np.ndarray, check_fn: Callable[[np.ndarray], bool], min_rank: int = 1) -> Optional[np.ndarray]:
        """Try truncated SVD approximations with rank r from n-1 down to min_rank."""
        try:
            U, s, Vh = la.svd(A, full_matrices=False)
        except la.LinAlgError:
            return None
        n = len(s)
        for r in range(n - 1, min_rank - 1, -1):
            Sr = np.zeros_like(A, dtype=A.dtype)
            Ur = U[:, :r]
            Vr = Vh[:r, :]
            Sr = (Ur * s[:r]) @ Vr
            if check_fn(Sr):
                return Sr
        return None

    def shrink(self, ce_id: str, A: np.ndarray, check_fn: Callable[[np.ndarray], bool], min_dim: int = 2, min_rank: int = 1) -> ShrinkResult:
        """Attempt a sequence of shrink strategies.

        ReturnsShrinkerResult with artifact path and metadata on success.
        """
        n = A.shape[0]
        metadata = {
            "original_dim": n,
            "steps": [],
        }

        # Quick check: ensure original A still violates (defensive)
        try:
            if not check_fn(A):
                metadata["steps"].append({"step": "original_not_violating"})
                return ShrinkResult(success=False, matrix=None, artifact_path=None, metadata=metadata)
        except Exception as e:
            metadata["steps"].append({"step": "check_fn_error", "error": str(e)})
            return ShrinkResult(success=False, matrix=None, artifact_path=None, metadata=metadata)

        # 1) principal submatrices
        B = self.try_principal_submatrices(A, check_fn, min_dim=min_dim)
        if B is not None:
            metadata["steps"].append({"step": "principal_submatrix", "new_dim": B.shape[0]})
            path = self._save_artifact(ce_id + "_submatrix", B)
            metadata["artifact"] = path
            return ShrinkResult(success=True, matrix=B, artifact_path=path, metadata=metadata)

        # 2) rank truncation
        B2 = self.try_rank_truncation(A, check_fn, min_rank=min_rank)
        if B2 is not None:
            # if rank truncation changed dimension (it doesn't), we still save
            metadata["steps"].append({"step": "rank_truncation", "shape": list(B2.shape)})
            path = self._save_artifact(ce_id + "_rank", B2)
            metadata["artifact"] = path
            return ShrinkResult(success=True, matrix=B2, artifact_path=path, metadata=metadata)

        # 3) no shrink found
        metadata["steps"].append({"step": "no_shrink_found"})
        return ShrinkResult(success=False, matrix=None, artifact_path=None, metadata=metadata)
