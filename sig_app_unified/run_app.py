#!/usr/bin/env python3
"""
Script de ejecución principal para la aplicación SIG unificada.
"""

import sys
import os

# Agregar el directorio del proyecto al path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Importar y ejecutar la aplicación
if __name__ == "__main__":
    try:
        from src.ui.main_window import main
        main()
    except Exception as e:
        print(f"Error ejecutando la aplicación: {e}")
        import traceback
        traceback.print_exc()
