// IJewelEmbed.tsx
// Método VERIFICADO de embed de iJewel3D: iframe hacia la página alojada por
// iJewel (pestaña "Embed" del Playground → "Copy HTML code"). Sustituye a
// IJewelViewer.tsx (que asumía un bundle JS + web component <webgi-viewer>,
// método que no aplica a esta cuenta).
//
// Al ser un iframe de otro origen, el configurador de materiales (si el
// modelo lo tiene configurado en iJewel3D) aparece DENTRO del propio iframe;
// no se puede controlar por JS desde fuera.
//
// Cómo usarlo en Lovable:
//   1. Crea src/components/IJewelEmbed.tsx y pega este contenido.
//   2. <IJewelEmbed slug="JxaASfzvTxOAxZxy2Ijw0g" title="Mi anillo" />

type Props = {
  /** El slug del archivo en iJewel Drive (parte final de la URL /drive/files/<slug>/...). */
  slug: string;
  /** Título accesible del iframe (nombre del modelo). */
  title?: string;
  /** Quita el logo/enlace de iJewel del embed. Por defecto true. */
  removeLogoLink?: boolean;
  /** Alto del visor. Por defecto 600px. */
  height?: number | string;
};

export default function IJewelEmbed({
  slug,
  title = "Visor 3D",
  removeLogoLink = true,
  height = 600,
}: Props) {
  const src = `https://ijewel3d.com/drive/files/${slug}/embedded?slug=${slug}&isRemoveLogoLink=${removeLogoLink}`;

  return (
    <iframe
      title={title}
      src={src}
      allow="camera; autoplay; fullscreen; xr-spatial-tracking; web-share"
      allowFullScreen
      style={{
        display: "block",
        width: "100%",
        height: typeof height === "number" ? `${height}px` : height,
        border: 0,
        borderRadius: 12,
        overflow: "hidden",
      }}
    />
  );
}
