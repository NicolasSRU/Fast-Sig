
"""
Página para extraer coordenadas de archivos KMZ a Excel.
"""

import tkinter as tk
from tkinter import filedialog
import threading
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ui.base_window import BaseWindow
from src.core.kmz_processor import KMZProcessor
from src.core.validators import InputValidator, ValidationError
from src.core.config import logger, SUPPORTED_FORMATS

class KMZExtractorPage(BaseWindow):
    """Página para extraer coordenadas de KMZ a Excel."""
    
    def __init__(self, parent=None):
        super().__init__("Extraer Coordenadas KMZ → Excel", 800, 500, True, parent)
        
        self.processor = KMZProcessor()
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        self._create_interface()
        self.configure_grid_weights()
    
    def _create_interface(self):
        """Crea la interfaz de la página."""
        
        # Título
        self.create_title("Extraer Coordenadas de KMZ a Excel")
        
        # Selector de archivo KMZ de entrada
        self.create_file_selector(
            "Archivo KMZ de entrada:",
            1,
            [("Archivos KMZ", "*.kmz")],
            self._browse_input_file,
            self.input_file
        )
        
        # Selector de archivo Excel de salida
        self.create_file_selector(
            "Guardar Excel como:",
            2,
            [("Archivos Excel", "*.xlsx")],
            self._browse_output_file,
            self.output_file
        )
        
        # Frame para opciones adicionales
        options_frame = tk.Frame(self.main_frame, bg=self.root.cget("bg"))
        options_frame.grid(row=3, column=0, columnspan=3, pady=15, sticky="ew")
        
        # Opción de sistema de coordenadas
        tk.Label(
            options_frame,
            text="Sistema de coordenadas de salida:",
            font=("Helvetica", 12),
            bg=self.root.cget("bg")
        ).pack(side=tk.LEFT)
        
        self.crs_var = tk.StringVar(value="UTM 19S (Chile)")
        crs_combo = tk.OptionMenu(
            options_frame,
            self.crs_var,
            "UTM 19S (Chile)",
            "WGS84 (Geográficas)",
            "Auto-detectar"
        )
        crs_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botones de acción
        button_frame = tk.Frame(self.main_frame, bg=self.root.cget("bg"))
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.create_action_button(
            "Extraer Coordenadas",
            self._extract_coordinates,
            4, 1, "primary"
        )
        
        self.create_action_button(
            "Volver al Menú",
            self._return_to_menu,
            4, 2, "secondary"
        )
        
        # Etiqueta de estado
        self.create_status_label(5)
        
        # Información adicional
        info_text = """
Información:
• El archivo KMZ debe contener puntos geográficos (Placemarks)
• Las coordenadas se extraen y convierten al sistema seleccionado
• El archivo Excel incluirá: Nombre, Descripción, Longitud, Latitud, Este, Norte
        """
        
        info_label = tk.Label(
            self.main_frame,
            text=info_text,
            font=("Helvetica", 10),
            bg=self.root.cget("bg"),
            fg="#666666",
            justify=tk.LEFT
        )
        info_label.grid(row=6, column=0, columnspan=3, pady=(20, 0), sticky="w")
    
    def _browse_input_file(self):
        """Abre diálogo para seleccionar archivo KMZ de entrada."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo KMZ",
            filetypes=[("Archivos KMZ", "*.kmz"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.input_file.set(file_path)
            self.status_var.set(f"Archivo seleccionado: {os.path.basename(file_path)}")
    
    def _browse_output_file(self):
        """Abre diálogo para seleccionar ubicación de archivo Excel."""
        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo Excel como",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.output_file.set(file_path)
    
    def _get_target_crs(self):
        """Obtiene el CRS de destino basado en la selección."""
        crs_selection = self.crs_var.get()
        
        if crs_selection == "UTM 19S (Chile)":
            return "EPSG:32719"
        elif crs_selection == "WGS84 (Geográficas)":
            return "EPSG:4326"
        else:  # Auto-detectar
            return "auto"
    
    def _extract_coordinates(self):
        """Extrae coordenadas del KMZ a Excel."""
        if self.is_processing:
            return
        
        try:
            # Validar entradas
            InputValidator.validate_file_path_input(self.input_file.get(), "kmz")
            output_path = InputValidator.validate_output_path(self.output_file.get(), ".xlsx")
            
            # Ejecutar en hilo separado
            thread = threading.Thread(
                target=self._extract_coordinates_thread,
                args=(self.input_file.get(), output_path)
            )
            thread.daemon = True
            thread.start()
            
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            logger.error(f"Error iniciando extracción: {e}")
            self.show_error(f"Error inesperado: {e}")
    
    def _extract_coordinates_thread(self, input_path: str, output_path: str):
        """Ejecuta la extracción en un hilo separado."""
        try:
            self.root.after(0, lambda: self.set_processing(True, "Extrayendo coordenadas..."))
            
            # Obtener CRS de destino
            target_crs = self._get_target_crs()
            
            # Procesar archivo
            success = self.processor.extract_coordinates_to_excel(
                input_path, 
                output_path, 
                target_crs
            )
            
            if success:
                message = f"Coordenadas extraídas exitosamente a:\n{output_path}"
                self.root.after(0, lambda: self.show_success(message))
            else:
                self.root.after(0, lambda: self.show_error("Error durante la extracción"))
                
        except Exception as e:
            logger.error(f"Error en extracción: {e}")
            self.root.after(0, lambda: self.show_error(f"Error durante la extracción: {e}"))
        finally:
            self.root.after(0, lambda: self.set_processing(False))
    
    def _return_to_menu(self):
        """Regresa al menú principal."""
        self.close()

def main():
    """Función principal para testing."""
    app = KMZExtractorPage()
    app.show()

if __name__ == "__main__":
    main()
