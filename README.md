# Integración iJewel3D — Visor 3D + configurador de materiales

Este repo contiene lo necesario para mostrar tus modelos de joyería en 3D con
**iJewel3D** y permitir el cambio de materiales (oro amarillo, blanco, platino, etc.)
en tiempo real.

## ¿Qué hay aquí?

| Archivo | Para qué sirve |
|---|---|
| `index.html`, `styles.css`, `app.js` | **Página de prueba independiente** (HTML simple). Úsala para testear tus modelos rápido, sin Lovable. Abre `index.html` en el navegador. |
| `lovable/IJewelViewer.tsx` | **Componente React** listo para pegar en tu proyecto de **Lovable**, usando el visor de **iJewel3D**. |
| `lovable/CustomJewelryViewer.tsx` | **Visor propio** (Three.js vía `@react-three/fiber`), en paralelo al de iJewel. Color, iluminación y ancho de banda en tiempo real. |
| `lovable/GlbUploader.tsx` | Componente para subir `.glb` a Supabase Storage y alimentar al visor propio. |
| `supabase/schema.sql` | Tabla `jewelry_models` + bucket de Storage + políticas RLS que necesita `GlbUploader.tsx`. |

## Tu situación

Tu página real está en **Lovable** (`kindred-connect-cloud.lovable.app`), que genera
una app en **React**. Este repositorio de GitHub está separado de ese proyecto.

Tienes dos caminos:

### Opción A — Editar directo en Lovable (más rápido)
1. En Lovable, crea `src/components/IJewelViewer.tsx` y pega el contenido de
   `lovable/IJewelViewer.tsx`.
2. Úsalo en la página donde quieras el visor:
   ```tsx
   import IJewelViewer from "@/components/IJewelViewer";

   <IJewelViewer modelUrl="https://.../tu-modelo.glb" />
   ```

### Opción B — Conectar Lovable con GitHub (para que yo edite el código real)
En Lovable: menú **GitHub → Connect to GitHub**. Eso crea/sincroniza un repo con
el código de tu app. Si me pasas ese repo, trabajo directamente sobre él.

## Pasos para que funcione el cambio de materiales

1. **Sube tus modelos** a iJewel3D y configura el **MaterialConfiguratorPlugin**
   (define las variaciones: oro amarillo, blanco, platino…).
2. Copia la **URL del modelo** (.glb) desde iJewel3D Drive.
3. Pásala como `modelUrl` al componente / a `MODEL_URL` en `app.js`.

El configurador de materiales aparece **dentro del propio visor** cuando el modelo
tiene esa configuración. Los botones extra en `app.js` son opcionales, por si
quieres tu propia UI de materiales fuera del visor.

## Documentación oficial (iJewel3D)
- Visor: https://docs.ijewel3d.com/viewer/introduction.html
- Embedding: https://docs.ijewel3d.com/integrations/embedding.html
- Configurador de anillos: https://docs.ijewel3d.com/ring-configurator/introduction.html

## Visor propio (Three.js) — en paralelo a iJewel

`CustomJewelryViewer.tsx` es una alternativa construida con Three.js
(`@react-three/fiber` + `@react-three/drei`, el mismo motor que usa iJewel por
debajo) que permite, en tiempo real: cambiar color/acabado del metal, ajustar
la iluminación (exposición sobre un HDRI), y cambiar el ancho de la pieza.
No sustituye a `IJewelViewer.tsx` — conviven, para poder comparar calidad.

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
