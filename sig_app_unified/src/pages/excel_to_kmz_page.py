
"""
Página para crear archivos KMZ desde datos de Excel.
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
from src.core.validators import InputValidator, ValidationError
from src.core.config import logger, DEFAULT_CRS

class ExcelToKMZPage(BaseWindow):
    """Página para crear KMZ desde Excel."""
    
    def __init__(self, parent=None):
        super().__init__("Crear KMZ desde Excel", 850, 600, True, parent)
        
        self.processor = KMZProcessor()
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        # Variables para configuración de columnas
        self.name_col = tk.StringVar(value="nombre")
        self.x_col = tk.StringVar(value="este")
        self.y_col = tk.StringVar(value="norte")
        self.desc_col = tk.StringVar(value="descripcion")
        
        self._create_interface()
        self.configure_grid_weights()
    
    def _create_interface(self):
        """Crea la interfaz de la página."""
        
        # Título
        self.create_title("Crear KMZ desde datos de Excel")
        
        # Selector de archivo Excel de entrada
        self.create_file_selector(
            "Archivo Excel de entrada:",
            1,
            [("Archivos Excel", "*.xlsx *.xls")],
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
        
        # Frame para configuración de columnas
        self._create_column_config_frame()
        
        # Frame para opciones de CRS
        self._create_crs_config_frame()
        
        # Botones de acción
        button_frame = tk.Frame(self.main_frame, bg=self.root.cget("bg"))
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        self.create_action_button(
            "Crear KMZ",
            self._create_kmz,
            6, 1, "primary"
        )
        
        self.create_action_button(
            "Vista Previa",
            self._preview_data,
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
        self._create_info_section()
    
    def _create_column_config_frame(self):
        """Crea el frame de configuración de columnas."""
        config_frame = tk.LabelFrame(
            self.main_frame,
            text="Configuración de Columnas",
            font=("Helvetica", 12, "bold"),
            bg=self.root.cget("bg"),
            fg="#E4610F",
            padx=10,
            pady=10
        )
        config_frame.grid(row=3, column=0, columnspan=3, pady=15, sticky="ew", padx=20)
        
        # Configurar grid
        for i in range(4):
            config_frame.grid_columnconfigure(i, weight=1)
        
        # Campos de configuración
        configs = [
            ("Columna Nombre:", self.name_col, "nombre"),
            ("Columna Este/X:", self.x_col, "este"),
            ("Columna Norte/Y:", self.y_col, "norte"),
            ("Columna Descripción:", self.desc_col, "descripcion")
        ]
        
        for i, (label_text, var, default) in enumerate(configs):
            tk.Label(
                config_frame,
                text=label_text,
                font=("Helvetica", 10),
                bg=self.root.cget("bg")
            ).grid(row=0, column=i, sticky="w", padx=5)
            
            entry = tk.Entry(
                config_frame,
                textvariable=var,
                font=("Helvetica", 10),
                width=12,
                bg="white"
            )
            entry.grid(row=1, column=i, padx=5, pady=5, sticky="ew")
    
    def _create_crs_config_frame(self):
        """Crea el frame de configuración de CRS."""
        crs_frame = tk.LabelFrame(
            self.main_frame,
            text="Sistema de Coordenadas de Origen",
            font=("Helvetica", 12, "bold"),
            bg=self.root.cget("bg"),
            fg="#E4610F",
            padx=10,
            pady=10
        )
        crs_frame.grid(row=4, column=0, columnspan=3, pady=15, sticky="ew", padx=20)
        
        self.source_crs = tk.StringVar(value="UTM 19S (Chile)")
        
        crs_options = [
            "UTM 19S (Chile)",
            "WGS84 (Geográficas)",
            "Auto-detectar zona UTM"
        ]
        
        for i, option in enumerate(crs_options):
            rb = tk.Radiobutton(
                crs_frame,
                text=option,
                variable=self.source_crs,
                value=option,
                font=("Helvetica", 10),
                bg=self.root.cget("bg")
            )
            rb.grid(row=0, column=i, padx=20, pady=5, sticky="w")
    
    def _create_info_section(self):
        """Crea la sección de información."""
        info_text = """
