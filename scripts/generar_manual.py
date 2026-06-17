# -*- coding: utf-8 -*-
"""
Generador del Manual Interactivo (PDF) del Playground iJewel3D.

Crea un PDF en español, con:
  - Portada
  - Índice navegable (enlaces internos clicables)
  - Marcadores / outline (panel lateral del lector de PDF)
  - Cabeceras, pies con numeración y enlaces "volver al índice"
  - Cajas de nota, pasos y bloques de código

Uso:  python3 scripts/generar_manual.py
Salida:  Manual_Playground_iJewel3D_ES.pdf  (en la raíz del repo)
"""

from fpdf import FPDF

# --------------------------------------------------------------------------
# Paleta de color (coincide con el styles.css del proyecto: tema oscuro + dorado)
# --------------------------------------------------------------------------
ORO       = (201, 162, 39)    # --accent  #c9a227
TINTA     = (24, 26, 33)      # texto principal
GRIS      = (110, 116, 128)   # texto secundario
GRIS_CLARO= (235, 236, 240)   # fondos suaves
AZULOSCURO= (15, 17, 21)      # --bg
PANEL     = (243, 244, 246)
CODIGO_BG = (28, 32, 40)
CODIGO_TX = (220, 224, 232)
BLANCO    = (255, 255, 255)

ANCHO_UTIL = 210 - 18 - 18    # A4 menos márgenes


class Manual(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(18, 20, 18)
        self.indice_link = None          # enlace interno al índice
        self.titulo_actual = ""
        self.es_portada = False

    # -------- Cabecera y pie en cada página (excepto portada) --------
    def header(self):
        if self.es_portada:
            return
        self.set_y(8)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 5, "Manual del Playground iJewel3D", align="L")
        self.cell(0, 5, self.titulo_actual, align="R")
        self.set_draw_color(*ORO)
        self.set_line_width(0.4)
        self.line(18, 15, 210 - 18, 15)
        self.set_y(20)

    def footer(self):
        if self.es_portada:
            return
        self.set_y(-14)
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.2)
        self.line(18, self.get_y(), 210 - 18, self.get_y())
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 6, f"Pagina {self.page_no()}", align="C")
        # Enlace "volver al indice" a la derecha
        if self.indice_link and self.page_no() > 2:
            self.set_xy(210 - 18 - 40, -12)
            self.set_text_color(*ORO)
            self.cell(40, 6, "Volver al indice  >", align="R", link=self.indice_link)


def t(txt):
    """Codifica a latin-1 (fuentes core) sustituyendo lo no soportado."""
    reemplazos = {
        "—": "-", "–": "-", "‘": "'", "’": "'",
        "“": '"', "”": '"', "…": "...", "•": "-",
        "€": "EUR", "→": ">", "✓": "OK", " ": " ",
    }
    for a, b in reemplazos.items():
        txt = txt.replace(a, b)
    return txt.encode("latin-1", "replace").decode("latin-1")


# ==========================================================================
#  Bloques reutilizables de maquetación
# ==========================================================================
def titulo_seccion(pdf, numero, texto, link):
    """Encabezado grande de capítulo + marcador en el outline."""
    pdf.set_link(link)                      # destino del enlace interno
    pdf.start_section(t(f"{numero}. {texto}"))
    pdf.titulo_actual = t(texto)
    pdf.ln(2)
    pdf.set_fill_color(*ORO)
    pdf.set_text_color(*BLANCO)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(11, 11, str(numero), align="C", fill=True)
    pdf.set_text_color(*TINTA)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_x(pdf.get_x() + 3)
    pdf.multi_cell(0, 11, t(texto))
    pdf.set_draw_color(*ORO)
    pdf.set_line_width(0.3)
    pdf.line(18, pdf.get_y() + 1, 210 - 18, pdf.get_y() + 1)
    pdf.ln(5)


def subtitulo(pdf, texto):
    pdf.ln(1)
    pdf.set_text_color(*ORO)
    pdf.set_font("Helvetica", "B", 12.5)
    pdf.multi_cell(0, 7, t(texto))
    pdf.ln(1)


