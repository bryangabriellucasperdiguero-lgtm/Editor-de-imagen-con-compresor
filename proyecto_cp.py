import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance, ImageOps
import os
import io
import zlib
import struct
import copy


# ============================================================
# APLICACION PRINCIPAL
# ============================================================

class Aplicacion:

    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto CP")
        self.root.geometry("1150x750")
        self.root.minsize(850, 550)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.editor = EditorImagenes(self.notebook)
        self.compresor = CompresorCP(self.notebook)
        self.formato_cp = FormatoImagenCP(self.notebook)

        self.notebook.add(self.editor.frame, text="Editor de imágenes")
        self.notebook.add(self.compresor.frame, text="Compresor de archivos")
        self.notebook.add(self.formato_cp.frame, text="Formato de imagen CP")


# ============================================================
# EDITOR DE IMAGENES
# ============================================================

class EditorImagenes:

    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)

        self.capas = [None, None]
        self.visibles = [True, True]
        self.capa_activa = 0

        self.herramienta = "Lápiz"
        self.color = "#000000"
        self.grosor = 5
        self.zoom = 1.0

        self.imagen_tk = None
        self.inicio = None
        self.ultimo_punto = None
        self.imagen_arrastre = None

        self.historial = []
        self.posicion_historial = -1
        self.max_historial = 30

        self.crear_interfaz()
        self.guardar_historial()

    # --------------------------------------------------------
    # INTERFAZ
    # --------------------------------------------------------

    def crear_interfaz(self):

        barra = ttk.Frame(self.frame)
        barra.pack(fill="x", padx=5, pady=5)

        botones = [
            ("Abrir", self.abrir_imagen),
            ("Guardar", self.guardar_imagen),
            ("Deshacer", self.deshacer),
            ("Rehacer", self.rehacer),
            ("Recortar", lambda: self.seleccionar_herramienta("Recortar")),
            ("Redimensionar", self.redimensionar),
            ("Tamaño lienzo", self.cambiar_lienzo),
            ("Rotar izquierda", lambda: self.rotar(90)),
            ("Rotar derecha", lambda: self.rotar(-90)),
            ("Voltear H", lambda: self.voltear("H")),
            ("Voltear V", lambda: self.voltear("V"))
        ]

        for texto, comando in botones:
            ttk.Button(barra, text=texto, command=comando).pack(
                side="left", padx=2
            )

        herramientas = ttk.LabelFrame(self.frame, text="Herramientas")
        herramientas.pack(fill="x", padx=5, pady=4)

        herramientas_lista = [
            "Lápiz", "Borrador", "Seleccionar", "Mover capa",
            "Cuentagotas", "Línea", "Rectángulo", "Círculo"
        ]

        for herramienta in herramientas_lista:
            ttk.Button(
                herramientas,
                text=herramienta,
                command=lambda h=herramienta: self.seleccionar_herramienta(h)
            ).pack(side="left", padx=3, pady=4)

        ttk.Label(herramientas, text="Grosor:").pack(side="left", padx=(12, 2))

        self.control_grosor = tk.IntVar(value=5)

        ttk.Spinbox(
            herramientas,
            from_=1,
            to=100,
            width=5,
            textvariable=self.control_grosor,
            command=self.actualizar_grosor
        ).pack(side="left")

        ttk.Button(
            herramientas,
            text="Color",
            command=self.elegir_color
        ).pack(side="left", padx=5)

        ttk.Button(
            herramientas,
            text="Zoom +",
            command=lambda: self.cambiar_zoom(1.2)
        ).pack(side="left", padx=2)

        ttk.Button(
            herramientas,
            text="Zoom -",
            command=lambda: self.cambiar_zoom(0.8)
        ).pack(side="left", padx=2)

        ttk.Button(
            herramientas,
            text="Zoom 100%",
            command=self.zoom_original
        ).pack(side="left", padx=2)

        zona = ttk.Frame(self.frame)
        zona.pack(fill="both", expand=True, padx=5, pady=5)

        # Panel de capas
        panel = ttk.LabelFrame(zona, text="Capas")
        panel.pack(side="left", fill="y", padx=5)

        self.lista_capas = tk.Listbox(panel, height=5, width=20)
        self.lista_capas.pack(fill="x", padx=5, pady=5)
        self.lista_capas.bind("<<ListboxSelect>>", self.seleccionar_capa)

        ttk.Button(
            panel, text="Cargar imagen en capa",
            command=self.cargar_en_capa
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            panel, text="Limpiar capa",
            command=self.limpiar_capa
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            panel, text="Mostrar / ocultar",
            command=self.alternar_visibilidad
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            panel, text="Subir capa",
            command=lambda: self.mover_orden_capa(-1)
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            panel, text="Bajar capa",
            command=lambda: self.mover_orden_capa(1)
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            panel, text="Añadir texto",
            command=self.anhadir_texto
        ).pack(fill="x", padx=5, pady=(12, 2))

        ttk.Button(
            panel, text="Brillo",
            command=self.ajustar_brillo
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            panel, text="Contraste",
            command=self.ajustar_contraste
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            panel, text="Blanco y negro",
            command=lambda: self.aplicar_filtro("BN")
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            panel, text="Sepia",
            command=lambda: self.aplicar_filtro("Sepia")
        ).pack(fill="x", padx=5, pady=2)

        ttk.Button(
            panel, text="Negativo",
            command=lambda: self.aplicar_filtro("Negativo")
        ).pack(fill="x", padx=5, pady=2)

        # Zona de dibujo
        centro = ttk.Frame(zona)
        centro.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(
            centro,
            background="#777777",
            cursor="crosshair"
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.iniciar_dibujo)
        self.canvas.bind("<B1-Motion>", self.continuar_dibujo)
        self.canvas.bind("<ButtonRelease-1>", self.terminar_dibujo)

        self.estado = ttk.Label(self.frame, text="Sin imagen")
        self.estado.pack(fill="x", padx=8, pady=4)

        self.actualizar_lista_capas()

    # --------------------------------------------------------
    # FUNCIONES GENERALES
    # --------------------------------------------------------

    def seleccionar_herramienta(self, herramienta):
        self.herramienta = herramienta
        self.estado.config(text="Herramienta: " + herramienta)

    def actualizar_grosor(self):
        try:
            self.grosor = max(1, min(100, int(self.control_grosor.get())))
        except (ValueError, tk.TclError):
            self.grosor = 5

    def elegir_color(self):
        resultado = colorchooser.askcolor(color=self.color)
        if resultado and resultado[1]:
            self.color = resultado[1]
            self.estado.config(text="Color: " + self.color)

    def obtener_tamano(self):
        for capa in self.capas:
            if capa is not None:
                return capa.size
        return None

    def normalizar_capas(self):
        tamano = self.obtener_tamano()
        if tamano is None:
            return

        for i, capa in enumerate(self.capas):
            if capa is not None and capa.size != tamano:
                nueva = Image.new("RGBA", tamano, (0, 0, 0, 0))
                nueva.alpha_composite(capa, (0, 0))
                self.capas[i] = nueva

    def obtener_imagen_final(self):

        self.normalizar_capas()
        tamano = self.obtener_tamano()

        if tamano is None:
            return None

        resultado = Image.new("RGBA", tamano, (0, 0, 0, 0))

        # La capa 1 es el fondo y la capa 2 se dibuja encima.
        for i in range(2):
            if self.capas[i] is not None and self.visibles[i]:
                resultado.alpha_composite(self.capas[i])

        return resultado

    def actualizar_lista_capas(self):

        self.lista_capas.delete(0, tk.END)

        for i in range(2):
            nombre = f"Capa {i + 1}"
            if self.capas[i] is None:
                nombre += " (vacía)"
            if not self.visibles[i]:
                nombre += " (oculta)"

            self.lista_capas.insert(tk.END, nombre)

        self.lista_capas.selection_clear(0, tk.END)
        self.lista_capas.selection_set(self.capa_activa)

    def seleccionar_capa(self, evento=None):

        seleccion = self.lista_capas.curselection()

        if seleccion:
            self.capa_activa = seleccion[0]
            self.estado.config(
                text=f"Capa activa: {self.capa_activa + 1}"
            )

    def guardar_historial(self):

        estado = {
            "capas": [
                capa.copy() if capa is not None else None
                for capa in self.capas
            ],
            "visibles": self.visibles.copy(),
            "activa": self.capa_activa
        }

        self.historial = self.historial[:self.posicion_historial + 1]
        self.historial.append(estado)

        if len(self.historial) > self.max_historial:
            self.historial.pop(0)

        self.posicion_historial = len(self.historial) - 1

    def restaurar_historial(self):

        estado = self.historial[self.posicion_historial]

        self.capas = [
            capa.copy() if capa is not None else None
            for capa in estado["capas"]
        ]

        self.visibles = estado["visibles"].copy()
        self.capa_activa = estado["activa"]

        self.actualizar_lista_capas()
        self.actualizar_vista()

    def deshacer(self):

        if self.posicion_historial > 0:
            self.posicion_historial -= 1
            self.restaurar_historial()

    def rehacer(self):

        if self.posicion_historial < len(self.historial) - 1:
            self.posicion_historial += 1
            self.restaurar_historial()

    # --------------------------------------------------------
    # VISUALIZACION
    # --------------------------------------------------------

    def actualizar_vista(self):

        self.canvas.delete("all")

        imagen = self.obtener_imagen_final()

        if imagen is None:
            self.estado.config(text="Sin imagen")
            return

        ancho = max(1, int(imagen.width * self.zoom))
        alto = max(1, int(imagen.height * self.zoom))

        vista = imagen.resize(
            (ancho, alto),
            Image.Resampling.LANCZOS
        )

        self.imagen_tk = ImageTk.PhotoImage(vista)

        self.canvas.create_image(
            10, 10,
            anchor="nw",
            image=self.imagen_tk
        )

        self.canvas.config(
            scrollregion=(0, 0, ancho + 20, alto + 20)
        )

        self.estado.config(
            text=f"{imagen.width} x {imagen.height} píxeles | Zoom: {int(self.zoom * 100)}%"
        )

    def cambiar_zoom(self, factor):

        self.zoom = max(0.1, min(5.0, self.zoom * factor))
        self.actualizar_vista()

    def zoom_original(self):
        self.zoom = 1.0
        self.actualizar_vista()

    def coordenadas_imagen(self, evento):

        x = self.canvas.canvasx(evento.x) - 10
        y = self.canvas.canvasy(evento.y) - 10

        return int(x / self.zoom), int(y / self.zoom)

    # --------------------------------------------------------
    # ABRIR Y GUARDAR
    # --------------------------------------------------------

    def abrir_imagen(self):

        ruta = filedialog.askopenfilename(
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not ruta:
            return

        try:
            imagen = Image.open(ruta).convert("RGBA")

            self.capas = [imagen, None]
            self.visibles = [True, True]
            self.capa_activa = 0

            self.zoom = 1.0
            self.historial = []
            self.posicion_historial = -1

            self.guardar_historial()
            self.actualizar_lista_capas()
            self.actualizar_vista()

        except Exception as error:
            messagebox.showerror("Error", str(error))

    def guardar_imagen(self):

        imagen = self.obtener_imagen_final()

        if imagen is None:
            messagebox.showwarning("Aviso", "No hay ninguna imagen.")
            return

        ruta = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg"),
                ("WebP", "*.webp"),
                ("BMP", "*.bmp")
            ]
        )

        if not ruta:
            return

        try:
            if ruta.lower().endswith((".jpg", ".jpeg")):
                imagen.convert("RGB").save(ruta, quality=95)
            else:
                imagen.save(ruta)

            messagebox.showinfo("Guardado", "Imagen guardada correctamente.")

        except Exception as error:
            messagebox.showerror("Error", str(error))

    # --------------------------------------------------------
    # CAPAS
    # --------------------------------------------------------

    def cargar_en_capa(self):

        ruta = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp")]
        )

        if not ruta:
            return

        try:
            imagen = Image.open(ruta).convert("RGBA")

            if self.capas[0] is None:
                self.capas[0] = Image.new(
                    "RGBA", imagen.size, (0, 0, 0, 0)
                )

            tamano = self.obtener_tamano()

            if imagen.size != tamano:
                imagen.thumbnail(tamano, Image.Resampling.LANCZOS)

                lienzo = Image.new(
                    "RGBA", tamano, (0, 0, 0, 0)
                )
                lienzo.alpha_composite(imagen)
                imagen = lienzo

            self.capas[self.capa_activa] = imagen

            self.guardar_historial()
            self.actualizar_lista_capas()
            self.actualizar_vista()

        except Exception as error:
            messagebox.showerror("Error", str(error))

    def limpiar_capa(self):

        if self.capas[self.capa_activa] is None:
            return

        self.capas[self.capa_activa] = None
        self.guardar_historial()
        self.actualizar_lista_capas()
        self.actualizar_vista()

    def alternar_visibilidad(self):

        self.visibles[self.capa_activa] = not self.visibles[self.capa_activa]

        self.guardar_historial()
        self.actualizar_lista_capas()
        self.actualizar_vista()

    def mover_orden_capa(self, direccion):

        otra = self.capa_activa + direccion

        if otra < 0 or otra > 1:
            return

        self.capas[self.capa_activa], self.capas[otra] = (
            self.capas[otra], self.capas[self.capa_activa]
        )

        self.visibles[self.capa_activa], self.visibles[otra] = (
            self.visibles[otra], self.visibles[self.capa_activa]
        )

        self.capa_activa = otra

        self.guardar_historial()
        self.actualizar_lista_capas()
        self.actualizar_vista()

    def obtener_capa_activa(self):

        if self.capas[self.capa_activa] is None:
            tamano = self.obtener_tamano()

            if tamano is None:
                return None

            self.capas[self.capa_activa] = Image.new(
                "RGBA", tamano, (0, 0, 0, 0)
            )

        return self.capas[self.capa_activa]

 # --------------------------------------------------------
    # DIBUJO Y HERRAMIENTAS
    # --------------------------------------------------------

    def iniciar_dibujo(self, evento):

        punto = self.coordenadas_imagen(evento)
        imagen = self.obtener_imagen_final()

        if imagen is None:
            return

        if self.herramienta == "Cuentagotas":

            x, y = punto

            if 0 <= x < imagen.width and 0 <= y < imagen.height:
                pixel = imagen.getpixel((x, y))
                self.color = "#{:02x}{:02x}{:02x}".format(
                    pixel[0], pixel[1], pixel[2]
                )
                self.estado.config(text="Color seleccionado: " + self.color)

            return

        if self.herramienta == "Mover capa":

            if self.capa_activa != 1:
                self.estado.config(
                    text="Selecciona la capa 2 para moverla."
                )
                return

            if self.capas[1] is None:
                return

            self.inicio = punto
            self.imagen_arrastre = self.capas[1].copy()
            return

        self.inicio = punto
        self.ultimo_punto = punto

        if self.herramienta in ("Lápiz", "Borrador"):
            capa = self.obtener_capa_activa()

            if capa is None:
                return

            draw = ImageDraw.Draw(capa)

            color = self.color
            if self.herramienta == "Borrador":
                color = (0, 0, 0, 0)

            if self.herramienta == "Lápiz":
                color = self.color

            draw.ellipse(
                (
                    punto[0] - self.grosor // 2,
                    punto[1] - self.grosor // 2,
                    punto[0] + self.grosor // 2,
                    punto[1] + self.grosor // 2
                ),
                fill=color
            )

            self.actualizar_vista()

        elif self.herramienta == "Seleccionar":
            self.canvas.delete("seleccion")
            x = evento.x
            y = evento.y

            self.canvas.create_rectangle(
                x, y, x, y,
                outline="yellow",
                width=2,
                tags="seleccion"
            )

    def continuar_dibujo(self, evento):

        if self.inicio is None:
            return

        punto = self.coordenadas_imagen(evento)

        if self.herramienta in ("Lápiz", "Borrador"):

            capa = self.obtener_capa_activa()

            if capa is None:
                return

            draw = ImageDraw.Draw(capa)

            color = self.color

            if self.herramienta == "Borrador":
                color = (0, 0, 0, 0)

            draw.line(
                [self.ultimo_punto, punto],
                fill=color,
                width=self.grosor
            )

            radio = self.grosor // 2

            draw.ellipse(
                (
                    punto[0] - radio,
                    punto[1] - radio,
                    punto[0] + radio,
                    punto[1] + radio
                ),
                fill=color
            )

            self.ultimo_punto = punto
            self.actualizar_vista()

        elif self.herramienta == "Seleccionar":

            self.canvas.delete("seleccion")

            x1 = self.inicio[0] * self.zoom + 10
            y1 = self.inicio[1] * self.zoom + 10
            x2 = punto[0] * self.zoom + 10
            y2 = punto[1] * self.zoom + 10

            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="yellow",
                width=2,
                tags="seleccion"
            )

        elif self.herramienta == "Mover capa":

            self.canvas.delete("movimiento")

            x1 = self.inicio[0] * self.zoom + 10
            y1 = self.inicio[1] * self.zoom + 10
            x2 = punto[0] * self.zoom + 10
            y2 = punto[1] * self.zoom + 10

            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="cyan",
                width=2,
                tags="movimiento"
            )

    def terminar_dibujo(self, evento):

        if self.inicio is None:
            return

        final = self.coordenadas_imagen(evento)
        inicio = self.inicio

        if self.herramienta in ("Lápiz", "Borrador"):

            self.guardar_historial()
            self.actualizar_vista()

        elif self.herramienta in (
            "Línea", "Rectángulo", "Círculo"
        ):

            capa = self.obtener_capa_activa()

            if capa is not None:
                draw = ImageDraw.Draw(capa)

                caja = [
                    inicio[0], inicio[1],
                    final[0], final[1]
                ]

                if self.herramienta == "Línea":
                    draw.line(
                        [inicio, final],
                        fill=self.color,
                        width=self.grosor
                    )

                elif self.herramienta == "Rectángulo":
                    draw.rectangle(
                        caja,
                        outline=self.color,
                        width=self.grosor
                    )

                elif self.herramienta == "Círculo":
                    draw.ellipse(
                        caja,
                        outline=self.color,
                        width=self.grosor
                    )

                self.guardar_historial()
                self.actualizar_vista()

        elif self.herramienta == "Seleccionar":

            self.canvas.delete("seleccion")

            x1 = max(0, min(inicio[0], final[0]))
            y1 = max(0, min(inicio[1], final[1]))
            x2 = max(inicio[0], final[0])
            y2 = max(inicio[1], final[1])

            if x2 > x1 and y2 > y1:
                self.estado.config(
                    text=f"Selección: {x2-x1} x {y2-y1} píxeles. Usa Recortar."
                )
                self.seleccion = (x1, y1, x2, y2)

        elif self.herramienta == "Mover capa":

            self.canvas.delete("movimiento")

            if self.capas[1] is not None:
                dx = final[0] - inicio[0]
                dy = final[1] - inicio[1]

                nueva = Image.new(
                    "RGBA",
                    self.capas[1].size,
                    (0, 0, 0, 0)
                )

                nueva.alpha_composite(
                    self.capas[1],
                    (dx, dy)
                )

                self.capas[1] = nueva

                self.guardar_historial()
                self.actualizar_vista()

        self.inicio = None
        self.ultimo_punto = None
        self.imagen_arrastre = None

    # --------------------------------------------------------
    # RECORTE Y DIMENSIONES
    # --------------------------------------------------------

    def recortar(self):

        if not hasattr(self, "seleccion"):
            messagebox.showwarning(
                "Aviso",
                "Primero selecciona una zona de la imagen."
            )
            return

        x1, y1, x2, y2 = self.seleccion

        for i in range(2):
            if self.capas[i] is not None:
                self.capas[i] = self.capas[i].crop(
                    (x1, y1, x2, y2)
                )

        self.guardar_historial()
        self.actualizar_vista()
        del self.seleccion

    def redimensionar(self):

        tamano = self.obtener_tamano()

        if tamano is None:
            return

        ancho = simpledialog.askinteger(
            "Redimensionar",
            "Nuevo ancho en píxeles:",
            initialvalue=tamano[0],
            minvalue=1,
            maxvalue=20000
        )

        if ancho is None:
            return

        alto = simpledialog.askinteger(
            "Redimensionar",
            "Nuevo alto en píxeles:",
            initialvalue=tamano[1],
            minvalue=1,
            maxvalue=20000
        )

        if alto is None:
            return

        for i in range(2):
            if self.capas[i] is not None:
                self.capas[i] = self.capas[i].resize(
                    (ancho, alto),
                    Image.Resampling.LANCZOS
                )

        self.guardar_historial()
        self.actualizar_vista()

    def cambiar_lienzo(self):

        tamano = self.obtener_tamano()

        if tamano is None:
            return

        ancho = simpledialog.askinteger(
            "Tamaño del lienzo",
            "Ancho nuevo:",
            initialvalue=tamano[0],
            minvalue=1,
            maxvalue=20000
        )

        if ancho is None:
            return

        alto = simpledialog.askinteger(
            "Tamaño del lienzo",
            "Alto nuevo:",
            initialvalue=tamano[1],
            minvalue=1,
            maxvalue=20000
        )

        if alto is None:
            return

        for i in range(2):
            if self.capas[i] is not None:
                nueva = Image.new(
                    "RGBA",
                    (ancho, alto),
                    (0, 0, 0, 0)
                )

                nueva.alpha_composite(self.capas[i])
                self.capas[i] = nueva

        self.guardar_historial()
        self.actualizar_vista()

    # --------------------------------------------------------
    # ROTACION Y VOLTEO
    # --------------------------------------------------------

    def rotar(self, grados):

        if self.obtener_tamano() is None:
            return

        for i in range(2):
            if self.capas[i] is not None:
                self.capas[i] = self.capas[i].rotate(
                    grados,
                    expand=True
                )

        self.guardar_historial()
        self.actualizar_vista()

    def voltear(self, direccion):

        if self.obtener_tamano() is None:
            return

        for i in range(2):
            if self.capas[i] is not None:

                if direccion == "H":
                    self.capas[i] = ImageOps.mirror(self.capas[i])
                else:
                    self.capas[i] = ImageOps.flip(self.capas[i])

        self.guardar_historial()
        self.actualizar_vista()

    # --------------------------------------------------------
    # TEXTO Y FILTROS
    # --------------------------------------------------------

    def anhadir_texto(self):

        texto = simpledialog.askstring(
            "Añadir texto",
            "Escribe el texto:"
        )

        if not texto:
            return

        tamano = simpledialog.askinteger(
            "Tamaño de texto",
            "Tamaño de letra:",
            initialvalue=30,
            minvalue=1,
            maxvalue=500
        )

        if tamano is None:
            return

        capa = self.obtener_capa_activa()

        if capa is None:
            messagebox.showwarning(
                "Aviso",
                "Primero abre una imagen."
            )
            return

        try:
            fuente = ImageFont.truetype("arial.ttf", tamano)
        except OSError:
            fuente = ImageFont.load_default()

        draw = ImageDraw.Draw(capa)

        draw.text(
            (20, 20),
            texto,
            font=fuente,
            fill=self.color
        )

        self.guardar_historial()
        self.actualizar_vista()

    def ajustar_brillo(self):

        capa = self.obtener_capa_activa()

        if capa is None:
            return

        valor = simpledialog.askfloat(
            "Brillo",
            "Factor de brillo (1 = normal):",
            initialvalue=1.2,
            minvalue=0.1,
            maxvalue=5.0
        )

        if valor is None:
            return

        alpha = capa.getchannel("A")
        rgb = capa.convert("RGB")

        rgb = ImageEnhance.Brightness(rgb).enhance(valor)

        resultado = rgb.convert("RGBA")
        resultado.putalpha(alpha)

        self.capas[self.capa_activa] = resultado

        self.guardar_historial()
        self.actualizar_vista()

    def ajustar_contraste(self):

        capa = self.obtener_capa_activa()

        if capa is None:
            return

        valor = simpledialog.askfloat(
            "Contraste",
            "Factor de contraste (1 = normal):",
            initialvalue=1.3,
            minvalue=0.1,
            maxvalue=5.0
        )

        if valor is None:
            return

        alpha = capa.getchannel("A")
        rgb = capa.convert("RGB")

        rgb = ImageEnhance.Contrast(rgb).enhance(valor)

        resultado = rgb.convert("RGBA")
        resultado.putalpha(alpha)

        self.capas[self.capa_activa] = resultado

        self.guardar_historial()
        self.actualizar_vista()

    def aplicar_filtro(self, filtro):

        capa = self.obtener_capa_activa()

        if capa is None:
            return

        alpha = capa.getchannel("A")
        rgb = capa.convert("RGB")

        if filtro == "BN":
            rgb = ImageOps.grayscale(rgb).convert("RGB")

        elif filtro == "Sepia":
            gris = ImageOps.grayscale(rgb)
            rgb = ImageOps.colorize(
                gris,
                "#382515",
                "#f5dfb5"
            ).convert("RGB")

        elif filtro == "Negativo":
            rgb = ImageOps.invert(rgb)

        resultado = rgb.convert("RGBA")
        resultado.putalpha(alpha)

        self.capas[self.capa_activa] = resultado

        self.guardar_historial()
        self.actualizar_vista()

