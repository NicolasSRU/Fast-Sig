
"""
Configuración global de la aplicación SIG.
Define constantes, estilos y configuraciones compartidas.
"""

import os
import logging
from pathlib import Path

# Configuración de directorios
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEMP_DIR = PROJECT_ROOT / "temp"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorios si no existen
for directory in [DATA_DIR, TEMP_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Configuración de colores y estilo (tema naranja)
UI_COLORS = {
    "bg_primary": "#FFFFFF",        # Blanco principal
    "bg_secondary": "#F8F9FA",      # Gris muy claro
    "accent_primary": "#E4610F",    # Naranja principal
    "accent_hover": "#F47D3C",      # Naranja hover
    "accent_dark": "#CC5A0E",       # Naranja oscuro
    "text_primary": "#212529",      # Negro principal
    "text_secondary": "#6C757D",    # Gris texto
    "success": "#28A745",           # Verde éxito
    "warning": "#FFC107",           # Amarillo advertencia
    "error": "#DC3545",             # Rojo error
    "border": "#DEE2E6"             # Gris borde
}

# Configuración de fuentes
UI_FONTS = {
    "title": ("Helvetica", 18, "bold"),
    "subtitle": ("Helvetica", 14, "bold"),
    "body": ("Helvetica", 12),
    "small": ("Helvetica", 10),
    "button": ("Helvetica", 12, "bold")
}

# Configuración de CRS por defecto
DEFAULT_CRS = {
    "geographic": "EPSG:4326",      # WGS84
    "utm_chile": "EPSG:32719",      # UTM Zona 19S (Chile)
    "utm_auto": "auto"              # Auto-detectar zona UTM
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": logging.INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "sig_app.log"
}

# Configuración de archivos soportados
SUPPORTED_FORMATS = {
    "kmz": [".kmz"],
    "kml": [".kml"],
    "gpx": [".gpx"],
    "excel": [".xlsx", ".xls"],
    "shapefile": [".shp"]
}

# Configuración de buffer por defecto
BUFFER_CONFIG = {
    "default_distance": 100,        # metros
    "min_distance": 1,
    "max_distance": 10000,
    "default_segments": 16
}

# Mensajes de la aplicación
MESSAGES = {
    "success": {
        "file_processed": "Archivo procesado exitosamente",
        "export_complete": "Exportación completada",
        "conversion_complete": "Conversión completada"
    },
    "error": {
        "file_not_found": "Archivo no encontrado",
        "invalid_format": "Formato de archivo no válido",
        "processing_error": "Error durante el procesamiento",
        "no_data": "No se encontraron datos para procesar"
    },
    "warning": {
        "large_file": "El archivo es muy grande, el procesamiento puede tardar",
        "no_crs": "No se detectó sistema de coordenadas, usando WGS84"
    }
}

def setup_logging():
    """Configura el sistema de logging de la aplicación."""
    logging.basicConfig(
        level=LOGGING_CONFIG["level"],
        format=LOGGING_CONFIG["format"],
        handlers=[
            logging.FileHandler(LOGGING_CONFIG["file"]),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Logger global
logger = setup_logging()
