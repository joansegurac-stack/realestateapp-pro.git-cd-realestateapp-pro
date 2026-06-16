# Integración iJewel3D — Visor 3D + configurador de materiales

Este repo contiene lo necesario para mostrar tus modelos de joyería en 3D con
**iJewel3D** y permitir el cambio de materiales (oro amarillo, blanco, platino, etc.)
en tiempo real.

## ¿Qué hay aquí?

| Archivo | Para qué sirve |
|---|---|
| `index.html`, `styles.css`, `app.js` | **Página de prueba independiente** (HTML simple). Úsala para testear tus modelos rápido, sin Lovable. Abre `index.html` en el navegador. |
| `lovable/IJewelViewer.tsx` | **Componente React** listo para pegar en tu proyecto de **Lovable** (que es donde está tu web real). |

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

## Documentación oficial
- Visor: https://docs.ijewel3d.com/viewer/introduction.html
- Embedding: https://docs.ijewel3d.com/integrations/embedding.html
- Configurador de anillos: https://docs.ijewel3d.com/ring-configurator/introduction.html