Información:
• El archivo Excel debe contener al menos las columnas de nombre y coordenadas
• Las coordenadas deben estar en formato numérico
• La columna descripción es opcional
• El KMZ resultante será compatible con Google Earth y otras aplicaciones SIG
        """
        
        info_label = tk.Label(
            self.main_frame,
            text=info_text,
            font=("Helvetica", 10),
            bg=self.root.cget("bg"),
            fg="#666666",
            justify=tk.LEFT
        )
        info_label.grid(row=8, column=0, columnspan=3, pady=(20, 0), sticky="w")
    
    def _browse_input_file(self):
        """Abre diálogo para seleccionar archivo Excel."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[
                ("Archivos Excel", "*.xlsx *.xls"),
                ("Todos los archivos", "*.*")
            ]
        )
        if file_path:
            self.input_file.set(file_path)
            self.status_var.set(f"Archivo seleccionado: {os.path.basename(file_path)}")
    
    def _browse_output_file(self):
        """Abre diálogo para seleccionar ubicación de archivo KMZ."""
        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo KMZ como",
            defaultextension=".kmz",
            filetypes=[("Archivos KMZ", "*.kmz"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.output_file.set(file_path)
    
    def _get_source_crs(self):
        """Obtiene el CRS de origen basado en la selección."""
        crs_selection = self.source_crs.get()
        
        if crs_selection == "UTM 19S (Chile)":
            return DEFAULT_CRS["utm_chile"]
        elif crs_selection == "WGS84 (Geográficas)":
            return DEFAULT_CRS["geographic"]
        else:  # Auto-detectar
            return "auto"
    
    def _preview_data(self):
        """Muestra vista previa de los datos del Excel."""
        try:
            InputValidator.validate_file_path_input(self.input_file.get(), "excel")
            
            import pandas as pd
            df = pd.read_excel(self.input_file.get())
            
            # Crear ventana de vista previa
            preview_window = tk.Toplevel(self.root)
            preview_window.title("Vista Previa de Datos")
            preview_window.geometry("800x400")
            preview_window.configure(bg="white")
            
            # Frame para la tabla
            table_frame = tk.Frame(preview_window)
            table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Crear Treeview para mostrar datos
            columns = list(df.columns)
            tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
            
            # Configurar columnas
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            
            # Agregar datos (primeras 50 filas)
            for index, row in df.head(50).iterrows():
                tree.insert("", "end", values=list(row))
            
            # Scrollbars
            v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Posicionar widgets
            tree.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            table_frame.grid_rowconfigure(0, weight=1)
            table_frame.grid_columnconfigure(0, weight=1)
            
            # Información
            info_label = tk.Label(
                preview_window,
                text=f"Mostrando primeras 50 filas de {len(df)} total. Columnas disponibles: {', '.join(columns)}",
                bg="white",
                fg="#666666"
            )
            info_label.pack(pady=5)
            
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            logger.error(f"Error en vista previa: {e}")
            self.show_error(f"Error mostrando vista previa: {e}")
    
    def _create_kmz(self):
        """Crea el archivo KMZ desde Excel."""
        if self.is_processing:
            return
        
        try:
            # Validar entradas
            InputValidator.validate_file_path_input(self.input_file.get(), "excel")
            output_path = InputValidator.validate_output_path(self.output_file.get(), ".kmz")
            
            # Validar configuración de columnas
            required_cols = [self.name_col.get(), self.x_col.get(), self.y_col.get()]
            if not all(col.strip() for col in required_cols):
                raise ValidationError("Debe especificar nombres para las columnas requeridas")
            
            # Ejecutar en hilo separado
            thread = threading.Thread(
                target=self._create_kmz_thread,
                args=(self.input_file.get(), output_path)
            )
            thread.daemon = True
            thread.start()
            
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            logger.error(f"Error iniciando creación de KMZ: {e}")
            self.show_error(f"Error inesperado: {e}")
    
    def _create_kmz_thread(self, input_path: str, output_path: str):
        """Ejecuta la creación de KMZ en un hilo separado."""
        try:
            self.root.after(0, lambda: self.set_processing(True, "Creando archivo KMZ..."))
            
            # Obtener configuración
            source_crs = self._get_source_crs()
            
            # Procesar archivo
            success = self.processor.create_kmz_from_excel(
                input_path,
                output_path,
                name_col=self.name_col.get(),
                x_col=self.x_col.get(),
                y_col=self.y_col.get(),
                desc_col=self.desc_col.get(),
                source_crs=source_crs
            )
            
            if success:
                message = f"Archivo KMZ creado exitosamente:\n{output_path}"
                self.root.after(0, lambda: self.show_success(message))
            else:
                self.root.after(0, lambda: self.show_error("Error durante la creación del KMZ"))
                
        except Exception as e:
            logger.error(f"Error en creación de KMZ: {e}")
            self.root.after(0, lambda: self.show_error(f"Error durante la creación: {e}"))
        finally:
            self.root.after(0, lambda: self.set_processing(False))
    
    def _return_to_menu(self):
        """Regresa al menú principal."""
        self.close()

def main():
    """Función principal para testing."""
    app = ExcelToKMZPage()
    app.show()

if __name__ == "__main__":
    main()
