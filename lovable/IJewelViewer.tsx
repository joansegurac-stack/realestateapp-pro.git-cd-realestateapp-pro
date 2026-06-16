// IJewelViewer.tsx
// Componente React listo para PEGAR en tu proyecto de Lovable.
//
// Cómo usarlo en Lovable:
//   1. Crea un archivo nuevo, p.ej. src/components/IJewelViewer.tsx
//   2. Pega este contenido.
//   3. Úsalo en cualquier página:  <IJewelViewer modelUrl="https://.../tu-modelo.glb" />
//
// Carga el script del visor de iJewel una sola vez y renderiza el web component
// <webgi-viewer>. El configurador de materiales aparece dentro del visor si tu
// modelo tiene el MaterialConfiguratorPlugin configurado en iJewel3D.

import { useEffect, useRef } from "react";

// Permite usar el web component <webgi-viewer> dentro de JSX/TSX sin errores de tipos.
declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace JSX {
    interface IntrinsicElements {
      "webgi-viewer": React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement>,
        HTMLElement
      > & {
        src?: string;
        environment?: string;
      };
    }
  }
}

const VIEWER_BUNDLE = "https://releases.ijewel3d.com/libs/webgi-v0/bundle-0.22.0.js";
const MINI_VIEWER = "https://releases.ijewel3d.com/libs/mini-viewer/0.6.8/bundle.nowebgi.iife.js";
const DEFAULT_HDR = "https://demo-assets.pixotronics.com/pixo/hdr/gem_2.hdr";

// Carga el script del visor una sola vez en toda la app.
function useIJewelScript() {
  useEffect(() => {
    if (document.querySelector(`script[data-ijewel="viewer"]`)) return;
    const s = document.createElement("script");
    s.type = "module";
    s.src = VIEWER_BUNDLE;
    s.dataset.ijewel = "viewer";
    document.head.appendChild(s);
  }, []);
}

type Props = {
  /** URL de tu modelo (.glb) en iJewel3D Drive */
  modelUrl: string;
  /** URL del entorno HDR (iluminación). Opcional. */
  environment?: string;
  /** Alto del visor. Por defecto 600px. */
  height?: number | string;
};

export default function IJewelViewer({
  modelUrl,
  environment = DEFAULT_HDR,
  height = 600,
}: Props) {
  useIJewelScript();
  const viewerRef = useRef<HTMLElement & { load?: (url: string) => Promise<void> }>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      // Esperamos a que el web component esté definido.
      if (window.customElements) {
        await window.customElements.whenDefined("webgi-viewer").catch(() => {});
      }
      const el = viewerRef.current;
      if (!el || cancelled) return;

      try {
        if (typeof el.load === "function") {
          await el.load(modelUrl);
        } else {
          el.setAttribute("model", modelUrl);
        }
      } catch (err) {
        console.error("[iJewel] No se pudo cargar el modelo:", err);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [modelUrl]);

  return (
    <webgi-viewer
      ref={viewerRef as React.Ref<HTMLElement>}
      src={MINI_VIEWER}
      environment={environment}
      style={{
        display: "block",
        width: "100%",
        height: typeof height === "number" ? `${height}px` : height,
        background: "#000",
        borderRadius: "12px",
        overflow: "hidden",
      }}
    />
  );
}
