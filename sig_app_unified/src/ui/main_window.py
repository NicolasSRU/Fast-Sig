
"""
Ventana principal de la aplicación SIG unificada.
Menú central interactivo con diseño moderno en tono naranja.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Agregar el directorio src al path para importaciones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.config import UI_COLORS, UI_FONTS, logger
from src.pages.kmz_extractor_page import KMZExtractorPage
from src.pages.excel_to_kmz_page import ExcelToKMZPage
from src.pages.gpx_converter_page import GPXConverterPage
from src.pages.buffer_generator_page import BufferGeneratorPage

class MainWindow:
    """Ventana principal con menú interactivo."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fast SIG Arcadis")
        self.root.configure(bg=UI_COLORS["bg_primary"])
        self.root.resizable(False, False)
        
        # Configurar tamaño y posición
        self._setup_window()
        
        # Crear interfaz
        self._create_interface()
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        logger.info("Aplicación SIG iniciada")
    
    def _setup_window(self):
        """Configura el tamaño y posición de la ventana."""
        width = 700
        height = 600
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_interface(self):
        """Crea la interfaz principal."""
        # Frame principal
        main_frame = tk.Frame(self.root, bg=UI_COLORS["bg_primary"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Título principal
        title_label = tk.Label(
            main_frame,
            text="Fast SIG Arcadis",
            font=("Helvetica", 24, "bold"),
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["accent_primary"]
        )
        title_label.pack(pady=(0, 10))
        
        # Subtítulo
        subtitle_label = tk.Label(
            main_frame,
            text="Kit de Herramientas Rapidas para procesamientos geoespaciales",
            font=UI_FONTS["subtitle"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_secondary"]
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Frame para botones del menú
        menu_frame = tk.Frame(main_frame, bg=UI_COLORS["bg_primary"])
        menu_frame.pack(expand=True, fill=tk.BOTH)
        
        # Configurar grid del menú
        menu_frame.grid_columnconfigure(0, weight=1)
        menu_frame.grid_columnconfigure(1, weight=1)
        
        # Botones del menú principal
        self._create_menu_buttons(menu_frame)
        
        # Frame inferior con información
        info_frame = tk.Frame(main_frame, bg=UI_COLORS["bg_primary"])
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        # Información de la aplicación
        info_label = tk.Label(
            info_frame,
            text="Versión 1.0 | Desarrollado para procesamiento SIG",
            font=UI_FONTS["small"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_secondary"]
        )
        info_label.pack()
    
    def _create_menu_buttons(self, parent):
        """Crea los botones del menú principal."""
        
        # Configuración de botones
        buttons_config = [
            {
                "text": "Extraer Coordenadas\nKMZ → Excel",
                "description": "Extrae coordenadas de archivos KMZ\ny las exporta a Excel",
                "command": self._open_kmz_extractor,
                "row": 0, "column": 0
            },
            {
                "text": "Crear KMZ\nExcel → KMZ",
                "description": "Crea archivos KMZ desde\ndatos de coordenadas en Excel",
                "command": self._open_excel_to_kmz,
                "row": 0, "column": 1
            },
            {
                "text": "Convertir GPX\nGPX → KMZ",
                "description": "Convierte archivos GPX\na formato KMZ",
                "command": self._open_gpx_converter,
                "row": 1, "column": 0
            },
            {
                "text": "Generar Buffers\nKMZ + Buffer",
                "description": "Aplica buffers a geometrías\nen archivos KMZ",
                "command": self._open_buffer_generator,
                "row": 1, "column": 1
            }
        ]
        
        # Crear botones
        for config in buttons_config:
            self._create_menu_button(parent, config)
    
    def _create_menu_button(self, parent, config):
        """Crea un botón individual del menú."""
        
        # Frame contenedor para el botón
        button_frame = tk.Frame(
            parent,
            bg=UI_COLORS["bg_secondary"],
            relief="solid",
            bd=1,
            padx=20,
            pady=20
        )
        button_frame.grid(
            row=config["row"], 
            column=config["column"], 
            padx=15, 
            pady=15, 
            sticky="nsew",
            ipadx=10,
            ipady=10
        )
        
        # Configurar peso del grid
        parent.grid_rowconfigure(config["row"], weight=1)
        
        # Botón principal
        main_button = tk.Button(
            button_frame,
            text=config["text"],
            command=config["command"],
            bg=UI_COLORS["accent_primary"],
            fg="white",
            font=("Helvetica", 14, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            cursor="hand2",
            width=15,
            height=3
        )
        main_button.pack(pady=(0, 10))
        
        # Descripción
        desc_label = tk.Label(
            button_frame,
            text=config["description"],
            font=UI_FONTS["small"],
            bg=UI_COLORS["bg_secondary"],
            fg=UI_COLORS["text_secondary"],
            justify=tk.CENTER
        )
        desc_label.pack()
        
        # Efectos hover para el botón
        self._add_hover_effects(main_button, button_frame)
    
    def _add_hover_effects(self, button, frame):
        """Agrega efectos hover a un botón del menú."""
        
        def on_enter(e):
            button.configure(bg=UI_COLORS["accent_hover"])
            frame.configure(bg=UI_COLORS["accent_primary"], bd=2)
        
        def on_leave(e):
            button.configure(bg=UI_COLORS["accent_primary"])
            frame.configure(bg=UI_COLORS["bg_secondary"], bd=1)
        
        # Aplicar efectos tanto al botón como al frame
        for widget in [button, frame]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
    
    def _open_kmz_extractor(self):
        """Abre la página de extracción de coordenadas KMZ."""
        try:
            page = KMZExtractorPage(self.root)
            page.show()
        except Exception as e:
            logger.error(f"Error abriendo extractor KMZ: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el extractor KMZ:\n{e}")
    
    def _open_excel_to_kmz(self):
        """Abre la página de conversión Excel a KMZ."""
        try:
            page = ExcelToKMZPage(self.root)
            page.show()
        except Exception as e:
            logger.error(f"Error abriendo conversor Excel a KMZ: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el conversor Excel a KMZ:\n{e}")
    
    def _open_gpx_converter(self):
        """Abre la página de conversión GPX."""
        try:
            page = GPXConverterPage(self.root)
            page.show()
        except Exception as e:
            logger.error(f"Error abriendo conversor GPX: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el conversor GPX:\n{e}")
    
    def _open_buffer_generator(self):
        """Abre la página de generación de buffers."""
        try:
            page = BufferGeneratorPage(self.root)
            page.show()
        except Exception as e:
            logger.error(f"Error abriendo generador de buffers: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el generador de buffers:\n{e}")
    
    def _on_close(self):
        """Maneja el cierre de la aplicación."""
        if messagebox.askokcancel("Salir", "¿Está seguro que desea salir de la aplicación?"):
            logger.info("Aplicación SIG cerrada")
            self.root.destroy()
    
    def run(self):
        """Ejecuta la aplicación."""
        self.root.mainloop()

def main():
    """Función principal."""
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {e}")
        messagebox.showerror("Error Fatal", f"Error iniciando la aplicación:\n{e}")

if __name__ == "__main__":
    main()
