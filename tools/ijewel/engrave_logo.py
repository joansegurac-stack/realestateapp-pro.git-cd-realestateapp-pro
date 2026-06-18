"""
Graba el LOGO en el interior del anillo y exporta GLB con TODOS los acabados.

Idea clave (que el usuario pidio): que el logo "sea siempre igual" en los 50 GLB.
Se consigue porque:
  1. El logo.3dm ya viene posicionado respecto al MISMO origen (0,0,0) que el
     anillo -> su transform queda BAKEADO. No se coloca a mano nunca.
  2. Los acabados (color + rugosidad + relieve) salen de finishes.py, un unico
     sitio -> identicos en cada exportacion.

Uso:
  # un anillo, todos los acabados en oro amarillo:
  python engrave_logo.py --ring PERFIL.3dm --logo logo.3dm

  # color concreto y angulo del logo (grados alrededor del dedo):
  python engrave_logo.py --ring PERFIL.3dm --logo logo.3dm --metal oro_rosa --angle 180

  # lote: procesa varios anillos -> los 50 GLB con el mismo logo:
  python engrave_logo.py --ring modelos/*.3dm --logo logo.3dm --all-finishes
"""
import os
import sys
import glob
import math
import argparse
import numpy as np
import rhino3dm as r3
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals
from PIL import Image

from finishes import METALS, FINISHES

TEX_DIR = os.path.join(os.path.dirname(__file__), "textures")
INNER_RADIUS_MM = 8.6   # radio interior (de la curva "Finger" del logo.3dm)


# --------------------------------------------------------------------------- #
#  Lectura de mallas Rhino                                                     #
# --------------------------------------------------------------------------- #
def brep_meshes(geom):
    """Extrae la malla de render incrustada de un Brep -> (V, F, N)."""
    V, F, N, off = [], [], [], 0
    for face in geom.Faces:
        rm = face.GetMesh(r3.MeshType.Render)
        if not rm:
            continue
        V += [(v.X, v.Y, v.Z) for v in rm.Vertices]
        N += [(n.X, n.Y, n.Z) for n in rm.Normals]
        for i in range(len(rm.Faces)):
            a, b, c, d = rm.Faces[i]
            F.append((a + off, b + off, c + off))
            if d != c:
                F.append((a + off, c + off, d + off))
        off += len(rm.Vertices)
    return np.array(V), np.array(F, np.int64), np.array(N)


def load_breps(path):
    m = r3.File3dm.Read(path)
    out = []
    for o in m.Objects:
        if isinstance(o.Geometry, r3.Brep):
            V, F, N = brep_meshes(o.Geometry)
            if len(V):
                out.append((V, F, N))
    return out


# --------------------------------------------------------------------------- #
#  UVs cilindricas (para que martillado/rallado envuelvan el aro)             #
# --------------------------------------------------------------------------- #
def cylindrical_uv(V, tile=1):
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    u = (np.arctan2(z, x) / (2 * math.pi) + 0.5) * tile
    vmin, vmax = y.min(), y.max()
    v = (y - vmin) / (vmax - vmin + 1e-9)
    return np.column_stack([u % 1.0, v])


def rot_y(V, deg):
    if not deg:
        return V
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return V @ R.T


def split_interior(V, F):
    """Separa triangulos de la PARED INTERIOR (contacto con el dedo) del resto.

    Interior = normal apuntando hacia el eje (dot con radial exterior < 0) y
    radio menor que el radio medio. Devuelve dos arrays de caras (int, ext).
    """
    cen = V[F].mean(axis=1)
    r = np.hypot(cen[:, 0], cen[:, 2])
    tri = V[F]
    gn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    gn /= np.linalg.norm(gn, axis=1, keepdims=True) + 1e-9
    out = cen.copy(); out[:, 1] = 0
    out /= np.linalg.norm(out, axis=1, keepdims=True) + 1e-9
    dot = (gn * out).sum(axis=1)
    rmid = (r.min() + r.max()) / 2
    interior = (dot < -0.3) & (r < rmid)
    return F[interior], F[~interior]


