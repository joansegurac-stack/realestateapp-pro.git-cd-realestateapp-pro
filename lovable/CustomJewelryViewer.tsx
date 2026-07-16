// CustomJewelryViewer.tsx
// Visor 3D propio (Three.js vía @react-three/fiber + drei), en PARALELO a
// IJewelViewer.tsx — no lo sustituye, es una alternativa para comparar.
//
// Requiere instalar en el proyecto de Lovable:
//   npm i three @react-three/fiber @react-three/drei
//
// Convención de modelado esperada en los .glb:
//   - Un morph target llamado "Width" (configurable con la prop widthMorphName)
//     en las mallas de la banda/pieza: influencia 0 = ancho mínimo, 1 = máximo.
//     El modelador debe exportarlo así desde Blender/etc.
//
// Cómo usarlo en Lovable:
//   1. Crea src/components/CustomJewelryViewer.tsx y pega este contenido.
//   2. <CustomJewelryViewer modelUrl="https://.../modelo.glb" />

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { Environment, OrbitControls, useGLTF } from "@react-three/drei";
import * as THREE from "three";

const DEFAULT_HDR = "https://demo-assets.pixotronics.com/pixo/hdr/gem_2.hdr";

const METAL_PRESETS = [
  { label: "Oro amarillo", color: "#d4af37", metalness: 1, roughness: 0.2 },
  { label: "Oro blanco", color: "#e8e8e8", metalness: 1, roughness: 0.15 },
  { label: "Oro rosa", color: "#e6b8a2", metalness: 1, roughness: 0.2 },
  { label: "Platino", color: "#e5e4e2", metalness: 1, roughness: 0.1 },
] as const;

type MaterialTint = {
  color: string;
  metalness: number;
  roughness: number;
};

function Model({
  url,
  width,
  widthMorphName,
  targetMaterial,
  tint,
  onMaterialNames,
}: {
  url: string;
  width: number;
  widthMorphName: string;
  targetMaterial: string | null;
  tint: MaterialTint;
  onMaterialNames: (names: string[]) => void;
}) {
  // Nota: se reutiliza la escena cacheada por useGLTF sin clonar. Si necesitas
  // varias instancias del MISMO modelo en la misma página a la vez, clónala
  // con SkeletonUtils.clone antes de mutarla.
  const { scene } = useGLTF(url);

  const materialsByName = useMemo(() => {
    const map = new Map<string, THREE.Material[]>();
    scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh) return;
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      for (const mat of mats) {
        if (!mat?.name) continue;
        const list = map.get(mat.name) ?? [];
        list.push(mat);
        map.set(mat.name, list);
      }
    });
    return map;
  }, [scene]);

  useEffect(() => {
    onMaterialNames(Array.from(materialsByName.keys()));
  }, [materialsByName, onMaterialNames]);

  // Ancho en tiempo real vía morph targets.
  useEffect(() => {
    scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      const dict = mesh.morphTargetDictionary;
      const influences = mesh.morphTargetInfluences;
      if (!dict || !influences) return;
      const idx = dict[widthMorphName];
      if (idx === undefined) return;
      influences[idx] = width;
    });
  }, [scene, width, widthMorphName]);

  // Color / acabado del material seleccionado.
  useEffect(() => {
    if (!targetMaterial) return;
    const mats = materialsByName.get(targetMaterial);
    if (!mats) return;
    for (const mat of mats) {
      const m = mat as THREE.MeshStandardMaterial;
      m.color.set(tint.color);
      m.metalness = tint.metalness;
      m.roughness = tint.roughness;
      m.needsUpdate = true;
    }
  }, [materialsByName, targetMaterial, tint]);

  return <primitive object={scene} />;
}

function ExposureControl({ intensity }: { intensity: number }) {
  const { gl } = useThree();
  useEffect(() => {
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = intensity;
  }, [gl, intensity]);
  return null;
}

type Props = {
  /** URL del modelo .glb (Supabase Storage, iJewel3D Drive, etc). */
  modelUrl: string;
  /** Nombre del morph target de ancho. Por defecto "Width". */
  widthMorphName?: string;
  /** URL del HDRI de iluminación. Opcional. */
  environment?: string;
  /** Alto del visor. Por defecto 600px. */
  height?: number | string;
};

export default function CustomJewelryViewer({
  modelUrl,
  widthMorphName = "Width",
  environment = DEFAULT_HDR,
  height = 600,
}: Props) {
  const [width, setWidth] = useState(0.5);
  const [exposure, setExposure] = useState(1);
  const [materialNames, setMaterialNames] = useState<string[]>([]);
  const [targetMaterial, setTargetMaterial] = useState<string | null>(null);
  const [tint, setTint] = useState<MaterialTint>({
    color: METAL_PRESETS[0].color,
    metalness: METAL_PRESETS[0].metalness,
    roughness: METAL_PRESETS[0].roughness,
  });

  const handleMaterialNames = useRef((names: string[]) => {
    setMaterialNames(names);
    setTargetMaterial((current) => current ?? names[0] ?? null);
  }).current;

  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
      <div
        style={{
          flex: "1 1 400px",
          height: typeof height === "number" ? `${height}px` : height,
          background: "#000",
          borderRadius: 12,
          overflow: "hidden",
        }}
      >
        <Canvas camera={{ position: [0, 0, 3], fov: 40 }}>
          <ExposureControl intensity={exposure} />
          <Suspense fallback={null}>
            <Model
              url={modelUrl}
              width={width}
              widthMorphName={widthMorphName}
              targetMaterial={targetMaterial}
              tint={tint}
              onMaterialNames={handleMaterialNames}
            />
            <Environment files={environment} />
          </Suspense>
          <OrbitControls enablePan={false} />
        </Canvas>
      </div>

      <aside style={{ flex: "0 0 220px", display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <label>Ancho: {Math.round(width * 100)}%</label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={width}
            onChange={(e) => setWidth(Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </div>

        <div>
          <label>Iluminación (exposición): {exposure.toFixed(2)}</label>
          <input
            type="range"
            min={0.2}
            max={2.5}
            step={0.05}
            value={exposure}
            onChange={(e) => setExposure(Number(e.target.value))}
            style={{ width: "100%" }}
          />
        </div>

        {materialNames.length > 0 && (
          <div>
            <label>Material a colorear</label>
            <select
              value={targetMaterial ?? ""}
              onChange={(e) => setTargetMaterial(e.target.value)}
              style={{ width: "100%" }}
            >
              {materialNames.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label>Acabado</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {METAL_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() =>
                  setTint({
                    color: preset.color,
                    metalness: preset.metalness,
                    roughness: preset.roughness,
                  })
                }
                style={{
                  background: preset.color,
                  border: "1px solid #0003",
                  borderRadius: 6,
                  padding: "6px 10px",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label>Color personalizado</label>
          <input
            type="color"
            value={tint.color}
            onChange={(e) => setTint((t) => ({ ...t, color: e.target.value }))}
            style={{ width: "100%" }}
          />
        </div>
      </aside>
    </div>
  );
}
