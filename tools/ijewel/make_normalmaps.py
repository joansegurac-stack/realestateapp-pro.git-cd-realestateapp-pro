"""
Genera los mapas de relieve (normal maps) para los acabados con textura:
  - hammered.png         -> martillado
  - brushed_vertical.png -> rayado vertical (lineas a lo ancho de la banda)
  - brushed.png          -> rayado horizontal (lineas alrededor del aro)

Son imagenes ANCHAS (relacion ~16:1) y tileables en horizontal, pensadas para
UV cilindrica con tile=1: la propia imagen ya lleva la proporcion del aro
(circunferencia ~60 mm x banda ~3 mm), asi el patron no sale estirado.

Uso:  python make_normalmaps.py
"""
import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "textures")
os.makedirs(OUT, exist_ok=True)
W, H = 2048, 128   # ancho = alrededor del aro (u), alto = ancho de banda (v)


def height_to_normal(h, strength=2.0):
    h = (h - h.min()) / (h.max() - h.min() + 1e-9)
    gx = np.gradient(h, axis=1) * strength * (W / 256)
    gy = np.gradient(h, axis=0) * strength * (H / 256)
    n = np.stack([-gx, -gy, np.ones_like(h)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8), "RGB")


def hammered(seed=7, dents=70, strength=2.2):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    h = np.zeros((H, W), np.float32)
    for _ in range(dents):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(28, 46)
        depth = rng.uniform(0.4, 1.0)
        dx = np.minimum(np.abs(xx - cx), W - np.abs(xx - cx))  # tileable en u
        dy = np.abs(yy - cy)
        h += np.exp(-(dx * dx + dy * dy) / (r * r)) * depth
    return height_to_normal(h, strength)


def brushed(seed=3, strength=1.4, vertical=False):
    rng = np.random.default_rng(seed)
    n = W if vertical else H
    line = rng.standard_normal(n)
    k = np.ones(5) / 5
    line = np.convolve(np.concatenate([line[-4:], line]), k, "valid")[:n]
    if vertical:                       # rayas verticales: finas en u, cruzan la banda
        h = np.tile(line[None, :], (H, 1))
    else:                              # rayas horizontales: dan la vuelta al aro
        h = np.tile(line[:, None], (1, W))
    return height_to_normal(h, strength)


if __name__ == "__main__":
    hammered().save(os.path.join(OUT, "hammered.png"))
    brushed(vertical=True).save(os.path.join(OUT, "brushed_vertical.png"))
    brushed(vertical=False).save(os.path.join(OUT, "brushed.png"))
    print("normal maps generados en", OUT)
