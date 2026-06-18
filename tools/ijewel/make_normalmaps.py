"""
Genera los mapas de relieve (normal maps) procedurales para los acabados
martillado y rallado. Se guardan en textures/ y se reutilizan en todos los GLB,
asi el relieve es identico siempre.

Uso:  python make_normalmaps.py
"""
import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "textures")
os.makedirs(OUT, exist_ok=True)
SIZE = 1024


def height_to_normal(h, strength=2.0):
    """Convierte un mapa de alturas (HxW, 0..1) en un normal map RGB tileable."""
    gx = np.gradient(np.roll(h, 0, axis=1), axis=1) * strength
    gy = np.gradient(h, axis=0) * strength
    nz = np.ones_like(h)
    n = np.stack([-gx, -gy, nz], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    rgb = ((n * 0.5 + 0.5) * 255).astype(np.uint8)
    return Image.fromarray(rgb, "RGB")


def hammered(seed=7, dents=420, strength=3.0):
    """Patron de martillado: muchos golpes redondeados (toroidal/tileable)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    h = np.zeros((SIZE, SIZE), np.float32)
    for _ in range(dents):
        cx, cy = rng.uniform(0, SIZE, 2)
        r = rng.uniform(SIZE * 0.03, SIZE * 0.07)
        depth = rng.uniform(0.4, 1.0)
        # distancia toroidal para que el patron sea tileable
        dx = np.minimum(np.abs(xx - cx), SIZE - np.abs(xx - cx))
        dy = np.minimum(np.abs(yy - cy), SIZE - np.abs(yy - cy))
        d2 = (dx * dx + dy * dy) / (r * r)
        h += np.exp(-d2) * depth
    h = (h - h.min()) / (h.max() - h.min() + 1e-9)
    return height_to_normal(h, strength)


def brushed(seed=3, strength=1.6):
    """Patron rallado/cepillado: lineas finas en una direccion."""
    rng = np.random.default_rng(seed)
    line = rng.standard_normal(SIZE)
    # suavizar un poco en la direccion de la linea
    k = np.ones(5) / 5
    line = np.convolve(np.concatenate([line[-4:], line]), k, "valid")[:SIZE]
    h = np.tile(line, (SIZE, 1))          # lineas verticales
    h = (h - h.min()) / (h.max() - h.min() + 1e-9)
    return height_to_normal(h.T, strength)  # T -> lineas horizontales (alrededor del aro)


if __name__ == "__main__":
    hammered().save(os.path.join(OUT, "hammered.png"))
    brushed().save(os.path.join(OUT, "brushed.png"))
    print("normal maps generados en", OUT)
