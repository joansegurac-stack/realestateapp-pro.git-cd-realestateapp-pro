// app.js — Lógica del visor iJewel para la página de prueba (HTML simple)
//
// Aquí cargamos el modelo 3D y conectamos con el configurador de materiales.
// Sustituye las URLs de ejemplo por las de TUS modelos de iJewel3D.

// 1) URL de tu modelo (.glb / .glb comprimido) exportado o alojado en iJewel3D Drive.
//    Lo obtienes desde tu cuenta de iJewel3D (botón "Embed" / "Share").
const MODEL_URL = "PON_AQUI_LA_URL_DE_TU_MODELO.glb";

// 2) Esperamos a que el web component del visor esté listo.
const viewer = document.getElementById("ijewel-viewer");

async function init() {
  // El web component <webgi-viewer> expone una promesa/initialize según versión.
  // Patrón recomendado por iJewel: esperar a 'initialize' y luego cargar el modelo.
  await customElements.whenDefined("webgi-viewer");

  // Algunas versiones exponen viewer.initialize(); otras cargan vía atributo.
  // Cargamos el modelo de forma defensiva:
  try {
    if (typeof viewer.load === "function") {
      await viewer.load(MODEL_URL);
    } else {
      // Fallback: asignar como atributo de modelo
      viewer.setAttribute("model", MODEL_URL);
    }
  } catch (err) {
    console.error("No se pudo cargar el modelo. Revisa MODEL_URL:", err);
  }

  setupMaterialButtons();
}

// 3) Botones de materiales personalizados (opcional).
//    El configurador nativo de iJewel ya sale dentro del visor si tu modelo
//    tiene el MaterialConfiguratorPlugin configurado en iJewel3D.
//    Esto es por si quieres TUS propios botones fuera del visor.
function setupMaterialButtons() {
  const container = document.getElementById("material-buttons");

  // Define aquí las variaciones que configuraste en iJewel
  // (los nombres/índices deben coincidir con tu configuración del modelo).
  const materiales = [
    { label: "Oro amarillo", variation: 0 },
    { label: "Oro blanco", variation: 1 },
    { label: "Oro rosa", variation: 2 },
    { label: "Platino", variation: 3 },
  ];

  materiales.forEach((m) => {
    const btn = document.createElement("button");
    btn.textContent = m.label;
    btn.addEventListener("click", () => applyMaterial(m.variation));
    container.appendChild(btn);
  });
}

// 4) Aplicar una variación de material vía el MaterialConfiguratorPlugin.
//    La API exacta depende de la versión del visor; este es el patrón típico.
function applyMaterial(variationIndex) {
  try {
    const plugin =
      viewer.getPlugin?.("MaterialConfiguratorPlugin") ||
      viewer.plugins?.MaterialConfiguratorPlugin;

    if (plugin && typeof plugin.applyVariation === "function") {
      plugin.applyVariation(variationIndex);
    } else {
      console.warn(
        "MaterialConfiguratorPlugin no disponible. Verifica que el modelo lo tenga configurado en iJewel3D."
      );
    }
  } catch (err) {
    console.error("Error al cambiar material:", err);
  }
}

init();