def parrafo(pdf, texto):
    pdf.set_text_color(*TINTA)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.multi_cell(0, 5.6, t(texto))
    pdf.ln(1.5)


def vinetas(pdf, items):
    pdf.set_font("Helvetica", "", 10.5)
    for it in items:
        pdf.set_text_color(*ORO)
        pdf.set_font("Helvetica", "B", 10.5)
        x = pdf.get_x()
        pdf.cell(5, 5.6, t("-"))
        pdf.set_text_color(*TINTA)
        pdf.set_font("Helvetica", "", 10.5)
        pdf.multi_cell(ANCHO_UTIL - 5, 5.6, t(it))
        pdf.set_x(x)
    pdf.ln(1.5)


def pasos(pdf, items):
    pdf.set_font("Helvetica", "", 10.5)
    for i, it in enumerate(items, 1):
        x = pdf.get_x()
        pdf.set_fill_color(*ORO)
        pdf.set_text_color(*BLANCO)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(6, 6, str(i), align="C", fill=True)
        pdf.set_x(x + 8)
        pdf.set_text_color(*TINTA)
        pdf.set_font("Helvetica", "", 10.5)
        pdf.multi_cell(ANCHO_UTIL - 8, 6, t(it))
        pdf.ln(0.5)
    pdf.ln(1.5)


def nota(pdf, titulo, texto):
    """Caja de aviso/consejo."""
    pdf.ln(1)
    alto_linea = 5.2
    ancho_texto = ANCHO_UTIL - 12
    # Medir cuantas lineas ocupa el cuerpo (sin escribir nada)
    pdf.set_font("Helvetica", "", 10)
    lineas = pdf.multi_cell(ancho_texto, alto_linea, t(texto),
                            dry_run=True, output="LINES")
    alto = 7 + len(lineas) * alto_linea + 4   # titulo + cuerpo + margenes
    # Salto de pagina si no cabe entera
    if pdf.get_y() + alto > 275:
        pdf.add_page()
    y0 = pdf.get_y()
    # Caja
    pdf.set_fill_color(252, 248, 232)
    pdf.set_draw_color(*ORO)
    pdf.set_line_width(0.3)
    pdf.rect(18, y0, ANCHO_UTIL, alto, style="DF")
    pdf.set_fill_color(*ORO)
    pdf.rect(18, y0, 2, alto, style="F")   # barra lateral
    # Titulo
    pdf.set_xy(24, y0 + 2)
    pdf.set_text_color(*ORO)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, t(titulo))
    # Cuerpo
    yy = y0 + 8
    pdf.set_text_color(*TINTA)
    pdf.set_font("Helvetica", "", 10)
    for linea in lineas:
        pdf.set_xy(24, yy)
        pdf.cell(ancho_texto, alto_linea, linea)
        yy += alto_linea
    pdf.set_y(y0 + alto + 3)


def codigo(pdf, lineas, titulo=None):
    if titulo:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*GRIS)
        pdf.cell(0, 5, t(titulo))
        pdf.ln(5)
    pdf.set_font("Courier", "", 9)
    alto_linea = 4.8
    alto = alto_linea * len(lineas) + 4
    y0 = pdf.get_y()
    # Salto de página si no cabe
    if y0 + alto > 277:
        pdf.add_page()
        y0 = pdf.get_y()
    pdf.set_fill_color(*CODIGO_BG)
    pdf.rect(18, y0, ANCHO_UTIL, alto, style="F")
    pdf.set_xy(22, y0 + 2)
    pdf.set_text_color(*CODIGO_TX)
    for ln in lineas:
        pdf.set_x(22)
        pdf.cell(0, alto_linea, t(ln))
        pdf.ln(alto_linea)
    pdf.set_y(y0 + alto + 3)
    pdf.set_text_color(*TINTA)


