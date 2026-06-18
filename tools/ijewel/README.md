# iJewel · Logo grabado en el interior + acabados (GLB)

Pipeline para **grabar el logo en el interior del anillo** de forma
**estandarizada** y exportar GLB listos para subir a **iJewel3D**, con todos los
acabados (mate, satinado, martillado, rallado, pulido) y colores de metal.

## ¿Por qué "siempre sale igual" en los 50 GLB?

1. **Posición del logo bakeada.** El `logo.3dm` ya viene colocado respecto al
   **mismo origen (0,0,0)** que el anillo (radio interior 8.6 mm, lado −X). El
   script no lo recoloca a mano nunca → la posición es idéntica en cada export.
2. **Acabados centralizados.** Color, rugosidad y relieve salen de
   `finishes.py` (un único sitio) → mismos valores en todas las exportaciones.

## Uso

```bash
pip install rhino3dm trimesh numpy pillow

# 1) generar los mapas de relieve (solo una vez)
python make_normalmaps.py

# 2) un anillo, TODOS los acabados en oro amarillo
python engrave_logo.py --ring PERFIL.3dm --logo logo.3dm --metal oro_amarillo

# 3) lote: los 50 anillos, mismo logo, todos los acabados y metales
python engrave_logo.py --ring "modelos/*.3dm" --logo logo.3dm \
       --all-finishes --all-metals --out salida

# 4) 3 colores conmutables DENTRO de un mismo GLB (oro amarillo/rosa/blanco)
python engrave_logo.py --ring PERFIL.3dm --logo logo.3dm --multicolor
```

Salida: `out/<anillo>__<metal>__<acabado>.glb`
(con `--multicolor`: `out/<anillo>__tricolor__<acabado>.glb`)

### Multicolor en un solo GLB

`--multicolor` genera **un GLB por acabado con los 3 colores de oro dentro**,
conmutables mediante la extensión estándar `KHR_materials_variants`. El logo
negro NO cambia (queda fijo). El visor debe soportar variantes de material
(iJewel y la mayoría de configuradores lo hacen). Personaliza con
`--colors oro_amarillo oro_rosa oro_blanco`.

## Recomendado para que se vea increíble en iJewel

Como en iJewel los materiales se aplican con sus **presets** y su render (HDRI),
tienes dos formas de trabajar:

- **Opción A (recomendada):** sube cualquier GLB (p. ej. el `satinado`) y aplica
  el color/acabado con los **presets de iJewel** (`Replace Material`). La
  geometría con el logo interior ya va perfecta.
- **Opción B (martillado/rallado):** en iJewel usa los PNG de `textures/`
  (`hammered.png`, `brushed.png`) como **Bump/Normal Map** sobre el preset que
  elijas. Son tileables y envuelven el aro.

## Reglas fijas del modelo

- **Logo = grabado láser negro:** material negro mate y no metálico (no se ve
  como metal, sino como marcado láser).
- **Cara interior siempre pulida:** aunque el exterior sea satinado, rayado,
  rugoso o mate, la pared interior (contacto con el dedo, donde va el logo) se
  exporta **pulida/brillo**. La separación interior/exterior se calcula por
  geometría (normal hacia el eje y radio < radio medio).
- **Centrado en el origen:** el GLB se centra en el centro del anillo para que
  **orbite libre en todas direcciones** en cualquier visor.

## Acabados (`finishes.py`)

| Acabado    | roughness | relieve        |
|------------|-----------|----------------|
| pulido     | 0.06      | —              |
| satinado   | 0.35      | —              |
| mate       | 0.80      | —              |
| martillado | 0.28      | hammered.png   |
| rallado    | 0.40      | brushed.png    |

Colores: `oro_amarillo`, `oro_rosa`, `oro_blanco`, `plata`, `platino`
(editables en `finishes.py`).

## Parámetros útiles

- `--angle <grados>`: gira el logo alrededor del dedo (eje Y) sin cambiar tamaño
  ni profundidad. Útil para posicionarlo en otro punto del interior.
- `--metal`, `--finish`: para generar una sola combinación.
