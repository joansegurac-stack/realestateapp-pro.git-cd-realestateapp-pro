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
import copy
import math
import argparse
import numpy as np
import rhino3dm as r3
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals
from PIL import Image
from pygltflib import GLTF2

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
#  Variantes de color en un MISMO GLB (KHR_materials_variants)                 #
# --------------------------------------------------------------------------- #
def add_color_variants(path, colors):
    """Convierte un GLB (construido con colors[0]) en uno con varios colores
    conmutables. Solo cambian los materiales metalicos; el logo negro se queda
    fijo. `colors` = lista de (nombre, (r,g,b))."""
    g = GLTF2().load(path)

    # materiales coloreables = los metalicos (el logo es metallic=0 -> se ignora)
    base_idx = [i for i, m in enumerate(g.materials)
                if (m.pbrMetallicRoughness.metallicFactor or 0) >= 0.99]

    variant_mat = {}  # material base -> [idx de material por color]
    for bi in base_idx:
        lst = []
        for ci, (cname, rgb) in enumerate(colors):
            if ci == 0:
                g.materials[bi].pbrMetallicRoughness.baseColorFactor = [*rgb, 1.0]
                lst.append(bi)
            else:
                nm = copy.deepcopy(g.materials[bi])
                nm.name = f"{cname}"
                nm.pbrMetallicRoughness.baseColorFactor = [*rgb, 1.0]
                g.materials.append(nm)
                lst.append(len(g.materials) - 1)
        variant_mat[bi] = lst

    # declarar la extension a nivel de documento
    g.extensions = g.extensions or {}
    g.extensions["KHR_materials_variants"] = {
        "variants": [{"name": c[0]} for c in colors]
    }
    g.extensionsUsed = list(set((g.extensionsUsed or []) + ["KHR_materials_variants"]))

    # mapear cada primitiva metalica a la variante correspondiente
    for me in g.meshes:
        for pr in me.primitives:
            if pr.material in variant_mat:
                lst = variant_mat[pr.material]
                pr.extensions = pr.extensions or {}
                pr.extensions["KHR_materials_variants"] = {
                    "mappings": [{"material": lst[ci], "variants": [ci]}
                                 for ci in range(len(colors))]
                }
    g.save(path)


# --------------------------------------------------------------------------- #
#  Grabado HUNDIDO hacia dentro (boolean) + GLB maestro multi-acabado          #
# --------------------------------------------------------------------------- #
def prepare_engraving(ring, logo, angle=0, recess=0.05):
    """Resta el logo del anillo para crear el HUECO del grabado y devuelve el
    'tapon' negro que rellena ese hueco, ligeramente hundido (look laser hacia
    dentro). Devuelve (anillo_con_hueco, tapon)."""
    import trimesh.transformations as tf
    lg = trimesh.Trimesh(*logo[0][:2], process=True)
    if angle:
        lg.apply_transform(tf.rotation_matrix(math.radians(angle), [0, 1, 0]))
    lr = np.hypot(lg.vertices[:, 0], lg.vertices[:, 2])
    lrmin, lrmax = lr.min(), lr.max()

    rings_out, plugs = [], []
    for (V, F, N) in ring:
        rr = np.hypot(V[:, 0], V[:, 2])
        if rr.min() < lrmax and rr.max() > lrmin:          # el logo penetra esta capa
            shell = trimesh.Trimesh(V, F, process=True)
            cut = shell.difference(lg)                       # anillo - logo = hueco
            inter = shell.intersection(lg)                  # parte embebida = tapon
            rings_out.append((np.asarray(cut.vertices), np.asarray(cut.faces), None))
            if inter is not None and len(inter.faces):
                plugs.append(inter)
        else:
            rings_out.append((V, F, N))

    plug = None
    if plugs:
        pm = trimesh.util.concatenate(plugs)
        if recess:                                          # hundir radialmente hacia el metal
            rad = pm.vertices.copy(); rad[:, 1] = 0
            rad /= np.linalg.norm(rad, axis=1, keepdims=True) + 1e-9
            pm.vertices = pm.vertices + rad * recess
        plug = (np.asarray(pm.vertices), np.asarray(pm.faces), None)
    return rings_out, plug