def tabla(pdf, encabezados, filas, anchos):
    alto_linea = 5.0
    pad = 1.5

    def pintar_encabezado():
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_fill_color(*TINTA)
        pdf.set_text_color(*BLANCO)
        x0 = 18
        for h, w in zip(encabezados, anchos):
            pdf.set_xy(x0, pdf.get_y())
            pdf.cell(w, 8, t("  " + h), border=0, align="L", fill=True)
            x0 += w
        pdf.ln(8)

    pintar_encabezado()
    pdf.set_font("Helvetica", "", 9.5)
    fila_par = False
    for fila in filas:
        # Numero de lineas de cada celda con la fuente actual
        lineas_por_celda = []
        for celda, w in zip(fila, anchos):
            lns = pdf.multi_cell(w - 2 * pad, alto_linea, t(celda),
                                 dry_run=True, output="LINES")
            lineas_por_celda.append(lns)
        max_lineas = max(len(l) for l in lineas_por_celda)
        alto = max_lineas * alto_linea + 2 * pad
        if pdf.get_y() + alto > 275:
            pdf.add_page()
            pintar_encabezado()
            pdf.set_font("Helvetica", "", 9.5)
        y0 = pdf.get_y()
        # Fondo de la fila
        pdf.set_fill_color(*(PANEL if fila_par else BLANCO))
        pdf.rect(18, y0, sum(anchos), alto, style="F")
        # Texto de cada celda
        x = 18
        pdf.set_text_color(*TINTA)
        for lns, w in zip(lineas_por_celda, anchos):
            yy = y0 + pad
            for linea in lns:
                pdf.set_xy(x + pad, yy)
                pdf.cell(w - 2 * pad, alto_linea, linea)
                yy += alto_linea
            x += w
        # Linea separadora
        pdf.set_draw_color(225, 225, 225)
        pdf.set_line_width(0.15)
        pdf.line(18, y0 + alto, 18 + sum(anchos), y0 + alto)
        pdf.set_xy(18, y0 + alto)
        fila_par = not fila_par
    pdf.ln(3)


