"""
Definicion ESTANDAR de acabados y colores de metal para iJewel.

La gracia de tener esto en un fichero aparte es que TODOS los GLB que generemos
(los 50 del modelo) usan exactamente los mismos valores -> el resultado es
identico y reproducible siempre.

Acabado = rugosidad (roughness) + (opcional) mapa de relieve normal map.
Color   = baseColorFactor en PBR (metallic siempre 1.0 porque es metal).
"""

# --- Colores de metal (RGB lineal aprox, 0..1) -----------------------------
METALS = {
    "oro_amarillo": (1.000, 0.766, 0.336),
    "oro_rosa":     (0.955, 0.637, 0.538),
    "oro_blanco":   (0.913, 0.894, 0.840),
    "plata":        (0.962, 0.949, 0.922),
    "platino":      (0.834, 0.824, 0.808),
}

# --- Acabados ---------------------------------------------------------------
# roughness:  0 = espejo, 1 = totalmente mate
# normal_map: nombre del PNG de relieve (None = superficie lisa)
# tile:       repeticiones extra del patron alrededor del aro (los PNG ya van
#             con proporcion correcta, asi que normalmente 1)
# label:      nombre bonito para el selector de variantes
FINISHES = {
    "pulido":          {"roughness": 0.06, "normal_map": None,                  "tile": 1, "label": "Brillo"},
    "satinado":        {"roughness": 0.35, "normal_map": None,                  "tile": 1, "label": "Satinado"},
    "mate":            {"roughness": 0.80, "normal_map": None,                  "tile": 1, "label": "Mate"},
    "martillado":      {"roughness": 0.28, "normal_map": "hammered.png",        "tile": 1, "label": "Martillado"},
    "rayado_vertical": {"roughness": 0.40, "normal_map": "brushed_vertical.png","tile": 1, "label": "Rayado vertical"},
    "rallado":         {"roughness": 0.40, "normal_map": "brushed.png",         "tile": 1, "label": "Rayado horizontal"},
}