def _prettify(name):
    return name.replace("_", " ").capitalize()


def build_master_glb(ring, plug, finishes, colors, out_path):
    """UN GLB con todos los acabados x colores conmutables (KHR_materials_variants)
    y el logo grabado en negro fijo."""
    textured = [f for f in finishes if FINISHES[f]["normal_map"]]
    nmaps = {f: Image.open(os.path.join(TEX_DIR, FINISHES[f]["normal_map"])).convert("RGB")
             for f in textured}
    base0 = [*colors[0][1], 1.0]

    scene = trimesh.Scene()
    ei = 0
    for i, (V, F, N) in enumerate(ring):
        Fin, Fext = split_interior(V, F)
        if len(Fext):
            me = trimesh.Trimesh(vertices=V, faces=Fext, process=False)
            mat = PBRMaterial(baseColorFactor=base0, metallicFactor=1.0, roughnessFactor=0.3)
            if ei < len(textured):                          # incrusta la textura en el GLB
                f = textured[ei]; mat.normalTexture = nmaps[f]; mat.name = f"EMB::{f}"
            me.visual = TextureVisuals(uv=cylindrical_uv(V, 1), material=mat)
            scene.add_geometry(me, node_name=f"RING{i}_EXT")
            ei += 1
        if len(Fin):
            mi = trimesh.Trimesh(vertices=V, faces=Fin, process=False)
            mi.visual = TextureVisuals(uv=cylindrical_uv(V, 1),
                                       material=PBRMaterial(baseColorFactor=base0,
                                                            metallicFactor=1.0, roughnessFactor=0.05))
            scene.add_geometry(mi, node_name=f"RING{i}_INT")

    if plug is not None:
        V, F, N = plug
        pm = trimesh.Trimesh(vertices=V, faces=F, process=False)
        pm.visual = TextureVisuals(uv=cylindrical_uv(V, 1),
                                   material=PBRMaterial(baseColorFactor=[0.02, 0.02, 0.02, 1.0],
                                                        metallicFactor=0.0, roughnessFactor=0.55))
        scene.add_geometry(pm, node_name="LOGO_LASER")

    center = scene.bounds.mean(axis=0)                       # centrar -> giro 360 libre
    T = np.eye(4); T[:3, 3] = -center
    for name in list(scene.geometry):
        scene.graph.update(frame_to=name, matrix=T)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    scene.export(out_path)
    _wire_master_variants(out_path, finishes, colors)
    return out_path


