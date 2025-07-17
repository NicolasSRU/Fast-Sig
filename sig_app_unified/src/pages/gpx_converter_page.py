
"""
Página para convertir archivos GPX a KMZ.
"""

import tkinter as tk
from tkinter import filedialog, ttk
import threading
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ui.base_window import BaseWindow
from src.core.gpx_processor import GPXProcessor
from src.core.validators import InputValidator, ValidationError
from src.core.config import logger

class GPXConverterPage(BaseWindow):
    """Página para convertir GPX a KMZ."""
    
    def __init__(self, parent=None):
        super().__init__("Convertir GPX a KMZ", 800, 550, True, parent)
        
        self.processor = GPXProcessor()
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.gpx_info = {}
        
        self._create_interface()
        self.configure_grid_weights()
    
    def _create_interface(self):
        """Crea la interfaz de la página."""
        
        # Título
        self.create_title("Convertir archivos GPX a KMZ")
        
        # Selector de archivo GPX de entrada
        self.create_file_selector(
            "Archivo GPX de entrada:",
            1,
            [("Archivos GPX", "*.gpx")],
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
        
        # Frame para información del GPX
        self._create_info_frame()
        
        # Botones de acción
        button_frame = tk.Frame(self.main_frame, bg=self.root.cget("bg"))
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.create_action_button(
            "Convertir a KMZ",
            self._convert_gpx,
            4, 1, "primary"
        )
        
        self.create_action_button(
            "Analizar GPX",
            self._analyze_gpx,
            4, 0, "secondary"
        )
        
        self.create_action_button(
            "Volver al Menú",
            self._return_to_menu,
            4, 2, "secondary"
        )
        
        # Etiqueta de estado
        self.create_status_label(5)
        
        # Información adicional
        self._create_help_section()
    
    def _create_info_frame(self):
        """Crea el frame de información del GPX."""
        self.info_frame = tk.LabelFrame(
            self.main_frame,
            text="Información del archivo GPX",
            font=("Helvetica", 12, "bold"),
            bg=self.root.cget("bg"),
            fg="#E4610F",
            padx=15,
            pady=10
        )
        self.info_frame.grid(row=3, column=0, columnspan=3, pady=15, sticky="ew", padx=20)
        
        # Crear labels para mostrar información
        self.info_labels = {}
        info_items = [
            ("tracks", "Tracks:"),
            ("routes", "Rutas:"),
            ("waypoints", "Waypoints:"),
            ("total_points", "Total de puntos:"),
            ("total_distance", "Distancia total:"),
            ("bounds", "Área geográfica:")
        ]
        
        for i, (key, label_text) in enumerate(info_items):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(
                self.info_frame,
                text=label_text,
                font=("Helvetica", 10, "bold"),
                bg=self.root.cget("bg")
            ).grid(row=row, column=col, sticky="w", padx=5, pady=2)
            
            info_label = tk.Label(
                self.info_frame,
                text="No disponible",
                font=("Helvetica", 10),
                bg=self.root.cget("bg"),
                fg="#666666"
            )
            info_label.grid(row=row, column=col+1, sticky="w", padx=5, pady=2)
            self.info_labels[key] = info_label
        
        # Configurar grid
        for i in range(4):
            self.info_frame.grid_columnconfigure(i, weight=1)
    
    def _create_help_section(self):
        """Crea la sección de ayuda."""
        help_text = """
Información sobre conversión GPX:
• Tracks: Se convierten a líneas (LineString) en el KMZ
• Rutas: Se convierten a líneas con diferente estilo
• Waypoints: Se convierten a puntos (Point) en el KMZ
• Se preserva la información de elevación cuando está disponible
• El archivo KMZ resultante es compatible con Google Earth
        """
        
        help_label = tk.Label(
            self.main_frame,
            text=help_text,
            font=("Helvetica", 10),
            bg=self.root.cget("bg"),
            fg="#666666",
            justify=tk.LEFT
        )
        help_label.grid(row=6, column=0, columnspan=3, pady=(20, 0), sticky="w")
    
    def _browse_input_file(self):
        """Abre diálogo para seleccionar archivo GPX."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo GPX",
            filetypes=[("Archivos GPX", "*.gpx"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.input_file.set(file_path)
            self.status_var.set(f"Archivo seleccionado: {os.path.basename(file_path)}")
            
            # Auto-generar nombre de salida
            if not self.output_file.get():
                base_name = os.path.splitext(file_path)[0]
                self.output_file.set(f"{base_name}.kmz")
            
            # Limpiar información previa
            self._clear_gpx_info()
    
    def _browse_output_file(self):
        """Abre diálogo para seleccionar ubicación de archivo KMZ."""
        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo KMZ como",
            defaultextension=".kmz",
            filetypes=[("Archivos KMZ", "*.kmz"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.output_file.set(file_path)
    
    def _clear_gpx_info(self):
        """Limpia la información del GPX mostrada."""
        for label in self.info_labels.values():
            label.configure(text="No disponible", fg="#666666")
        self.gpx_info = {}
    
    def _analyze_gpx(self):
        """Analiza el archivo GPX y muestra información."""
        try:
            InputValidator.validate_file_path_input(self.input_file.get(), "gpx")
            
            # Ejecutar análisis en hilo separado
            thread = threading.Thread(target=self._analyze_gpx_thread)
            thread.daemon = True
            thread.start()
            
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            logger.error(f"Error iniciando análisis: {e}")
            self.show_error(f"Error inesperado: {e}")
    
    def _analyze_gpx_thread(self):
        """Ejecuta el análisis del GPX en un hilo separado."""
        try:
            self.root.after(0, lambda: self.set_processing(True, "Analizando archivo GPX..."))
            
            # Obtener información del GPX
            self.gpx_info = self.processor.get_gpx_info(self.input_file.get())
            
            # Actualizar interfaz
            self.root.after(0, self._update_gpx_info_display)
            
        except Exception as e:
            logger.error(f"Error analizando GPX: {e}")
            self.root.after(0, lambda: self.show_error(f"Error analizando GPX: {e}"))
        finally:
            self.root.after(0, lambda: self.set_processing(False))
    
    def _update_gpx_info_display(self):
        """Actualiza la visualización de información del GPX."""
        if "error" in self.gpx_info:
            self.show_error(f"Error leyendo GPX: {self.gpx_info['error']}")
            return
        
        # Actualizar labels con información
        updates = {
            "tracks": str(self.gpx_info.get("tracks", 0)),
            "routes": str(self.gpx_info.get("routes", 0)),
            "waypoints": str(self.gpx_info.get("waypoints", 0)),
            "total_points": str(self.gpx_info.get("total_points", 0))
        }
        
        # Formatear distancia
        distance = self.gpx_info.get("total_distance", 0)
        if distance > 0:
            if distance >= 1000:
                updates["total_distance"] = f"{distance/1000:.2f} km"
            else:
                updates["total_distance"] = f"{distance:.0f} m"
        else:
            updates["total_distance"] = "No disponible"
        
        # Formatear bounds
        bounds = self.gpx_info.get("bounds")
        if bounds:
            updates["bounds"] = f"Lat: {bounds['min_lat']:.4f} a {bounds['max_lat']:.4f}, Lon: {bounds['min_lon']:.4f} a {bounds['max_lon']:.4f}"
        else:
            updates["bounds"] = "No disponible"
        
        # Actualizar labels
        for key, value in updates.items():
            if key in self.info_labels:
                self.info_labels[key].configure(text=value, fg="#333333")
        
        self.status_var.set("Análisis completado")
    
    def _convert_gpx(self):
        """Convierte el archivo GPX a KMZ."""
        if self.is_processing:
            return
        
        try:
            # Validar entradas
            InputValidator.validate_file_path_input(self.input_file.get(), "gpx")
            output_path = InputValidator.validate_output_path(self.output_file.get(), ".kmz")
            
            # Ejecutar en hilo separado
            thread = threading.Thread(
                target=self._convert_gpx_thread,
                args=(self.input_file.get(), output_path)
            )
            thread.daemon = True
            thread.start()
            
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            logger.error(f"Error iniciando conversión: {e}")
            self.show_error(f"Error inesperado: {e}")
    
    def _convert_gpx_thread(self, input_path: str, output_path: str):
        """Ejecuta la conversión en un hilo separado."""
        try:
            self.root.after(0, lambda: self.set_processing(True, "Convirtiendo GPX a KMZ..."))
            
            # Convertir archivo
            result_path = self.processor.convert_gpx_to_kmz(input_path, output_path)
            
            if result_path:
                message = f"Archivo convertido exitosamente:\n{result_path}"
                self.root.after(0, lambda: self.show_success(message))
            else:
                self.root.after(0, lambda: self.show_error("Error durante la conversión"))
                
        except Exception as e:
            logger.error(f"Error en conversión: {e}")
            self.root.after(0, lambda: self.show_error(f"Error durante la conversión: {e}"))
        finally:
            self.root.after(0, lambda: self.set_processing(False))
    
    def _return_to_menu(self):
        """Regresa al menú principal."""
        self.close()

def main():
    """Función principal para testing."""
    app = GPXConverterPage()
    app.show()

if __name__ == "__main__":
    main()
