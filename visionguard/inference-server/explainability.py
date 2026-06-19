"""Explainability: a CAM heatmap (where the model is looking) and a feature
embedding (for similar-defect retrieval), both from a single backbone forward.

Uses EigenCAM — the first principal component of a backbone feature map — which
needs only activations, no gradients, so it works under inference mode and is
robust across YOLO variants. The same activation is global-average-pooled into a
fixed-length embedding for pgvector similarity search.

Requires a torch model (a .pt). When the deployed model is ONNX, CAM/embedding
degrade to None / zero-vector and detection still works.
"""
from __future__ import annotations

import base64

import cv2
import numpy as np
import torch

from config import EMBED_DIM


def _find_target_layer(torch_model):
    """The backbone's SPPF (last backbone block) is a good, semantically rich CAM
    target. Falls back to the deepest Conv2d found."""
    seq = getattr(getattr(torch_model, "model", None), "model", None)
    if seq is None:
        return None
    # ultralytics backbone SPPF sits around index 9; grab the last module that
    # produces a 4D feature map by picking the deepest container before head.
    try:
        return seq[9]
    except (IndexError, TypeError):
        last = None
        for m in torch_model.modules():
            if isinstance(m, torch.nn.Conv2d):
                last = m
        return last


class Explainer:
    def __init__(self, detector) -> None:
        self.detector = detector
        self.torch_model = detector.torch_model
        self.layer = _find_target_layer(self.torch_model) if self.torch_model else None
        self._activation: torch.Tensor | None = None
        if self.layer is not None:
            self.layer.register_forward_hook(self._hook)

    def _hook(self, _module, _inp, output):
        out = output[0] if isinstance(output, (list, tuple)) else output
        self._activation = out.detach()

    def explain(self, image, detections) -> tuple[str | None, list[float]]:
        """Run a forward (via the detector) and return (heatmap_b64, embedding)."""
        if self.layer is None:
            return None, [0.0] * EMBED_DIM

        arr = np.asarray(image.convert("RGB"))
        self._activation = None
        # Triggers the hooked forward pass.
        self.detector.model.predict(arr, verbose=False)
        act = self._activation
        if act is None:
            return None, [0.0] * EMBED_DIM

        a = act[0].float().cpu().numpy()          # (C, H, W)
        heatmap = self._eigencam(a)               # (H, W) in [0,1]
        overlay = self._overlay(arr, heatmap)
        embedding = self._embedding(a)
        return overlay, embedding

    @staticmethod
    def _eigencam(a: np.ndarray) -> np.ndarray:
        c, h, w = a.shape
        flat = a.reshape(c, h * w)                 # (C, HW)
        flat = flat - flat.mean(axis=1, keepdims=True)
        # First principal component over channels -> per-pixel projection.
        _, _, vt = np.linalg.svd(flat, full_matrices=False)
        proj = vt[0].reshape(h, w)
        proj = np.abs(proj)
        proj -= proj.min()
        rng = proj.max() - proj.min()
        return proj / rng if rng > 1e-8 else proj

    @staticmethod
    def _overlay(img: np.ndarray, heatmap: np.ndarray) -> str:
        h, w = img.shape[:2]
        hm = cv2.resize(heatmap, (w, h))
        hm = np.uint8(255 * hm)
        hm = cv2.applyColorMap(hm, cv2.COLORMAP_JET)
        hm = cv2.cvtColor(hm, cv2.COLOR_BGR2RGB)
        blended = np.uint8(0.55 * img + 0.45 * hm)
        ok, buf = cv2.imencode(".png", cv2.cvtColor(blended, cv2.COLOR_RGB2BGR))
        if not ok:
            return None
        return "data:image/png;base64," + base64.b64encode(buf).decode()

    @staticmethod
    def _embedding(a: np.ndarray) -> list[float]:
        gap = a.mean(axis=(1, 2))                   # (C,)
        # Resample channel vector to a fixed length so the pgvector dim is stable.
        x_old = np.linspace(0, 1, len(gap))
        x_new = np.linspace(0, 1, EMBED_DIM)
        vec = np.interp(x_new, x_old, gap)
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm > 1e-8 else vec.tolist()


_explainer = None


def get_explainer(detector):
    global _explainer
    if _explainer is None:
        _explainer = Explainer(detector)
    return _explainer