# --------------------------------------------------------------------------- #
#  Construccion de un GLB para un acabado concreto                            #
# --------------------------------------------------------------------------- #
def build_glb(ring, logo, metal, finish_name, out_path, angle=0):
    spec = FINISHES[finish_name]
    color = METALS[metal]
    base = [color[0], color[1], color[2], 1.0]

    nmap = None
    if spec["normal_map"]:
        p = os.path.join(TEX_DIR, spec["normal_map"])
        if os.path.exists(p):
            nmap = Image.open(p).convert("RGB")

    def ext_material():
        # acabado elegido (exterior del anillo)
        return PBRMaterial(
            baseColorFactor=base, metallicFactor=1.0,
            roughnessFactor=spec["roughness"], normalTexture=nmap,
        )

    def polished_material():
        # cara interior SIEMPRE pulida/brillo, sea cual sea el acabado exterior
        return PBRMaterial(
            baseColorFactor=base, metallicFactor=1.0, roughnessFactor=0.05,
        )

    scene = trimesh.Scene()

    # --- anillo: exterior con acabado + pared interior SIEMPRE pulida ---
    for i, (V, F, N) in enumerate(ring):
        Fin, Fext = split_interior(V, F)
        if len(Fext):
            me = trimesh.Trimesh(vertices=V, faces=Fext, vertex_normals=N, process=False)
            me.visual = TextureVisuals(uv=cylindrical_uv(V, spec["tile"]),
                                       material=ext_material())
            scene.add_geometry(me, node_name=f"Ring_{i}_ext")
        if len(Fin):
            mi = trimesh.Trimesh(vertices=V, faces=Fin, vertex_normals=N, process=False)
            mi.visual = TextureVisuals(uv=cylindrical_uv(V, 1),
                                       material=polished_material())
            scene.add_geometry(mi, node_name=f"Ring_{i}_interior_pulido")

    # --- logo: grabado laser NEGRO (mate, no metalico) ---
    V, F, N = logo[0]
    V = rot_y(V, angle)
    lmesh = trimesh.Trimesh(vertices=V, faces=F, vertex_normals=rot_y(N, angle), process=False)
    lmesh.visual = TextureVisuals(
        uv=cylindrical_uv(V, 1),
        material=PBRMaterial(
            baseColorFactor=[0.02, 0.02, 0.02, 1.0],  # negro
            metallicFactor=0.0,                        # no metal -> look grabado laser
            roughnessFactor=0.55,
        ),
    )
    scene.add_geometry(lmesh, node_name="Logo_Laser_Negro")

    # centrar en el CENTRO del anillo para que orbite libre en todas direcciones
    center = scene.bounds.mean(axis=0)
    T = np.eye(4); T[:3, 3] = -center
    for name in list(scene.geometry):
        scene.graph.update(frame_to=name, matrix=T)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    scene.export(out_path)
    return out_path


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ring", nargs="+", required=True, help="uno o varios .3dm de anillo")
    ap.add_argument("--logo", required=True, help=".3dm del logo (ya posicionado)")
    ap.add_argument("--metal", default="oro_amarillo", choices=list(METALS))
    ap.add_argument("--finish", default=None, choices=list(FINISHES),
                    help="un acabado concreto; por defecto se hacen todos")
    ap.add_argument("--all-finishes", action="store_true")
    ap.add_argument("--all-metals", action="store_true")
    ap.add_argument("--angle", type=float, default=0, help="giro del logo en grados")
    ap.add_argument("--out", default="out", help="carpeta de salida")
    args = ap.parse_args()

    # expandir comodines manualmente (por si el shell no lo hace)
    rings = []
    for r in args.ring:
        rings += glob.glob(r) or [r]

    logo = load_breps(args.logo)
    metals = list(METALS) if args.all_metals else [args.metal]
    finishes = ([args.finish] if args.finish
                else list(FINISHES))  # por defecto: todos los acabados

    n = 0
    for rp in rings:
        ring = load_breps(rp)
        stem = os.path.splitext(os.path.basename(rp))[0]
        for metal in metals:
            for fin in finishes:
                out = os.path.join(args.out, f"{stem}__{metal}__{fin}.glb")
                build_glb(ring, logo, metal, fin, out, args.angle)
                print("  ->", out)
                n += 1
    print(f"\n{n} GLB generados en '{args.out}/'")


if __name__ == "__main__":
    main()
