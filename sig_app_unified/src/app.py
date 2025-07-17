
"""
Punto de entrada principal de la aplicación SIG unificada.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Agregar el directorio src al path para importaciones
sys.path.insert(0, os.path.dirname(__file__))

try:
    from src.ui.main_window import MainWindow
    from src.core.config import logger
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Asegúrese de que todas las dependencias estén instaladas")
    sys.exit(1)

def main():
    """Función principal de la aplicación."""
    try:
        # Configurar tkinter para manejar errores
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana temporal
        
        # Verificar dependencias críticas
        try:
            import geopandas
            import shapely
            import pyproj
            import gpxpy
            import pandas
            import openpyxl
        except ImportError as e:
            error_msg = f"Dependencia faltante: {e}\n\nPor favor instale las dependencias requeridas:\npip install geopandas shapely pyproj gpxpy pandas openpyxl"
            messagebox.showerror("Error de Dependencias", error_msg)
            logger.error(f"Dependencia faltante: {e}")
            return
        
        root.destroy()  # Destruir ventana temporal
        
        # Iniciar aplicación principal
        logger.info("Iniciando aplicación SIG unificada")
        app = MainWindow()
        app.run()
        
    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {e}")
        try:
            messagebox.showerror("Error Fatal", f"Error iniciando la aplicación:\n\n{e}")
        except:
            print(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
