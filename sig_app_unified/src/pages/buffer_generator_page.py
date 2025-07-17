
"""
Página para generar buffers en archivos KMZ.
"""

import tkinter as tk
from tkinter import filedialog, ttk
import threading
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ui.base_window import BaseWindow
from src.core.kmz_processor import KMZProcessor
from src.core.validators import InputValidator, ValidationError, DataValidator
from src.core.config import logger, BUFFER_CONFIG
from src.core.utils import format_distance

class BufferGeneratorPage(BaseWindow):
    """Página para generar buffers en KMZ."""
    
    def __init__(self, parent=None):
        super().__init__("Generar Buffers en KMZ", 850, 650, True, parent)
        
        self.processor = KMZProcessor()
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.buffer_distance = tk.StringVar(value=str(BUFFER_CONFIG["default_distance"]))
        self.combine_buffers = tk.BooleanVar(value=False)
        
        self._create_interface()
        self.configure_grid_weights()
    
    def _create_interface(self):
        """Crea la interfaz de la página."""
        
        # Título
        self.create_title("Generar Buffers en archivos KMZ")
        
        # Selector de archivo KMZ de entrada
        self.create_file_selector(
            "Archivo KMZ de entrada:",
            1,
            [("Archivos KMZ", "*.kmz")],
            self._browse_input_file,
            self.input_file
        )
        
        # Selector de archivo KMZ de salida
        self.create_file_selector(
            "Guardar KMZ como:",
            2,
            [("Archivos KMZ", "*.kmz")],
            self._browse_output_file,
            self.output_file
        )
        
        # Frame para configuración de buffer
        self._create_buffer_config_frame()
        
        # Frame para opciones avanzadas
        self._create_advanced_options_frame()
        
        # Botones de acción
        button_frame = tk.Frame(self.main_frame, bg=self.root.cget("bg"))
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        self.create_action_button(
            "Generar Buffer",
            self._generate_buffer,
            6, 1, "primary"
        )
        
        self.create_action_button(
            "Vista Previa",
            self._preview_geometries,
            6, 0, "secondary"
        )
        
        self.create_action_button(
            "Volver al Menú",
            self._return_to_menu,
            6, 2, "secondary"
        )
        
        # Etiqueta de estado
        self.create_status_label(7)
        
        # Información adicional
        self._create_help_section()
    
    def _create_buffer_config_frame(self):
        """Crea el frame de configuración de buffer."""
        config_frame = tk.LabelFrame(
            self.main_frame,
            text="Configuración del Buffer",
            font=("Helvetica", 12, "bold"),
            bg=self.root.cget("bg"),
            fg="#E4610F",
            padx=15,
            pady=10
        )
        config_frame.grid(row=3, column=0, columnspan=3, pady=15, sticky="ew", padx=20)
        
        # Distancia del buffer
        tk.Label(
            config_frame,
            text="Distancia del buffer (metros):",
            font=("Helvetica", 11),
            bg=self.root.cget("bg")
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        distance_frame = tk.Frame(config_frame, bg=self.root.cget("bg"))
        distance_frame.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        distance_entry = tk.Entry(
            distance_frame,
            textvariable=self.buffer_distance,
            font=("Helvetica", 11),
            width=15,
            bg="white",
            validate="key",
            validatecommand=(self.root.register(self._validate_distance), '%P')
        )
        distance_entry.pack(side=tk.LEFT)
        
        # Botones de distancia predefinida
        preset_distances = [50, 100, 250, 500, 1000]
        for dist in preset_distances:
            btn = tk.Button(
                distance_frame,
                text=format_distance(dist),
                command=lambda d=dist: self.buffer_distance.set(str(d)),
                bg="#F0F0F0",
                fg="#333333",
                font=("Helvetica", 9),
                relief="solid",
                bd=1,
                padx=8,
                pady=2
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Información de rango
        range_label = tk.Label(
            config_frame,
            text=f"Rango válido: {BUFFER_CONFIG['min_distance']} - {format_distance(BUFFER_CONFIG['max_distance'])}",
            font=("Helvetica", 9),
            bg=self.root.cget("bg"),
            fg="#666666"
        )
        range_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 5))
    
    def _create_advanced_options_frame(self):
        """Crea el frame de opciones avanzadas."""
        options_frame = tk.LabelFrame(
            self.main_frame,
            text="Opciones Avanzadas",
            font=("Helvetica", 12, "bold"),
            bg=self.root.cget("bg"),
            fg="#E4610F",
            padx=15,
            pady=10
        )
        options_frame.grid(row=4, column=0, columnspan=3, pady=15, sticky="ew", padx=20)
        
        # Opción de combinar buffers
        combine_cb = tk.Checkbutton(
            options_frame,
            text="Combinar todos los buffers en un solo polígono",
            variable=self.combine_buffers,
            font=("Helvetica", 11),
            bg=self.root.cget("bg"),
            activebackground=self.root.cget("bg")
        )
        combine_cb.grid(row=0, column=0, sticky="w", pady=5)
        
        # Información sobre la opción
        info_label = tk.Label(
            options_frame,
            text="• Activado: Crea un único polígono que une todos los buffers\n• Desactivado: Mantiene buffers individuales junto con geometrías originales",
            font=("Helvetica", 9),
            bg=self.root.cget("bg"),
            fg="#666666",
            justify=tk.LEFT
        )
        info_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 5))
        
        # Configurar grid
        options_frame.grid_columnconfigure(0, weight=1)
    
    def _create_help_section(self):
        """Crea la sección de ayuda."""
        help_text = """
Información sobre buffers:
• Los buffers se aplican a todas las geometrías del archivo KMZ (puntos, líneas, polígonos)
• La distancia se especifica en metros
• Se preserva el sistema de coordenadas original
• El resultado incluye tanto las geometrías originales como los buffers (excepto si se combinan)
• Compatible con Google Earth y otras aplicaciones SIG
        """
        
        help_label = tk.Label(
            self.main_frame,
            text=help_text,
            font=("Helvetica", 10),
            bg=self.root.cget("bg"),
            fg="#666666",
            justify=tk.LEFT
        )
        help_label.grid(row=8, column=0, columnspan=3, pady=(20, 0), sticky="w")
    
    def _validate_distance(self, value):
        """Valida la entrada de distancia."""
        if not value:
            return True
        
        try:
            dist = float(value.replace(',', '.'))
            return BUFFER_CONFIG["min_distance"] <= dist <= BUFFER_CONFIG["max_distance"]
        except ValueError:
            return False
    
    def _browse_input_file(self):
        """Abre diálogo para seleccionar archivo KMZ de entrada."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo KMZ",
            filetypes=[("Archivos KMZ", "*.kmz"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.input_file.set(file_path)
            self.status_var.set(f"Archivo seleccionado: {os.path.basename(file_path)}")
            
            # Auto-generar nombre de salida
            if not self.output_file.get():
                base_name = os.path.splitext(file_path)[0]
                distance = self.buffer_distance.get() or "buffer"
                self.output_file.set(f"{base_name}_buffer_{distance}m.kmz")
    
    def _browse_output_file(self):
        """Abre diálogo para seleccionar ubicación de archivo KMZ."""
        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo KMZ como",
            defaultextension=".kmz",
            filetypes=[("Archivos KMZ", "*.kmz"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.output_file.set(file_path)
    
    def _preview_geometries(self):
        """Muestra vista previa de las geometrías del KMZ."""
        try:
            InputValidator.validate_file_path_input(self.input_file.get(), "kmz")
            
            # Ejecutar vista previa en hilo separado
            thread = threading.Thread(target=self._preview_geometries_thread)
            thread.daemon = True
            thread.start()
            
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            logger.error(f"Error iniciando vista previa: {e}")
            self.show_error(f"Error inesperado: {e}")
    
    def _preview_geometries_thread(self):
        """Ejecuta la vista previa en un hilo separado."""
        try:
            self.root.after(0, lambda: self.set_processing(True, "Analizando geometrías..."))
            
            # Leer archivo KMZ
            import tempfile
            import geopandas as gpd
            from core.utils import extract_kmz_to_kml
            
            temp_dir = tempfile.mkdtemp()
            kml_path = extract_kmz_to_kml(self.input_file.get(), temp_dir)
            gdf = gpd.read_file(kml_path, driver='KML')
            
            # Analizar geometrías
            geom_info = {
                "total": len(gdf),
                "points": len(gdf[gdf.geometry.type.isin(['Point', 'MultiPoint'])]),
                "lines": len(gdf[gdf.geometry.type.isin(['LineString', 'MultiLineString'])]),
                "polygons": len(gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]),
                "bounds": gdf.total_bounds if not gdf.empty else None,
                "crs": str(gdf.crs) if gdf.crs else "No definido"
            }
            
            # Mostrar ventana de vista previa
            self.root.after(0, lambda: self._show_preview_window(geom_info))
            
        except Exception as e:
            logger.error(f"Error en vista previa: {e}")
            self.root.after(0, lambda: self.show_error(f"Error analizando geometrías: {e}"))
        finally:
            self.root.after(0, lambda: self.set_processing(False))
    
    def _show_preview_window(self, geom_info):
        """Muestra ventana con información de geometrías."""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Vista Previa de Geometrías")
        preview_window.geometry("500x400")
        preview_window.configure(bg="white")
        
        # Título
        title_label = tk.Label(
            preview_window,
            text="Información de Geometrías",
            font=("Helvetica", 16, "bold"),
            bg="white",
            fg="#E4610F"
        )
        title_label.pack(pady=20)
        
        # Frame para información
        info_frame = tk.Frame(preview_window, bg="white")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Información de geometrías
        info_items = [
            ("Total de geometrías:", str(geom_info["total"])),
            ("Puntos:", str(geom_info["points"])),
            ("Líneas:", str(geom_info["lines"])),
            ("Polígonos:", str(geom_info["polygons"])),
            ("Sistema de coordenadas:", geom_info["crs"])
        ]
        
        for i, (label, value) in enumerate(info_items):
            tk.Label(
                info_frame,
                text=label,
                font=("Helvetica", 12, "bold"),
                bg="white",
                anchor="w"
            ).grid(row=i, column=0, sticky="w", pady=5)
            
            tk.Label(
                info_frame,
                text=value,
                font=("Helvetica", 12),
                bg="white",
                fg="#333333",
                anchor="w"
            ).grid(row=i, column=1, sticky="w", padx=20, pady=5)
        
        # Bounds si están disponibles
        if geom_info["bounds"] is not None:
            bounds = geom_info["bounds"]
            bounds_text = f"X: {bounds[0]:.6f} a {bounds[2]:.6f}\nY: {bounds[1]:.6f} a {bounds[3]:.6f}"
            
            tk.Label(
                info_frame,
                text="Extensión geográfica:",
                font=("Helvetica", 12, "bold"),
                bg="white",
                anchor="w"
            ).grid(row=len(info_items), column=0, sticky="nw", pady=5)
            
            tk.Label(
                info_frame,
                text=bounds_text,
                font=("Helvetica", 10),
                bg="white",
                fg="#333333",
                anchor="w",
                justify=tk.LEFT
            ).grid(row=len(info_items), column=1, sticky="w", padx=20, pady=5)
        
        # Configurar grid
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Botón cerrar
        tk.Button(
            preview_window,
            text="Cerrar",
            command=preview_window.destroy,
            bg="#E4610F",
            fg="white",
            font=("Helvetica", 12),
            padx=20,
            pady=8
        ).pack(pady=20)
    
    def _generate_buffer(self):
        """Genera el buffer en el archivo KMZ."""
        if self.is_processing:
            return
        
        try:
            # Validar entradas
            InputValidator.validate_file_path_input(self.input_file.get(), "kmz")
            output_path = InputValidator.validate_output_path(self.output_file.get(), ".kmz")
            
            # Validar distancia
            distance = DataValidator.validate_buffer_distance(self.buffer_distance.get())
            
            # Ejecutar en hilo separado
            thread = threading.Thread(
                target=self._generate_buffer_thread,
                args=(self.input_file.get(), output_path, distance)
            )
            thread.daemon = True
            thread.start()
            
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            logger.error(f"Error iniciando generación de buffer: {e}")
            self.show_error(f"Error inesperado: {e}")
    
    def _generate_buffer_thread(self, input_path: str, output_path: str, distance: float):
        """Ejecuta la generación de buffer en un hilo separado."""
        try:
            self.root.after(0, lambda: self.set_processing(True, f"Generando buffer de {format_distance(distance)}..."))
            
            # Generar buffer
            success = self.processor.apply_buffer_to_kmz(
                input_path,
                output_path,
                distance,
                self.combine_buffers.get()
            )
            
            if success:
                buffer_type = "combinado" if self.combine_buffers.get() else "individual"
                message = f"Buffer {buffer_type} de {format_distance(distance)} generado exitosamente:\n{output_path}"
                self.root.after(0, lambda: self.show_success(message))
            else:
                self.root.after(0, lambda: self.show_error("Error durante la generación del buffer"))
                
        except Exception as e:
            logger.error(f"Error en generación de buffer: {e}")
            self.root.after(0, lambda: self.show_error(f"Error durante la generación: {e}"))
        finally:
            self.root.after(0, lambda: self.set_processing(False))
    
    def _return_to_menu(self):
        """Regresa al menú principal."""
        self.close()

def main():
    """Función principal para testing."""
    app = BufferGeneratorPage()
    app.show()

if __name__ == "__main__":
    main()