# ============================================================
# COMPRESOR DE ARCHIVOS CP
# ============================================================

class CompresorCP:

    FIRMA = b"CP01"

    def __init__(self, notebook):

        self.frame = ttk.Frame(notebook)

        titulo = ttk.Label(
            self.frame,
            text="Compresor de archivos CP",
            font=("Arial", 18, "bold")
        )
        titulo.pack(pady=20)

        ttk.Label(
            self.frame,
            text="Comprime cualquier archivo en formato .cp y permite recuperarlo."
        ).pack(pady=5)

        ttk.Button(
            self.frame,
            text="Comprimir archivo",
            command=self.comprimir
        ).pack(pady=15)

        ttk.Button(
            self.frame,
            text="Descomprimir archivo",
            command=self.descomprimir
        ).pack(pady=5)

        self.estado = ttk.Label(self.frame, text="Preparado")
        self.estado.pack(pady=20)

    def comprimir(self):

        origen = filedialog.askopenfilename(
            title="Seleccionar archivo"
        )

        if not origen:
            return

        destino = filedialog.asksaveasfilename(
            title="Guardar archivo CP",
            defaultextension=".cp",
            filetypes=[("Archivo CP", "*.cp")]
        )

        if not destino:
            return

        try:
            with open(origen, "rb") as archivo:
                datos = archivo.read()

            comprimido = zlib.compress(datos, 9)

            with open(destino, "wb") as archivo:
                archivo.write(self.FIRMA)
                archivo.write(struct.pack(">Q", len(datos)))
                archivo.write(comprimido)

            porcentaje = 0

            if len(datos) > 0:
                porcentaje = 100 * (
                    1 - len(comprimido) / len(datos)
                )

            self.estado.config(
                text=f"Compresión terminada. Reducción: {porcentaje:.1f}%"
            )

            messagebox.showinfo(
                "Completado",
                "Archivo comprimido correctamente."
            )

        except Exception as error:
            messagebox.showerror("Error", str(error))

    def descomprimir(self):

        origen = filedialog.askopenfilename(
            title="Seleccionar archivo CP",
            filetypes=[("Archivo CP", "*.cp")]
        )

        if not origen:
            return

        destino = filedialog.asksaveasfilename(
            title="Guardar archivo recuperado"
        )

        if not destino:
            return

        try:
            with open(origen, "rb") as archivo:
                firma = archivo.read(4)

                if firma != self.FIRMA:
                    raise ValueError(
                        "El archivo no es un CP de compresión general."
                    )

                cabecera = archivo.read(8)

                if len(cabecera) != 8:
                    raise ValueError("Cabecera incompleta.")

                tamano_original = struct.unpack(
                    ">Q", cabecera
                )[0]

                datos = zlib.decompress(archivo.read())

            if len(datos) != tamano_original:
                raise ValueError(
                    "El tamaño recuperado no coincide."
                )

            with open(destino, "wb") as archivo:
                archivo.write(datos)

            self.estado.config(text="Descompresión terminada.")

            messagebox.showinfo(
                "Completado",
                "Archivo recuperado correctamente."
            )

        except Exception as error:
            messagebox.showerror("Error", str(error))