def _wire_master_variants(path, finishes, colors):
    from pygltflib import Material, PbrMetallicRoughness, NormalMaterialTexture
    g = GLTF2().load(path)

    # indice de textura incrustado por acabado (materiales EMB::<finish>)
    tex_index = {}
    for m in g.materials:
        if m.name and m.name.startswith("EMB::") and m.normalTexture is not None:
            tex_index[m.name.split("::", 1)[1]] = m.normalTexture.index

    # rol de cada mesh por el nombre del nodo
    mesh_role = {}
    for nd in g.nodes:
        if nd.mesh is None:
            continue
        nm = nd.name or ""
        mesh_role[nd.mesh] = ("ext" if "EXT" in nm else
                              "int" if "INT" in nm else
                              "logo" if "LOGO" in nm else "other")

    # reconstruir materiales (las texturas/imagenes se conservan por indice)
    g.materials = []

    def add_mat(rgb, rough, texidx=None, metal=1.0, name=None):
        pbr = PbrMetallicRoughness(baseColorFactor=[*rgb, 1.0],
                                   metallicFactor=metal, roughnessFactor=rough)
        mat = Material(name=name, pbrMetallicRoughness=pbr)
        if texidx is not None:
            mat.normalTexture = NormalMaterialTexture(index=texidx)
        g.materials.append(mat)
        return len(g.materials) - 1

    ext_mat, int_mat = {}, {}
    for f in finishes:
        ti = tex_index.get(f) if FINISHES[f]["normal_map"] else None
        for cn, rgb in colors:
            ext_mat[(f, cn)] = add_mat(rgb, FINISHES[f]["roughness"], ti, name=f"{f}|{cn}")
    for cn, rgb in colors:
        int_mat[cn] = add_mat(rgb, 0.05, name=f"interior|{cn}")
    black = add_mat((0.02, 0.02, 0.02), 0.55, metal=0.0, name="logo_laser")

    # lista de variantes (acabado x color) y su indice
    variants, varindex, vi = [], {}, 0
    for f in finishes:
        for cn, rgb in colors:
            variants.append({"name": f"{FINISHES[f]['label']} · {_prettify(cn)}"})
            varindex[(f, cn)] = vi; vi += 1
    g.extensions = g.extensions or {}
    g.extensions["KHR_materials_variants"] = {"variants": variants}
    g.extensionsUsed = list(set((g.extensionsUsed or []) + ["KHR_materials_variants"]))

    # mapear cada primitiva a la variante correspondiente
    for mi, me in enumerate(g.meshes):
        role = mesh_role.get(mi, "other")
        for pr in me.primitives:
            if role == "logo":
                pr.material = black
                continue
            mappings = []
            for f in finishes:
                for cn, rgb in colors:
                    m = ext_mat[(f, cn)] if role == "ext" else int_mat[cn]
                    mappings.append({"material": m, "variants": [varindex[(f, cn)]]})
            pr.material = mappings[0]["material"]
            pr.extensions = pr.extensions or {}
            pr.extensions["KHR_materials_variants"] = {"mappings": mappings}
    g.save(path)


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
    ap.add_argument("--multicolor", action="store_true",
                    help="3 colores conmutables en un MISMO GLB (oro amarillo/rosa/blanco)")
    ap.add_argument("--master", action="store_true",
                    help="UN solo GLB: acabados x colores conmutables + grabado hundido")
    ap.add_argument("--master-finishes", nargs="+",
                    default=["pulido", "mate", "rayado_vertical", "martillado"],
                    choices=list(FINISHES), help="acabados del GLB maestro")
    ap.add_argument("--colors", nargs="+", default=["oro_amarillo", "oro_rosa", "oro_blanco"],
                    choices=list(METALS), help="colores conmutables")
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
        if args.master:
            colors = [(c, METALS[c]) for c in args.colors]
            ring_eng, plug = prepare_engraving(ring, logo, args.angle)
            out = os.path.join(args.out, f"{stem}__master.glb")
            build_master_glb(ring_eng, plug, args.master_finishes, colors, out)
            print("  ->", out, "| acabados:", ", ".join(args.master_finishes),
                  "| colores:", ", ".join(args.colors))
            n += 1
        elif args.multicolor:
            # un GLB por acabado, con los 3 colores conmutables dentro
            colors = [(c, METALS[c]) for c in args.colors]
            for fin in finishes:
                out = os.path.join(args.out, f"{stem}__tricolor__{fin}.glb")
                build_glb(ring, logo, args.colors[0], fin, out, args.angle)
                add_color_variants(out, colors)
                print("  ->", out, "(colores:", ", ".join(args.colors) + ")")
                n += 1
        else:
            for metal in metals:
                for fin in finishes:
                    out = os.path.join(args.out, f"{stem}__{metal}__{fin}.glb")
                    build_glb(ring, logo, metal, fin, out, args.angle)
                    print("  ->", out)
                    n += 1
    print(f"\n{n} GLB generados en '{args.out}/'")


if __name__ == "__main__":
    main()
