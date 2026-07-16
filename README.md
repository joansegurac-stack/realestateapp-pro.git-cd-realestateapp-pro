# Integración iJewel3D — Visor 3D + configurador de materiales

Este repo contiene lo necesario para mostrar tus modelos de joyería en 3D con
**iJewel3D** y permitir el cambio de materiales (oro amarillo, blanco, platino, etc.)
en tiempo real.

## ¿Qué hay aquí?

| Archivo | Para qué sirve |
|---|---|
| `index.html`, `styles.css` | **Página de prueba independiente** (HTML simple). Abre `index.html` en el navegador para ver el embed de iJewel funcionando. |
| `lovable/IJewelEmbed.tsx` | **Componente React** listo para pegar en tu proyecto de **Lovable** — método de embed VERIFICADO (iframe) para tu cuenta de iJewel3D. |
| `lovable/CustomJewelryViewer.tsx` | **Visor propio** (Three.js vía `@react-three/fiber`), en paralelo al de iJewel. Color, iluminación y ancho de banda en tiempo real. |
| `lovable/GlbUploader.tsx` | Componente para subir `.glb` a Supabase Storage y alimentar al visor propio. |
| `supabase/schema.sql` | Tabla `jewelry_models` + bucket de Storage + políticas RLS que necesita `GlbUploader.tsx`. |

## Tu situación

Tu página real está en **Lovable** (`kindred-connect-cloud.lovable.app`), que genera
una app en **React**. Este repositorio de GitHub está separado de ese proyecto.

Tienes dos caminos:

### Opción A — Editar directo en Lovable (más rápido)
1. En Lovable, crea `src/components/IJewelEmbed.tsx` y pega el contenido de
   `lovable/IJewelEmbed.tsx`.
2. Úsalo en la página donde quieras el visor:
   ```tsx
   import IJewelEmbed from "@/components/IJewelEmbed";

   <IJewelEmbed slug="JxaASfzvTxOAxZxy2Ijw0g" title="Mi anillo" />
   ```
   El `slug` es la parte final de la URL de tu archivo en iJewel Drive
   (`/drive/files/<slug>/...`).

### Opción B — Conectar Lovable con GitHub (para que yo edite el código real)
En Lovable: menú **GitHub → Connect to GitHub**. Eso crea/sincroniza un repo con
el código de tu app. Si me pasas ese repo, trabajo directamente sobre él.

## Cómo funciona el embed de iJewel (método verificado)

Tu cuenta de iJewel3D usa el método de **iframe embed**: en el Playground,
pestaña **"Embed"** → botón **"Copy HTML code"** (o "View code"), te da un
`<iframe>` cuyo `src` apunta a una página alojada por iJewel
(`https://ijewel3d.com/drive/files/<slug>/embedded?slug=<slug>`). Esa página
ya trae el modelo y, si está configurado, el **MaterialConfiguratorPlugin**
con sus variaciones (oro amarillo, blanco, platino…) integrados dentro del
propio iframe.

Al ser un iframe de otro origen, **no se puede controlar desde fuera con
JS** (no hay acceso a `viewer.getPlugin(...)` como en una integración por
bundle/web-component). Los botones de material, si los quieres fuera del
visor, tendrían que ser variaciones que el propio iJewel exponga por URL o
mensajes `postMessage` — revisa la documentación de embedding si tu cuenta
lo soporta.

## Documentación oficial (iJewel3D)
- Visor: https://docs.ijewel3d.com/viewer/introduction.html
- Embedding: https://docs.ijewel3d.com/integrations/embedding.html
- Configurador de anillos: https://docs.ijewel3d.com/ring-configurator/introduction.html

## Visor propio (Three.js) — en paralelo a iJewel

`CustomJewelryViewer.tsx` es una alternativa construida con Three.js
(`@react-three/fiber` + `@react-three/drei`, el mismo motor que usa iJewel por
debajo) que permite, en tiempo real: cambiar color/acabado del metal, ajustar
la iluminación (exposición sobre un HDRI), y cambiar el ancho de la pieza.
No sustituye al embed de iJewel — conviven, para poder comparar calidad.

**Importante:** el iframe embed de iJewel (`IJewelEmbed.tsx`) NO expone una
URL directa del `.glb` — solo carga su propia página con el modelo dentro.
Para `CustomJewelryViewer.tsx` necesitas el archivo `.glb` en sí (por eso
existe `GlbUploader.tsx`: para subir tus modelos a tu propio Storage y
obtener una URL directa que Three.js sí pueda cargar).

### 1. Instalar dependencias en tu proyecto de Lovable
```
npm i three @react-three/fiber @react-three/drei
```

### 2. Convención de modelado para el ancho en tiempo real
Los `.glb` deben venir del modelador con un **morph target llamado `Width`**
en las mallas de la banda/pieza:
- Influencia `0` = ancho mínimo
- Influencia `1` = ancho máximo

El visor interpola entre esas dos formas clave con un slider. Si tu
convención de nombre es otra, pásala con la prop `widthMorphName`.

### 3. Subida de modelos (Supabase)
1. En el SQL editor de tu proyecto Supabase (el que ya usa Lovable), ejecuta
   `supabase/schema.sql`. Crea la tabla `jewelry_models` y el bucket
   `jewelry-models` con sus políticas.
2. Pega `lovable/GlbUploader.tsx` en `src/components/GlbUploader.tsx`.
3. Úsalo junto al visor:
   ```tsx
   import { useState } from "react";
   import GlbUploader from "@/components/GlbUploader";
   import CustomJewelryViewer from "@/components/CustomJewelryViewer";

   function Page() {
     const [modelUrl, setModelUrl] = useState<string | null>(null);
     return (
       <>
         <GlbUploader onSelectModel={setModelUrl} />
         {modelUrl && <CustomJewelryViewer modelUrl={modelUrl} />}
       </>
     );
   }
   ```

### Limitaciones a tener en cuenta
- El cambio de color se aplica por **nombre de material** (el selector lista
  los materiales del modelo cargado); si el modelador no nombra el material
  del metal de forma reconocible, el usuario tendrá que probar cuál es.
- `CustomJewelryViewer` reutiliza la escena cacheada por `useGLTF` sin
  clonarla — si necesitas varias instancias del mismo modelo a la vez en la
  misma página, clónala con `SkeletonUtils.clone` antes de mutarla.