# ==========================================================================
#  Construcción del documento
# ==========================================================================
def construir():
    pdf = Manual()
    pdf.set_title("Manual del Playground iJewel3D")
    pdf.set_author("Equipo joyeria 3D")
    pdf.set_lang("es")

    # Reservamos enlaces internos (uno por capítulo + índice)
    L_INDICE = pdf.add_link()
    links = [pdf.add_link() for _ in range(9)]
    pdf.indice_link = L_INDICE
    # Placeholder de pagina para poder enlazar hacia adelante (se reasigna en cada capitulo)
    for L in [L_INDICE] + links:
        pdf.set_link(L, page=1)

    # ---------------- PORTADA ----------------
    pdf.es_portada = True
    pdf.add_page()
    pdf.set_fill_color(*AZULOSCURO)
    pdf.rect(0, 0, 210, 297, style="F")
    # Franja dorada superior
    pdf.set_fill_color(*ORO)
    pdf.rect(0, 70, 210, 1.2, style="F")
    pdf.rect(0, 150, 210, 1.2, style="F")

    pdf.set_xy(0, 90)
    pdf.set_text_color(*ORO)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, t("M A N U A L   I N T E R A C T I V O"), align="C")
    pdf.ln(14)
    pdf.set_text_color(*BLANCO)
    pdf.set_font("Helvetica", "B", 34)
    pdf.cell(0, 16, t("Playground iJewel3D"), align="C")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(225, 226, 230)
    pdf.cell(0, 8, t("Visor 3D de joyeria + configurador de materiales"), align="C")
    pdf.ln(9)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 7, t("Como funciona todo el programa, de pe a pa"), align="C")

    pdf.set_xy(0, 250)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 6, t("Documento generado automaticamente - Edicion en espanol"), align="C")
    pdf.ln(6)
    pdf.cell(0, 6, t("Consejo: usa el indice de la pagina siguiente o el panel de marcadores de tu lector de PDF."), align="C")
    pdf.es_portada = False

    # ---------------- ÍNDICE ----------------
    pdf.add_page()
    pdf.set_link(L_INDICE)
    pdf.start_section(t("Indice"))
    pdf.titulo_actual = t("Indice")
    pdf.set_text_color(*TINTA)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, t("Indice"))
    pdf.ln(14)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(0, 5, t("Toca cualquier titulo para saltar directamente a ese capitulo. "
                           "Tambien puedes abrir el panel de marcadores (bookmarks) de tu visor de PDF."))
    pdf.ln(4)

    capitulos = [
        ("Que es este programa (vision general)",
         "Para que sirve y que problema resuelve."),
        ("Conceptos clave: iJewel3D, webgi y GLB",
         "El vocabulario imprescindible antes de empezar."),
        ("Estructura del proyecto (archivo por archivo)",
         "Que hace cada fichero del repositorio."),
        ("El Playground paso a paso (index.html, styles.css, app.js)",
         "Como funciona la pagina de prueba por dentro."),
        ("Como probarlo en tu ordenador",
         "Arrancar la pagina en local en 3 pasos."),
        ("Poner TU modelo y configurar materiales",
         "De iJewel3D Drive a la pantalla, con tus joyas."),
        ("Integracion en Lovable (componente React)",
         "Llevar el visor a tu web real."),
        ("Resolucion de problemas (FAQ)",
         "Que hacer cuando algo no carga."),
        ("Glosario y enlaces oficiales",
         "Terminos y documentacion de referencia."),
    ]
    for i, (titulo, desc) in enumerate(capitulos, 1):
        y = pdf.get_y()
        pdf.set_fill_color(*ORO)
        pdf.set_text_color(*BLANCO)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(8, 8, str(i), align="C", fill=True, link=links[i - 1])
        pdf.set_x(pdf.get_x() + 3)
        pdf.set_text_color(*TINTA)
        pdf.set_font("Helvetica", "B", 11.5)
        pdf.cell(0, 8, t(titulo), link=links[i - 1])
        pdf.ln(7.5)
        pdf.set_x(29)
        pdf.set_text_color(*GRIS)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(0, 5, t(desc), link=links[i - 1])
        pdf.ln(8.5)
        pdf.set_draw_color(225, 225, 225)
        pdf.set_line_width(0.2)
        pdf.line(18, pdf.get_y() - 1, 210 - 18, pdf.get_y() - 1)
        pdf.ln(2)

    # =====================================================================
    # CAP 1
    # =====================================================================
    pdf.add_page()
    titulo_seccion(pdf, 1, "Que es este programa (vision general)", links[0])
    parrafo(pdf, "Este proyecto es un visor 3D para joyeria. Permite mostrar tus piezas "
                 "(anillos, colgantes, pendientes...) girandolas en 360 grados, con zoom, y "
                 "cambiando el material en tiempo real (oro amarillo, oro blanco, oro rosa, "
                 "platino, etc.) directamente en el navegador.")
    parrafo(pdf, "Internamente se apoya en iJewel3D, un servicio especializado en visualizacion "
                 "de joyeria que aporta el motor 3D (llamado webgi) y un configurador de "
                 "materiales. Tu solo necesitas subir tus modelos a iJewel3D y conectar su URL.")
    subtitulo(pdf, "Que incluye el repositorio")
    vinetas(pdf, [
        "Un \"Playground\" o pagina de prueba en HTML puro (index.html + styles.css + app.js) "
        "para ver tus modelos al instante, sin frameworks.",
        "Un componente React (lovable/IJewelViewer.tsx) listo para pegar en tu web real, que "
        "esta construida en la plataforma Lovable.",
    ])
    nota(pdf, "Que es el \"Playground\"",
         "En este manual llamamos Playground a la pagina de prueba independiente (index.html). "
         "Es tu banco de pruebas: abres un archivo en el navegador, ves el modelo y compruebas "
         "que todo funciona antes de llevarlo a la web definitiva.")
    subtitulo(pdf, "El flujo en una frase")
    parrafo(pdf, "Subes tu joya a iJewel3D > copias la URL del modelo (.glb) > la pegas en el "
                 "codigo > abres la pagina > giras la pieza y cambias materiales.")

    # =====================================================================
    # CAP 2
    # =====================================================================
    pdf.add_page()
    titulo_seccion(pdf, 2, "Conceptos clave: iJewel3D, webgi y GLB", links[1])
    parrafo(pdf, "Antes de tocar el codigo conviene tener claro el vocabulario. Son pocos "
                 "terminos y se repiten en todo el proyecto.")
    tabla(pdf,
          ["Termino", "Que es"],
          [
              ["iJewel3D", "Servicio/plataforma especializado en mostrar joyeria en 3D. Aloja tus "
                           "modelos y ofrece el motor y el configurador de materiales."],
              ["webgi", "El motor 3D (renderizado WebGL) que usa iJewel3D. Se carga como un "
                        "componente web llamado <webgi-viewer>."],
              ["<webgi-viewer>", "Etiqueta HTML personalizada (web component) que pinta el visor "
                                 "3D en la pagina. Se comporta como cualquier elemento HTML."],
              ["GLB / .glb", "El formato de archivo del modelo 3D (geometria + materiales + "
                             "texturas en un solo fichero). Es lo que carga el visor."],
              ["HDR", "Imagen de iluminacion del entorno. Hace que el oro y las gemas reflejen "
                      "luz de forma realista."],
              ["MaterialConfiguratorPlugin", "El modulo de iJewel3D que define las variaciones de "
                                             "material (oro amarillo, blanco, platino...) de un modelo."],
              ["Lovable", "La plataforma no-code/low-code donde vive tu web real (genera una app "
                          "en React)."],
          ],
          [40, ANCHO_UTIL - 40])
    nota(pdf, "Idea importante",
         "El configurador de materiales NO se programa aqui: se define en iJewel3D al preparar el "
         "modelo. Si tu modelo trae ese plugin configurado, los botones de material aparecen solos "
         "dentro del visor.")

    # =====================================================================
    # CAP 3
    # =====================================================================
    pdf.add_page()
    titulo_seccion(pdf, 3, "Estructura del proyecto (archivo por archivo)", links[2])
    parrafo(pdf, "El repositorio es deliberadamente pequeno. Cada archivo tiene un papel claro:")
    tabla(pdf,
          ["Archivo", "Para que sirve"],
          [
              ["index.html", "La pagina del Playground. Carga el motor del visor, define la "
                             "etiqueta <webgi-viewer> y el panel lateral."],
              ["styles.css", "Los estilos (tema oscuro con acento dorado, distribucion en dos "
                             "columnas, diseno responsive)."],
              ["app.js", "La logica: carga el modelo 3D y crea los botones de material "
                         "personalizados (opcionales)."],
              ["lovable/IJewelViewer.tsx", "Componente React equivalente, para pegar en tu "
                                           "proyecto de Lovable."],
              ["README.md", "Resumen rapido del proyecto y las dos vias de trabajo "
                            "(editar en Lovable o conectar GitHub)."],
          ],
          [48, ANCHO_UTIL - 48])
    subtitulo(pdf, "Dos caminos de trabajo")
    vinetas(pdf, [
        "Opcion A - Editar directo en Lovable: copias IJewelViewer.tsx dentro de tu proyecto y "
        "lo usas en la pagina que quieras. Es el camino mas rapido.",
        "Opcion B - Conectar Lovable con GitHub: sincronizas el codigo real en un repo para "
        "editarlo desde fuera de Lovable.",
    ])

    # =====================================================================
    # CAP 4
    # =====================================================================
    pdf.add_page()
    titulo_seccion(pdf, 4, "El Playground paso a paso", links[3])
    parrafo(pdf, "Veamos por dentro la pagina de prueba. Son tres archivos que trabajan juntos.")

    subtitulo(pdf, "4.1 index.html - el esqueleto")
    parrafo(pdf, "Lo primero que hace es cargar el motor del visor desde el CDN oficial de "
                 "iJewel3D (no hace falta instalar nada):")
    codigo(pdf, [
        '<script type="module"',
        '  src="https://releases.ijewel3d.com/libs/webgi-v0/bundle-0.22.0.js">',
        '</script>',
    ])
    parrafo(pdf, "Despues coloca el visor en la pagina. Fijate en dos atributos: src (el bundle "
                 "del visor, NO el modelo) y environment (la iluminacion HDR):")
    codigo(pdf, [
        '<webgi-viewer',
        '   id="ijewel-viewer"',
        '   src="...mini-viewer/0.6.8/bundle.nowebgi.iife.js"',
        '   environment="...gem_2.hdr">',
        '</webgi-viewer>',
    ])
    parrafo(pdf, "Junto al visor hay un panel lateral (<aside>) con un contenedor vacio "
                 "(id=\"material-buttons\") donde app.js anadira los botones de material.")

    subtitulo(pdf, "4.2 app.js - la logica")
    parrafo(pdf, "El paso mas importante: aqui defines la URL de TU modelo. Es la unica linea "
                 "que tienes que cambiar para ver tu propia joya:")
    codigo(pdf, [
        'const MODEL_URL = "PON_AQUI_LA_URL_DE_TU_MODELO.glb";',
    ])
    parrafo(pdf, "La funcion init() espera a que el visor este listo y carga el modelo de forma "
                 "defensiva (usa viewer.load() si existe; si no, asigna el atributo model):")
    codigo(pdf, [
        'await customElements.whenDefined("webgi-viewer");',
        'if (typeof viewer.load === "function") {',
        '  await viewer.load(MODEL_URL);',
        '} else {',
        '  viewer.setAttribute("model", MODEL_URL);',
        '}',
    ])
    parrafo(pdf, "Luego setupMaterialButtons() crea botones propios (Oro amarillo, blanco, "
                 "rosa, platino). Cada uno llama a applyMaterial(indice), que busca el "
                 "MaterialConfiguratorPlugin del visor y aplica la variacion:")
    codigo(pdf, [
        'const plugin = viewer.getPlugin?.("MaterialConfiguratorPlugin")',
        '            || viewer.plugins?.MaterialConfiguratorPlugin;',
        'if (plugin?.applyVariation) plugin.applyVariation(indice);',
    ])
    nota(pdf, "Los botones del panel son OPCIONALES",
         "Si tu modelo ya tiene el configurador en iJewel3D, las variaciones aparecen dentro del "
         "propio visor. El panel lateral solo sirve si quieres TU propia interfaz de materiales "
         "fuera del visor. Los indices (0,1,2,3) deben coincidir con tu configuracion en iJewel3D.")

    subtitulo(pdf, "4.3 styles.css - el aspecto")
    parrafo(pdf, "Define el tema visual con variables CSS: fondo oscuro (--bg), paneles, texto y "
                 "un acento dorado (--accent: #c9a227). El visor ocupa el 70% del alto de la "
                 "ventana y, en pantallas estrechas (menos de 860px), las dos columnas pasan a "
                 "una sola para verse bien en movil.")

    # =====================================================================
    # CAP 5
    # =====================================================================
    pdf.add_page()
    titulo_seccion(pdf, 5, "Como probarlo en tu ordenador", links[4])
    parrafo(pdf, "El Playground no necesita instalar nada (el visor viene del CDN). Pero como "
                 "usa modulos de JavaScript (type=\"module\"), conviene servirlo con un pequeno "
                 "servidor local en lugar de abrir el archivo con doble clic.")
    subtitulo(pdf, "Opcion rapida (recomendada)")
    pasos(pdf, [
        "Abre una terminal en la carpeta del proyecto.",
        "Arranca un servidor local. Con Python:  python3 -m http.server 8000",
        "Abre el navegador en  http://localhost:8000",
    ])
    parrafo(pdf, "Si prefieres Node, tienes alternativas equivalentes:")
    codigo(pdf, [
        '# Con Node (cualquiera de estas):',
        'npx serve .',
        'npx http-server -p 8000',
    ])
    nota(pdf, "Por que un servidor y no doble clic",
         "Los navegadores bloquean ciertos modulos y peticiones cuando la pagina se abre como "
         "archivo (file://). Sirviendola por http://localhost todo carga correctamente.")
    parrafo(pdf, "La primera vez veras el visor pero sin modelo (la URL de ejemplo no existe). "
                 "Eso es normal: en el siguiente capitulo pones tu modelo real.")

    # =====================================================================
    # CAP 6
    # =====================================================================
    pdf.add_page()
    titulo_seccion(pdf, 6, "Poner TU modelo y configurar materiales", links[5])
    parrafo(pdf, "Aqui esta el corazon del uso diario: pasar de un modelo en iJewel3D a verlo en "
                 "tu pantalla con cambio de materiales.")
    subtitulo(pdf, "Paso a paso")
    pasos(pdf, [
        "Sube tu modelo a iJewel3D y configura el MaterialConfiguratorPlugin: define las "
        "variaciones (oro amarillo, blanco, platino...).",
        "Copia la URL del modelo (.glb) desde iJewel3D Drive (boton Embed / Share).",
        "Pega esa URL en app.js, en la constante MODEL_URL.",
        "Guarda y recarga la pagina. Tu joya deberia aparecer y poder girarse.",
        "Comprueba el cambio de material: si configuraste el plugin, las opciones salen dentro "
        "del visor; si usas el panel propio, ajusta los indices a tu configuracion.",
    ])
    subtitulo(pdf, "Donde se cambia exactamente")
    codigo(pdf, [
        '// app.js  (linea 8)',
        'const MODEL_URL = "https://drive.ijewel3d.com/.../tu-anillo.glb";',
    ])
    subtitulo(pdf, "Ajustar los botones propios (opcional)")
    parrafo(pdf, "Si quieres tu propia botonera, edita la lista de materiales en app.js. El "
                 "campo variation es el indice de la variacion tal y como la definiste en "
                 "iJewel3D:")
    codigo(pdf, [
        'const materiales = [',
        '  { label: "Oro amarillo", variation: 0 },',
        '  { label: "Oro blanco",   variation: 1 },',
        '  { label: "Oro rosa",     variation: 2 },',
        '  { label: "Platino",      variation: 3 },',
        '];',
    ])
    nota(pdf, "Si cambias de joya tambien cambia el HDR (opcional)",
         "El atributo environment del <webgi-viewer> controla la iluminacion. Puedes usar el HDR "
         "de ejemplo (gem_2.hdr) o uno propio para que el reflejo del metal y las gemas se ajuste "
         "a tu estilo de catalogo.")

    # =====================================================================
    # CAP 7
    # =====================================================================
    pdf.add_page()
    titulo_seccion(pdf, 7, "Integracion en Lovable (componente React)", links[6])
    parrafo(pdf, "Tu web real esta en Lovable y se genera como una app React. El archivo "
                 "lovable/IJewelViewer.tsx es el mismo visor, pero empaquetado como componente "
                 "reutilizable.")
    subtitulo(pdf, "Como usarlo")
    pasos(pdf, [
        "En Lovable crea un archivo, por ejemplo src/components/IJewelViewer.tsx.",
        "Pega el contenido de lovable/IJewelViewer.tsx.",
        "Usalo en cualquier pagina pasandole la URL de tu modelo.",
    ])
    codigo(pdf, [
        'import IJewelViewer from "@/components/IJewelViewer";',
        '',
        '<IJewelViewer modelUrl="https://.../tu-modelo.glb" />',
    ])
    subtitulo(pdf, "Que hace el componente por dentro")
    vinetas(pdf, [
        "useIJewelScript(): inyecta el script del visor UNA sola vez en toda la app (evita "
        "cargarlo duplicado).",
        "Espera a customElements.whenDefined(\"webgi-viewer\") y carga el modelo con el mismo "
        "patron defensivo que app.js (load() o atributo model).",
        "Acepta props: modelUrl (obligatoria), environment (HDR opcional) y height (alto, 600px "
        "por defecto).",
        "Limpia el efecto al desmontar (flag cancelled) para no cargar modelos sobre un "
        "componente que ya no esta en pantalla.",
    ])
    nota(pdf, "Diferencia clave con el Playground",
         "El Playground (HTML) es para probar rapido. El componente React es para PRODUCCION en "
         "tu web. La logica de carga es la misma; cambia el envoltorio.")

    # =====================================================================
    # CAP 8
    # =====================================================================
    pdf.add_page()
    titulo_seccion(pdf, 8, "Resolucion de problemas (FAQ)", links[7])
    problemas = [
        ("El visor aparece negro / no se ve el modelo",
         "Casi siempre la URL del modelo es incorrecta o sigue siendo la de ejemplo. Revisa "
         "MODEL_URL en app.js (o la prop modelUrl en React) y abre la consola del navegador "
         "(F12) para ver el mensaje de error."),
        ("No aparecen las opciones de material dentro del visor",
         "El modelo no tiene el MaterialConfiguratorPlugin configurado en iJewel3D. Vuelve a "
         "iJewel3D y define las variaciones de material para ese modelo."),
        ("Mis botones del panel no cambian nada",
         "Los indices (variation: 0,1,2...) no coinciden con tu configuracion en iJewel3D, o el "
         "plugin no esta presente. Ajusta los indices a los de tu modelo."),
        ("Funciona con doble clic pero da errores raros",
         "Sirve la pagina por http://localhost (ver capitulo 5). Abrir como archivo (file://) "
         "puede bloquear modulos y peticiones."),
        ("La pieza carga muy lenta",
         "Los .glb muy pesados tardan. Optimiza/comprime el modelo en iJewel3D y revisa tu "
         "conexion; el primer arranque tambien descarga el motor del visor."),
        ("En movil se ve mal",
         "El CSS ya colapsa a una columna por debajo de 860px. Si editaste estilos, comprueba "
         "que no rompiste la media query del final de styles.css."),
    ]
    for titulo, sol in problemas:
        subtitulo(pdf, titulo)
        parrafo(pdf, sol)

    # =====================================================================
    # CAP 9
    # =====================================================================
    pdf.add_page()
    titulo_seccion(pdf, 9, "Glosario y enlaces oficiales", links[8])
    subtitulo(pdf, "Glosario rapido")
    tabla(pdf,
          ["Termino", "Significado"],
          [
              ["CDN", "Red de servidores que entrega librerias por internet; por eso no instalas nada."],
              ["Web component", "Etiqueta HTML personalizada (como <webgi-viewer>) con su propio "
                                "comportamiento."],
              ["Modulo (ES module)", "JavaScript moderno con import/export; requiere servir por http."],
              ["Render / renderizado", "Proceso de dibujar la escena 3D en pantalla."],
              ["Prop", "Parametro de un componente React (modelUrl, environment, height)."],
              ["Variation", "Indice de una variacion de material definida en iJewel3D."],
          ],
          [42, ANCHO_UTIL - 42])
    subtitulo(pdf, "Documentacion oficial de iJewel3D")
    enlaces = [
        ("Visor (introduccion)", "https://docs.ijewel3d.com/viewer/introduction.html"),
        ("Embedding / incrustar", "https://docs.ijewel3d.com/integrations/embedding.html"),
        ("Configurador de anillos", "https://docs.ijewel3d.com/ring-configurator/introduction.html"),
    ]
    pdf.set_font("Helvetica", "", 10.5)
    for nombre, url in enlaces:
        pdf.set_text_color(*TINTA)
        pdf.set_font("Helvetica", "B", 10.5)
        x = pdf.get_x()
        pdf.cell(5, 6, t("-"))
        pdf.cell(50, 6, t(nombre))
        pdf.set_text_color(*ORO)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, t(url), link=url)
        pdf.ln(6.5)
        pdf.set_x(x)
    pdf.ln(4)
    nota(pdf, "En resumen",
         "1) Sube y configura el modelo en iJewel3D. 2) Copia su URL .glb. 3) Pega la URL en "
         "app.js (Playground) o en la prop modelUrl (React). 4) Sirve por localhost y prueba. "
         "5) Lleva el componente a Lovable para tu web real. Eso es todo, de pe a pa.")

    salida = "Manual_Playground_iJewel3D_ES.pdf"
    pdf.output(salida)
    print(f"PDF generado: {salida}  ({pdf.page_no()} paginas)")


if __name__ == "__main__":
    construir()