# ============================================================
# FORMATO DE IMAGEN CP
# ============================================================

class FormatoImagenCP:

    FIRMA = b"CPIM"
    VERSION = 1

    def __init__(self, notebook):

        self.frame = ttk.Frame(notebook)

        titulo = ttk.Label(
            self.frame,
            text="Formato de imagen CP",
            font=("Arial", 18, "bold")
        )
        titulo.pack(pady=20)

        ttk.Label(
            self.frame,
            text="Convierte imágenes al formato CP y vuelve a abrirlas."
        ).pack(pady=5)

        opciones = ttk.LabelFrame(
            self.frame,
            text="Modo de compresión"
        )
        opciones.pack(padx=30, pady=20, fill="x")

        self.modo = tk.StringVar(value="sin_perdida")

        ttk.Radiobutton(
            opciones,
            text="Sin pérdida: conserva los píxeles originales",
            variable=self.modo,
            value="sin_perdida"
        ).pack(anchor="w", padx=15, pady=8)

        ttk.Radiobutton(
            opciones,
            text="Máxima compresión: puede perder calidad",
            variable=self.modo,
            value="con_perdida"
        ).pack(anchor="w", padx=15, pady=8)

        ttk.Button(
            self.frame,
            text="Convertir imagen a CP",
            command=self.convertir_a_cp
        ).pack(pady=12)

        ttk.Button(
            self.frame,
            text="Abrir imagen CP",
            command=self.abrir_cp
        ).pack(pady=5)

        self.estado = ttk.Label(
            self.frame,
            text="Preparado"
        )
        self.estado.pack(pady=20)

        ttk.Label(
            self.frame,
            text=(
                "CP sin pérdida utiliza compresión de datos.\n"
                "CP con pérdida utiliza JPEG para el color y conserva "
                "el canal de transparencia."
            ),
            justify="center"
        ).pack(pady=10)

    # --------------------------------------------------------
    # CONVERSION A CP
    # --------------------------------------------------------

    def convertir_a_cp(self):

        origen = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not origen:
            return

        destino = filedialog.asksaveasfilename(
            title="Guardar imagen CP",
            defaultextension=".cp",
            filetypes=[("Imagen CP", "*.cp")]
        )

        if not destino:
            return

        try:

            imagen = Image.open(origen).convert("RGBA")

            ancho, alto = imagen.size

            if self.modo.get() == "sin_perdida":

                modo = 0

                # Se guardan los cuatro canales de cada píxel.
                datos_originales = imagen.tobytes()
                datos = zlib.compress(datos_originales, 9)

                datos_color = datos
                datos_alpha = b""

            else:

                modo = 1

                calidad = simpledialog.askinteger(
                    "Calidad de imagen",
                    "Calidad JPEG (1-95):",
                    initialvalue=75,
                    minvalue=1,
                    maxvalue=95
                )

                if calidad is None:
                    return

                # Comprimir los canales RGB mediante JPEG.
                rgb = imagen.convert("RGB")

                buffer_rgb = io.BytesIO()
                rgb.save(
                    buffer_rgb,
                    format="JPEG",
                    quality=calidad,
                    optimize=True
                )

                datos_color = buffer_rgb.getvalue()

                # Guardar la transparencia por separado.
                alpha = imagen.getchannel("A")
                datos_alpha = zlib.compress(alpha.tobytes(), 9)

            # Cabecera:
            # CPIM + versión + modo + ancho + alto
            # + longitud de color + longitud de transparencia.

            cabecera = (
                self.FIRMA
                + struct.pack(
                    ">BBIIQQ",
                    self.VERSION,
                    modo,
                    ancho,
                    alto,
                    len(datos_color),
                    len(datos_alpha)
                )
            )

            with open(destino, "wb") as archivo:
                archivo.write(cabecera)
                archivo.write(datos_color)
                archivo.write(datos_alpha)

            tamano_original = os.path.getsize(origen)
            tamano_cp = os.path.getsize(destino)

            if tamano_original > 0:
                reduccion = (
                    1 - tamano_cp / tamano_original
                ) * 100
            else:
                reduccion = 0

            self.estado.config(
                text=(
                    f"Conversión terminada. "
                    f"Tamaño: {tamano_cp / 1024:.1f} KB. "
                    f"Reducción: {reduccion:.1f}%"
                )
            )

            messagebox.showinfo(
                "Conversión terminada",
                "Imagen convertida al formato CP correctamente."
            )

        except Exception as error:
            messagebox.showerror(
                "Error al convertir",
                str(error)
            )

    # --------------------------------------------------------
    # ABRIR IMAGEN CP
    # --------------------------------------------------------

    def abrir_cp(self):

        origen = filedialog.askopenfilename(
            title="Abrir imagen CP",
            filetypes=[("Imagen CP", "*.cp")]
        )

        if not origen:
            return

        try:

            with open(origen, "rb") as archivo:

                firma = archivo.read(4)

                if firma != self.FIRMA:
                    raise ValueError(
                        "El archivo no es una imagen CP."
                    )

                cabecera = archivo.read(26)

                if len(cabecera) != 26:
                    raise ValueError("Cabecera incompleta.")

                version, modo, ancho, alto, longitud_color, longitud_alpha = (
                    struct.unpack(">BBIIQQ", cabecera)
                )

                if version != self.VERSION:
                    raise ValueError(
                        "Versión del formato CP no compatible."
                    )

                if ancho <= 0 or alto <= 0:
                    raise ValueError("Dimensiones no válidas.")

                if ancho * alto > 100_000_000:
                    raise ValueError(
                        "La imagen supera el límite de dimensiones permitido."
                    )

                datos_color = archivo.read(longitud_color)
                datos_alpha = archivo.read(longitud_alpha)

                if (
                    len(datos_color) != longitud_color
                    or len(datos_alpha) != longitud_alpha
                ):
                    raise ValueError("Archivo CP incompleto.")

                if archivo.read(1):
                    raise ValueError(
                        "El archivo contiene datos adicionales."
                    )

            if modo == 0:

                datos = zlib.decompress(datos_color)

                esperado = ancho * alto * 4

                if len(datos) != esperado:
                    raise ValueError(
                        "Los datos de imagen no son válidos."
                    )

                imagen = Image.frombytes(
                    "RGBA",
                    (ancho, alto),
                    datos
                )

            elif modo == 1:

                buffer = io.BytesIO(datos_color)

                imagen_rgb = Image.open(buffer).convert("RGB")

                if imagen_rgb.size != (ancho, alto):
                    raise ValueError(
                        "Las dimensiones de la imagen no coinciden."
                    )

                alpha_datos = zlib.decompress(datos_alpha)

                if len(alpha_datos) != ancho * alto:
                    raise ValueError(
                        "El canal de transparencia no es válido."
                    )

                alpha = Image.frombytes(
                    "L",
                    (ancho, alto),
                    alpha_datos
                )

                imagen = imagen_rgb.convert("RGBA")
                imagen.putalpha(alpha)

            else:
                raise ValueError(
                    "Modo de compresión desconocido."
                )

            destino = filedialog.asksaveasfilename(
                title="Guardar imagen recuperada",
                defaultextension=".png",
                filetypes=[
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg"),
                    ("WebP", "*.webp"),
                    ("BMP", "*.bmp")
                ]
            )

            if not destino:
                return

            if destino.lower().endswith((".jpg", ".jpeg")):
                imagen.convert("RGB").save(destino, quality=95)
            else:
                imagen.save(destino)

            self.estado.config(
                text=f"Imagen CP abierta: {ancho} x {alto}"
            )

            messagebox.showinfo(
                "Imagen recuperada",
                "La imagen CP se ha convertido correctamente."
            )

        except Exception as error:
            messagebox.showerror(
                "Error al abrir CP",
                str(error)
            )


# ============================================================
# INICIO DEL PROGRAMA
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = Aplicacion(root)

    root.mainloop()

