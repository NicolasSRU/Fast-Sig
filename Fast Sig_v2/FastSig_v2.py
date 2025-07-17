#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastSig v2.1.2 - Aplicación SIG Unificada
==========================================

CAMBIOS REALIZADOS EN LA VERSIÓN 2.1.2:
- Unificación de todos los módulos en un solo archivo Python
- Eliminación de dependencias de importación entre módulos
- Mantenimiento de toda la funcionalidad original
- Preservación de la estética y textos originales
- Agregado de información de versión y desarrollador en la ventana principal
- Optimización del código para ejecución independiente
- Documentación detallada de cambios realizados

FUNCIONALIDADES INCLUIDAS:
- Extractor de Coordenadas KMZ → Excel
- Creador KMZ Excel → KMZ  
- Conversor GPX → KMZ
- Generador de Buffers

DESARROLLADO POR: Nicolás Sanhueza mediante uso de Inteligencia Artificial
VERSIÓN: 2.1.2
FECHA: Julio 2025

Aplicación de escritorio completa para el procesamiento de datos geoespaciales 
con interfaz moderna en tono naranja.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict, Any, Optional, Callable
import threading
import logging
from pathlib import Path
import re

# Importaciones de librerías geoespaciales
try:
    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import Point
    from shapely.ops import unary_union
    from pyproj import Transformer, CRS
    import gpxpy
    import simplekml
except ImportError as e:
    print(f"Error importando dependencias: {e}")
    print("Por favor instale las dependencias requeridas:")
    print("pip install geopandas shapely pyproj gpxpy pandas openpyxl simplekml")
    sys.exit(1)

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

# Configuración de directorios
PROJECT_ROOT = Path.cwd()
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

# ============================================================================
# UTILIDADES COMPARTIDAS
# ============================================================================

def validate_file_exists(file_path: str) -> bool:
    """
    Valida que un archivo exista.
    
    Args:
        file_path: Ruta del archivo a validar
        
    Returns:
        True si el archivo existe, False en caso contrario
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)

def validate_file_format(file_path: str, expected_formats: List[str]) -> bool:
    """
    Valida que un archivo tenga el formato esperado.
    
    Args:
        file_path: Ruta del archivo
        expected_formats: Lista de extensiones válidas (ej: ['.kmz', '.kml'])
        
    Returns:
        True si el formato es válido, False en caso contrario
    """
    if not validate_file_exists(file_path):
        return False
    
    file_ext = Path(file_path).suffix.lower()
    return file_ext in expected_formats

def extract_kmz_to_kml(kmz_path: str, temp_dir: Optional[str] = None) -> str:
    """
    Extrae el archivo KML de un KMZ.
    
    Args:
        kmz_path: Ruta del archivo KMZ
        temp_dir: Directorio temporal (opcional)
        
    Returns:
        Ruta del archivo KML extraído
        
    Raises:
        ValueError: Si no se encuentra archivo KML en el KMZ
    """
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    
    try:
        with zipfile.ZipFile(kmz_path, 'r') as kmz:
            kmz.extractall(temp_dir)
        
        # Buscar archivo KML
        kml_files = [f for f in os.listdir(temp_dir) if f.endswith('.kml')]
        if not kml_files:
            raise ValueError("No se encontró archivo KML dentro del KMZ")
        
        return os.path.join(temp_dir, kml_files[0])
    
    except Exception as e:
        logger.error(f"Error extrayendo KMZ: {e}")
        raise

def create_kmz_from_kml(kml_path: str, kmz_path: str) -> None:
    """
    Crea un archivo KMZ a partir de un KML.
    
    Args:
        kml_path: Ruta del archivo KML
        kmz_path: Ruta de salida del KMZ
    """
    try:
        with zipfile.ZipFile(kmz_path, 'w', zipfile.ZIP_DEFLATED) as kmz:
            kmz.write(kml_path, os.path.basename(kml_path))
        logger.info(f"KMZ creado: {kmz_path}")
    except Exception as e:
        logger.error(f"Error creando KMZ: {e}")
        raise

def estimate_utm_crs(lon: float, lat: float) -> str:
    """
    Estima el CRS UTM apropiado para unas coordenadas dadas.
    
    Args:
        lon: Longitud
        lat: Latitud
        
    Returns:
        Código EPSG del CRS UTM estimado
    """
    # Calcular zona UTM
    utm_zone = int((lon + 180) / 6) + 1
    
    # Determinar hemisferio
    hemisphere = 'north' if lat >= 0 else 'south'
    
    # Construir código EPSG
    if hemisphere == 'north':
        epsg_code = f"EPSG:326{utm_zone:02d}"
    else:
        epsg_code = f"EPSG:327{utm_zone:02d}"
    
    return epsg_code

def auto_detect_crs(gdf: gpd.GeoDataFrame) -> str:
    """
    Auto-detecta el mejor CRS UTM para un GeoDataFrame.
    
    Args:
        gdf: GeoDataFrame con geometrías
        
    Returns:
        Código EPSG del CRS recomendado
    """
    try:
        if gdf.crs is None or gdf.crs.is_geographic:
            # Obtener centroide de los datos
            bounds = gdf.total_bounds
            center_lon = (bounds[0] + bounds[2]) / 2
            center_lat = (bounds[1] + bounds[3]) / 2
            
            return estimate_utm_crs(center_lon, center_lat)
        else:
            return gdf.crs.to_string()
    except Exception as e:
        logger.warning(f"Error auto-detectando CRS: {e}")
        return DEFAULT_CRS["utm_chile"]

def convert_coordinates(x: float, y: float, from_crs: str, to_crs: str) -> Tuple[float, float]:
    """
    Convierte coordenadas entre sistemas de referencia.
    
    Args:
        x, y: Coordenadas de entrada
        from_crs: CRS de origen
        to_crs: CRS de destino
        
    Returns:
        Tupla con coordenadas convertidas (x, y)
    """
    try:
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        return transformer.transform(x, y)
    except Exception as e:
        logger.error(f"Error convirtiendo coordenadas: {e}")
        raise

def validate_coordinates(lon: float, lat: float) -> bool:
    """
    Valida que las coordenadas estén en rangos válidos.
    
    Args:
        lon: Longitud
        lat: Latitud
        
    Returns:
        True si las coordenadas son válidas
    """
    return -180 <= lon <= 180 and -90 <= lat <= 90

def safe_float_conversion(value: str) -> Optional[float]:
    """
    Convierte un string a float de forma segura.
    
    Args:
        value: Valor a convertir
        
    Returns:
        Float convertido o None si falla
    """
    try:
        return float(value.replace(',', '.'))
    except (ValueError, AttributeError):
        return None

def format_distance(distance: float) -> str:
    """
    Formatea una distancia para mostrar.
    
    Args:
        distance: Distancia en metros
        
    Returns:
        String formateado con unidades
    """
    if distance >= 1000:
        return f"{distance/1000:.1f} km"
    else:
        return f"{distance:.0f} m"

def get_file_size_mb(file_path: str) -> float:
    """
    Obtiene el tamaño de un archivo en MB.
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Tamaño en MB
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0.0

def clean_temp_files(temp_dir: str) -> None:
    """
    Limpia archivos temporales.
    
    Args:
        temp_dir: Directorio temporal a limpiar
    """
    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.debug(f"Directorio temporal limpiado: {temp_dir}")
    except Exception as e:
        logger.warning(f"Error limpiando archivos temporales: {e}")

# ============================================================================
# VALIDADORES
# ============================================================================

class ValidationError(Exception):
    """Excepción personalizada para errores de validación."""
    pass

class FileValidator:
    """Validador para archivos de entrada."""
    
    @staticmethod
    def validate_kmz_file(file_path: str) -> bool:
        """
        Valida un archivo KMZ.
        
        Args:
            file_path: Ruta del archivo KMZ
            
        Returns:
            True si es válido
            
        Raises:
            ValidationError: Si el archivo no es válido
        """
        if not validate_file_exists(file_path):
            raise ValidationError(f"El archivo KMZ no existe: {file_path}")
        
        if not file_path.lower().endswith('.kmz'):
            raise ValidationError("El archivo debe tener extensión .kmz")
        
        # Validar que sea un archivo ZIP válido
        try:
            with zipfile.ZipFile(file_path, 'r') as kmz:
                # Verificar que contenga al menos un archivo KML
                kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
                if not kml_files:
                    raise ValidationError("El archivo KMZ no contiene archivos KML")
        except zipfile.BadZipFile:
            raise ValidationError("El archivo KMZ está corrupto")
        
        return True
    
    @staticmethod
    def validate_gpx_file(file_path: str) -> bool:
        """
        Valida un archivo GPX.
        
        Args:
            file_path: Ruta del archivo GPX
            
        Returns:
            True si es válido
            
        Raises:
            ValidationError: Si el archivo no es válido
        """
        if not validate_file_exists(file_path):
            raise ValidationError(f"El archivo GPX no existe: {file_path}")
        
        if not file_path.lower().endswith('.gpx'):
            raise ValidationError("El archivo debe tener extensión .gpx")
        
        # Validar contenido GPX básico
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
                
            # Verificar que tenga contenido
            has_content = (len(gpx.tracks) > 0 or 
                          len(gpx.routes) > 0 or 
                          len(gpx.waypoints) > 0)
            
            if not has_content:
                raise ValidationError("El archivo GPX no contiene tracks, rutas o waypoints")
                
        except Exception as e:
            raise ValidationError(f"Error parseando archivo GPX: {e}")
        
        return True
    
    @staticmethod
    def validate_excel_file(file_path: str, required_columns: List[str] = None) -> bool:
        """
        Valida un archivo Excel.
        
        Args:
            file_path: Ruta del archivo Excel
            required_columns: Columnas requeridas (opcional)
            
        Returns:
            True si es válido
            
        Raises:
            ValidationError: Si el archivo no es válido
        """
        if not validate_file_exists(file_path):
            raise ValidationError(f"El archivo Excel no existe: {file_path}")
        
        if not any(file_path.lower().endswith(ext) for ext in SUPPORTED_FORMATS["excel"]):
            raise ValidationError("El archivo debe ser .xlsx o .xls")
        
        try:
            df = pd.read_excel(file_path)
            
            if df.empty:
                raise ValidationError("El archivo Excel está vacío")
            
            if required_columns:
                missing_cols = set(required_columns) - set(df.columns)
                if missing_cols:
                    raise ValidationError(f"Faltan columnas requeridas: {missing_cols}")
                    
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Error leyendo archivo Excel: {e}")
        
        return True

class DataValidator:
    """Validador para datos geoespaciales."""
    
    @staticmethod
    def validate_coordinates_data(df: pd.DataFrame, lon_col: str = "este", 
                                lat_col: str = "norte") -> List[str]:
        """
        Valida datos de coordenadas en un DataFrame.
        
        Args:
            df: DataFrame con coordenadas
            lon_col: Nombre de columna de longitud/este
            lat_col: Nombre de columna de latitud/norte
            
        Returns:
            Lista de errores encontrados
        """
        errors = []
        
        # Verificar que existan las columnas
        if lon_col not in df.columns:
            errors.append(f"Columna '{lon_col}' no encontrada")
        if lat_col not in df.columns:
            errors.append(f"Columna '{lat_col}' no encontrada")
        
        if errors:
            return errors
        
        # Validar valores numéricos
        for idx, row in df.iterrows():
            try:
                lon = float(row[lon_col])
                lat = float(row[lat_col])
                
                # Validar rangos (asumiendo coordenadas geográficas o UTM)
                if abs(lon) > 1000000 or abs(lat) > 10000000:
                    errors.append(f"Fila {idx+1}: Coordenadas fuera de rango válido")
                
            except (ValueError, TypeError):
                errors.append(f"Fila {idx+1}: Coordenadas no numéricas")
        
        return errors
    
    @staticmethod
    def validate_buffer_distance(distance: str) -> float:
        """
        Valida y convierte distancia de buffer.
        
        Args:
            distance: Distancia como string
            
        Returns:
            Distancia como float
            
        Raises:
            ValidationError: Si la distancia no es válida
        """
        try:
            dist = float(distance.replace(',', '.'))
            
            if dist <= 0:
                raise ValidationError("La distancia debe ser mayor que 0")
            
            if dist > 100000:  # 100 km máximo
                raise ValidationError("La distancia máxima es 100,000 metros")
            
            return dist
            
        except ValueError:
            raise ValidationError("La distancia debe ser un número válido")
    
    @staticmethod
    def validate_geodataframe(gdf: gpd.GeoDataFrame) -> List[str]:
        """
        Valida un GeoDataFrame.
        
        Args:
            gdf: GeoDataFrame a validar
            
        Returns:
            Lista de errores/advertencias
        """
        issues = []
        
        if gdf.empty:
            issues.append("ERROR: GeoDataFrame vacío")
            return issues
        
        # Verificar geometrías válidas
        invalid_geoms = gdf.geometry.isna().sum()
        if invalid_geoms > 0:
            issues.append(f"ADVERTENCIA: {invalid_geoms} geometrías inválidas")
        
        # Verificar CRS
        if gdf.crs is None:
            issues.append("ADVERTENCIA: Sin sistema de coordenadas definido")
        
        # Verificar geometrías vacías
        empty_geoms = gdf.geometry.is_empty.sum()
        if empty_geoms > 0:
            issues.append(f"ADVERTENCIA: {empty_geoms} geometrías vacías")
        
        return issues

class InputValidator:
    """Validador para entradas de usuario en la interfaz."""
    
    @staticmethod
    def validate_file_path_input(path: str, file_type: str) -> bool:
        """
        Valida entrada de ruta de archivo.
        
        Args:
            path: Ruta ingresada por usuario
            file_type: Tipo de archivo esperado
            
        Returns:
            True si es válida
            
        Raises:
            ValidationError: Si la entrada no es válida
        """
        if not path or not path.strip():
            raise ValidationError("Debe seleccionar un archivo")
        
        path = path.strip()
        
        if file_type == "kmz":
            return FileValidator.validate_kmz_file(path)
        elif file_type == "gpx":
            return FileValidator.validate_gpx_file(path)
        elif file_type == "excel":
            return FileValidator.validate_excel_file(path)
        else:
            raise ValidationError(f"Tipo de archivo no soportado: {file_type}")
    
    @staticmethod
    def validate_output_path(path: str, extension: str) -> str:
        """
        Valida y normaliza ruta de salida.
        
        Args:
            path: Ruta de salida
            extension: Extensión esperada
            
        Returns:
            Ruta normalizada
            
        Raises:
            ValidationError: Si la ruta no es válida
        """
        if not path or not path.strip():
            raise ValidationError("Debe especificar una ruta de salida")
        
        path = path.strip()
        
        # Agregar extensión si no la tiene
        if not path.lower().endswith(extension.lower()):
            path += extension
        
        # Verificar que el directorio padre exista
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            raise ValidationError(f"El directorio no existe: {parent_dir}")
        
        return path

# ============================================================================
# PROCESADORES
# ============================================================================

class KMZProcessor:
    """Procesador principal para archivos KMZ."""
    
    def __init__(self):
        self.temp_dirs = []
    
    def __del__(self):
        """Limpia directorios temporales al destruir el objeto."""
        self.cleanup_temp_dirs()
    
    def cleanup_temp_dirs(self):
        """Limpia todos los directorios temporales creados."""
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Error limpiando directorio temporal: {e}")
        self.temp_dirs.clear()
    
    def extract_coordinates_to_excel(self, kmz_path: str, excel_path: str, 
                                   target_crs: str = DEFAULT_CRS["utm_chile"]) -> bool:
        """
        Extrae coordenadas de un KMZ y las exporta a Excel.
        
        Args:
            kmz_path: Ruta del archivo KMZ
            excel_path: Ruta de salida del Excel
            target_crs: CRS de destino para las coordenadas
            
        Returns:
            True si la operación fue exitosa
        """
        try:
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            
            # Extraer coordenadas
            coordinates = self._extract_coordinates_from_kmz(kmz_path, temp_dir)
            
            if not coordinates:
                raise ValidationError("No se encontraron coordenadas en el archivo KMZ")
            
            # Convertir a DataFrame
            data = []
            transformer = Transformer.from_crs(DEFAULT_CRS["geographic"], target_crs, always_xy=True)
            
            for name, description, lon, lat in coordinates:
                try:
                    # Convertir coordenadas
                    x, y = transformer.transform(lon, lat)
                    
                    data.append({
                        "Nombre del Punto": name,
                        "Descripción": description,
                        "Longitud": lon,
                        "Latitud": lat,
                        "Este": x,
                        "Norte": y
                    })
                except Exception as e:
                    logger.warning(f"Error convirtiendo coordenadas para {name}: {e}")
                    continue
            
            if not data:
                raise ValidationError("No se pudieron procesar las coordenadas")
            
            # Exportar a Excel
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            
            logger.info(f"Coordenadas exportadas a Excel: {excel_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error extrayendo coordenadas a Excel: {e}")
            raise
    
    def create_kmz_from_excel(self, excel_path: str, kmz_path: str,
                            name_col: str = "nombre", 
                            x_col: str = "este", 
                            y_col: str = "norte",
                            desc_col: str = "descripcion",
                            source_crs: str = DEFAULT_CRS["utm_chile"]) -> bool:
        """
        Crea un archivo KMZ desde datos de Excel.
        
        Args:
            excel_path: Ruta del archivo Excel
            kmz_path: Ruta de salida del KMZ
            name_col: Nombre de columna con nombres de puntos
            x_col: Nombre de columna con coordenada X/Este
            y_col: Nombre de columna con coordenada Y/Norte
            desc_col: Nombre de columna con descripción
            source_crs: CRS de origen de las coordenadas
            
        Returns:
            True si la operación fue exitosa
        """
        try:
            # Leer Excel
            df = pd.read_excel(excel_path)
            
            # Validar columnas requeridas
            required_cols = {name_col, x_col, y_col}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                raise ValidationError(f"Faltan columnas requeridas: {missing_cols}")
            
            # Agregar columna descripción si no existe
            if desc_col not in df.columns:
                df[desc_col] = ""
            
            # Crear GeoDataFrame
            geometry = [Point(row[x_col], row[y_col]) for _, row in df.iterrows()]
            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=source_crs)
            
            # Convertir a WGS84 para KML
            gdf = gdf.to_crs(DEFAULT_CRS["geographic"])
            
            # Asignar nombre para KML
            gdf["Name"] = gdf[name_col]
            gdf["Description"] = gdf[desc_col]
            
            # Crear KMZ
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            
            kml_path = os.path.join(temp_dir, "doc.kml")
            gdf.to_file(kml_path, driver="KML")
            
            create_kmz_from_kml(kml_path, kmz_path)
            
            logger.info(f"KMZ creado desde Excel: {kmz_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando KMZ desde Excel: {e}")
            raise
    
    def apply_buffer_to_kmz(self, input_kmz: str, output_kmz: str, 
                          buffer_distance: float, combine_buffers: bool = False) -> bool:
        """
        Aplica buffer a geometrías de un archivo KMZ.
        
        Args:
            input_kmz: Ruta del KMZ de entrada
            output_kmz: Ruta del KMZ de salida
            buffer_distance: Distancia del buffer en metros
            combine_buffers: Si combinar todos los buffers en uno
            
        Returns:
            True si la operación fue exitosa
        """
        try:
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            
            # Extraer y leer KML
            kml_path = extract_kmz_to_kml(input_kmz, temp_dir)
            gdf = gpd.read_file(kml_path, driver='KML')
            
            if gdf.empty:
                raise ValidationError("No se encontraron geometrías en el archivo KMZ")
            
            # Configurar CRS
            if gdf.crs is None:
                gdf = gdf.set_crs(DEFAULT_CRS["geographic"])
            
            original_crs = gdf.crs
            
            # Convertir a UTM si es necesario para buffer preciso
            if original_crs.is_geographic:
                utm_crs = gdf.estimate_utm_crs()
                gdf = gdf.to_crs(utm_crs)
            
            # Aplicar buffer
            if combine_buffers:
                # Combinar todas las geometrías y aplicar buffer
                combined_geom = unary_union(gdf.geometry.tolist())
                buffered_geom = combined_geom.buffer(buffer_distance)
                
                result = gpd.GeoDataFrame(
                    {"Name": [f"Buffer combinado ({buffer_distance}m)"],
                     "Description": [f"Buffer de {buffer_distance} metros aplicado a todas las geometrías"]},
                    geometry=[buffered_geom],
                    crs=gdf.crs
                )
            else:
                # Aplicar buffer individual
                gdf_buffered = gdf.copy()
                gdf_buffered.geometry = gdf.geometry.buffer(buffer_distance)
                gdf_buffered["Description"] = f"Buffer de {buffer_distance}m"
                
                # Combinar originales y buffers
                result = pd.concat([gdf, gdf_buffered], ignore_index=True)
                result = gpd.GeoDataFrame(result, crs=gdf.crs)
            
            # Convertir de vuelta al CRS original
            if original_crs.is_geographic:
                result = result.to_crs(original_crs)
            
            # Guardar como KML y crear KMZ
            output_kml = os.path.join(temp_dir, "buffered.kml")
            result.to_file(output_kml, driver="KML")
            
            create_kmz_from_kml(output_kml, output_kmz)
            
            logger.info(f"Buffer aplicado y KMZ creado: {output_kmz}")
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando buffer a KMZ: {e}")
            raise
    
    def _extract_coordinates_from_kmz(self, kmz_path: str, temp_dir: str) -> List[Tuple[str, str, float, float]]:
        """
        Extrae coordenadas de un archivo KMZ.
        
        Args:
            kmz_path: Ruta del archivo KMZ
            temp_dir: Directorio temporal
            
        Returns:
            Lista de tuplas (nombre, descripción, lon, lat)
        """
        try:
            # Extraer KML
            kml_path = extract_kmz_to_kml(kmz_path, temp_dir)
            
            # Parsear XML
            with open(kml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ET.ElementTree(ET.fromstring(content))
            root = tree.getroot()
            
            # Namespace KML
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            coordinates = []
            placemarks = root.findall('.//kml:Placemark', ns)
            
            for placemark in placemarks:
                # Obtener nombre
                name_elem = placemark.find('kml:name', ns)
                name = name_elem.text if name_elem is not None else "Sin Nombre"
                
                # Obtener descripción
                desc_elem = placemark.find('kml:description', ns)
                description = desc_elem.text if desc_elem is not None else ""
                
                # Buscar coordenadas en Point
                point_elem = placemark.find('.//kml:Point', ns)
                if point_elem is not None:
                    coords_elem = point_elem.find('kml:coordinates', ns)
                    if coords_elem is not None and coords_elem.text:
                        coord_text = coords_elem.text.strip()
                        parts = coord_text.split(',')
                        if len(parts) >= 2:
                            try:
                                lon = float(parts[0])
                                lat = float(parts[1])
                                coordinates.append((name, description, lon, lat))
                            except ValueError:
                                logger.warning(f"Coordenadas inválidas en {name}")
                                continue
            
            return coordinates
            
        except Exception as e:
            logger.error(f"Error extrayendo coordenadas de KMZ: {e}")
            raise

class GPXProcessor:
    """Procesador para archivos GPX."""
    
    def __init__(self):
        self.temp_dirs = []
    
    def __del__(self):
        """Limpia directorios temporales al destruir el objeto."""
        self.cleanup_temp_dirs()
    
    def cleanup_temp_dirs(self):
        """Limpia todos los directorios temporales creados."""
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Error limpiando directorio temporal: {e}")
        self.temp_dirs.clear()
    
    def convert_gpx_to_kmz(self, gpx_path: str, kmz_path: str = None) -> str:
        """
        Convierte un archivo GPX a KMZ.
        
        Args:
            gpx_path: Ruta del archivo GPX
            kmz_path: Ruta de salida del KMZ (opcional)
            
        Returns:
            Ruta del archivo KMZ creado
        """
        try:
            if not os.path.exists(gpx_path):
                raise ValidationError(f"El archivo GPX no existe: {gpx_path}")
            
            # Generar nombre de salida si no se proporciona
            if kmz_path is None:
                base_name = os.path.splitext(gpx_path)[0]
                kmz_path = f"{base_name}.kmz"
            
            # Parsear GPX
            with open(gpx_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            # Crear KML usando simplekml
            kml = simplekml.Kml()
            
            # Procesar tracks
            self._process_tracks(gpx, kml)
            
            # Procesar routes
            self._process_routes(gpx, kml)
            
            # Procesar waypoints
            self._process_waypoints(gpx, kml)
            
            # Guardar KML temporal
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            
            kml_path = os.path.join(temp_dir, "doc.kml")
            kml.save(kml_path)
            
            # Crear KMZ
            create_kmz_from_kml(kml_path, kmz_path)
            
            logger.info(f"GPX convertido a KMZ: {kmz_path}")
            return kmz_path
            
        except Exception as e:
            logger.error(f"Error convirtiendo GPX a KMZ: {e}")
            raise
    
    def _process_tracks(self, gpx, kml: simplekml.Kml) -> None:
        """
        Procesa tracks del GPX y los agrega al KML.
        
        Args:
            gpx: Objeto GPX parseado
            kml: Objeto KML de destino
        """
        for track_idx, track in enumerate(gpx.tracks):
            track_name = track.name or f"Track {track_idx + 1}"
            
            # Crear carpeta para el track si tiene múltiples segmentos
            if len(track.segments) > 1:
                track_folder = kml.newfolder(name=track_name)
            else:
                track_folder = kml
            
            for seg_idx, segment in enumerate(track.segments):
                if not segment.points:
                    continue
                
                # Nombre del segmento
                if len(track.segments) > 1:
                    seg_name = f"{track_name} - Segmento {seg_idx + 1}"
                else:
                    seg_name = track_name
                
                # Crear LineString
                linestring = track_folder.newlinestring(name=seg_name)
                
                # Agregar coordenadas
                coords = []
                for point in segment.points:
                    elevation = point.elevation if point.elevation is not None else 0
                    coords.append((point.longitude, point.latitude, elevation))
                
                linestring.coords = coords
                
                # Estilo de línea
                linestring.style.linestyle.color = simplekml.Color.red
                linestring.style.linestyle.width = 3
                
                # Descripción con información del track
                description_parts = []
                if track.description:
                    description_parts.append(f"Descripción: {track.description}")
                
                # Estadísticas del segmento
                if segment.points:
                    description_parts.append(f"Puntos: {len(segment.points)}")
                    
                    # Calcular distancia si es posible
                    try:
                        distance = segment.length_3d() or segment.length_2d()
                        if distance:
                            description_parts.append(f"Distancia: {distance/1000:.2f} km")
                    except:
                        pass
                
                if description_parts:
                    linestring.description = "\n".join(description_parts)
    
    def _process_routes(self, gpx, kml: simplekml.Kml) -> None:
        """
        Procesa routes del GPX y los agrega al KML.
        
        Args:
            gpx: Objeto GPX parseado
            kml: Objeto KML de destino
        """
        for route_idx, route in enumerate(gpx.routes):
            if not route.points:
                continue
            
            route_name = route.name or f"Ruta {route_idx + 1}"
            
            # Crear LineString para la ruta
            linestring = kml.newlinestring(name=route_name)
            
            # Agregar coordenadas
            coords = []
            for point in route.points:
                elevation = point.elevation if point.elevation is not None else 0
                coords.append((point.longitude, point.latitude, elevation))
            
            linestring.coords = coords
            
            # Estilo de línea (diferente color para rutas)
            linestring.style.linestyle.color = simplekml.Color.blue
            linestring.style.linestyle.width = 3
            
            # Descripción
            description_parts = []
            if route.description:
                description_parts.append(f"Descripción: {route.description}")
            
            description_parts.append(f"Puntos: {len(route.points)}")
            
            # Calcular distancia
            try:
                distance = route.length_3d() or route.length_2d()
                if distance:
                    description_parts.append(f"Distancia: {distance/1000:.2f} km")
            except:
                pass
            
            if description_parts:
                linestring.description = "\n".join(description_parts)
    
    def _process_waypoints(self, gpx, kml: simplekml.Kml) -> None:
        """
        Procesa waypoints del GPX y los agrega al KML.
        
        Args:
            gpx: Objeto GPX parseado
            kml: Objeto KML de destino
        """
        if not gpx.waypoints:
            return
        
        # Crear carpeta para waypoints si hay muchos
        if len(gpx.waypoints) > 5:
            waypoint_folder = kml.newfolder(name="Waypoints")
        else:
            waypoint_folder = kml
        
        for wp_idx, waypoint in enumerate(gpx.waypoints):
            wp_name = waypoint.name or f"Waypoint {wp_idx + 1}"
            
            # Crear punto
            point = waypoint_folder.newpoint(name=wp_name)
            
            elevation = waypoint.elevation if waypoint.elevation is not None else 0
            point.coords = [(waypoint.longitude, waypoint.latitude, elevation)]
            
            # Descripción
            description_parts = []
            if waypoint.description:
                description_parts.append(f"Descripción: {waypoint.description}")
            
            if waypoint.comment:
                description_parts.append(f"Comentario: {waypoint.comment}")
            
            if waypoint.elevation is not None:
                description_parts.append(f"Elevación: {waypoint.elevation:.1f} m")
            
            if waypoint.time:
                description_parts.append(f"Tiempo: {waypoint.time}")
            
            if description_parts:
                point.description = "\n".join(description_parts)
            
            # Estilo del punto
            point.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png"
            point.style.iconstyle.scale = 1.2
    
    def get_gpx_info(self, gpx_path: str) -> Dict[str, Any]:
        """
        Obtiene información básica de un archivo GPX.
        
        Args:
            gpx_path: Ruta del archivo GPX
            
        Returns:
            Diccionario con información del GPX
        """
        try:
            with open(gpx_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            info = {
                "tracks": len(gpx.tracks),
                "routes": len(gpx.routes),
                "waypoints": len(gpx.waypoints),
                "total_points": 0,
                "total_distance": 0.0,
                "bounds": None
            }
            
            # Contar puntos y calcular distancia total
            for track in gpx.tracks:
                for segment in track.segments:
                    info["total_points"] += len(segment.points)
                    try:
                        distance = segment.length_3d() or segment.length_2d()
                        if distance:
                            info["total_distance"] += distance
                    except:
                        pass
            
            for route in gpx.routes:
                info["total_points"] += len(route.points)
                try:
                    distance = route.length_3d() or route.length_2d()
                    if distance:
                        info["total_distance"] += distance
                except:
                    pass
            
            # Obtener bounds
            bounds = gpx.get_bounds()
            if bounds:
                info["bounds"] = {
                    "min_lat": bounds.min_latitude,
                    "max_lat": bounds.max_latitude,
                    "min_lon": bounds.min_longitude,
                    "max_lon": bounds.max_longitude
                }
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo información de GPX: {e}")
            return {"error": str(e)}

# ============================================================================
# INTERFAZ DE USUARIO
# ============================================================================

class BaseWindow:
    """Clase base para todas las ventanas de la aplicación."""
    
    def __init__(self, title: str, width: int = 800, height: int = 600, 
                 resizable: bool = True, parent: Optional[tk.Tk] = None):
        """
        Inicializa la ventana base.
        
        Args:
            title: Título de la ventana
            width: Ancho inicial
            height: Alto inicial
            resizable: Si la ventana es redimensionable
            parent: Ventana padre (opcional)
        """
        self.parent = parent
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title(title)
        self.root.configure(bg=UI_COLORS["bg_primary"])
        self.root.resizable(resizable, resizable)
        
        # Configurar tamaño y posición
        self._center_window(width, height)
        
        # Variables de estado
        self.is_processing = False
        self.status_var = tk.StringVar()
        
        # Configurar estilo
        self._setup_styles()
        
        # Crear frame principal
        self.main_frame = tk.Frame(self.root, bg=UI_COLORS["bg_primary"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Callback para cerrar ventana
        self.on_close_callback: Optional[Callable] = None
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_window(self, width: int, height: int):
        """Centra la ventana en la pantalla."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _setup_styles(self):
        """Configura estilos personalizados."""
        self.style = ttk.Style()
        
        # Configurar tema
        self.style.theme_use('clam')
        
        # Estilo para botones principales
        self.style.configure(
            "Primary.TButton",
            background=UI_COLORS["accent_primary"],
            foreground="white",
            font=UI_FONTS["button"],
            padding=(15, 8)
        )
        
        self.style.map(
            "Primary.TButton",
            background=[('active', UI_COLORS["accent_hover"]),
                       ('pressed', UI_COLORS["accent_dark"])]
        )
        
        # Estilo para botones secundarios
        self.style.configure(
            "Secondary.TButton",
            background=UI_COLORS["text_secondary"],
            foreground="white",
            font=UI_FONTS["body"],
            padding=(10, 6)
        )
    
    def create_title(self, text: str, row: int = 0) -> tk.Label:
        """
        Crea un título principal.
        
        Args:
            text: Texto del título
            row: Fila donde colocar el título
            
        Returns:
            Widget Label creado
        """
        title_label = tk.Label(
            self.main_frame,
            text=text,
            font=UI_FONTS["title"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_primary"]
        )
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20), sticky="ew")
        return title_label
    
    def create_file_selector(self, label_text: str, row: int, 
                           file_types: list, command: Callable,
                           variable: tk.StringVar) -> tuple:
        """
        Crea un selector de archivos con etiqueta, entrada y botón.
        
        Args:
            label_text: Texto de la etiqueta
            row: Fila donde colocar el selector
            file_types: Tipos de archivo para el diálogo
            command: Comando para el botón examinar
            variable: Variable para el campo de entrada
            
        Returns:
            Tupla (label, entry, button)
        """
        # Etiqueta
        label = tk.Label(
            self.main_frame,
            text=label_text,
            font=UI_FONTS["body"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_primary"]
        )
        label.grid(row=row, column=0, sticky="w", pady=5)
        
        # Campo de entrada
        entry = tk.Entry(
            self.main_frame,
            textvariable=variable,
            font=UI_FONTS["body"],
            width=50,
            bg="white",
            fg=UI_COLORS["text_primary"],
            relief="solid",
            bd=1
        )
        entry.grid(row=row, column=1, padx=(10, 5), pady=5, sticky="ew")
        
        # Botón examinar
        button = tk.Button(
            self.main_frame,
            text="Examinar",
            command=command,
            bg=UI_COLORS["accent_primary"],
            fg="white",
            font=UI_FONTS["body"],
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        button.grid(row=row, column=2, padx=5, pady=5)
        
        # Efectos hover
        self._add_hover_effects(button)
        
        return label, entry, button
    
    def create_action_button(self, text: str, command: Callable, 
                           row: int, column: int = 1, 
                           style: str = "primary") -> tk.Button:
        """
        Crea un botón de acción.
        
        Args:
            text: Texto del botón
            command: Comando a ejecutar
            row: Fila donde colocar el botón
            column: Columna donde colocar el botón
            style: Estilo del botón ('primary' o 'secondary')
            
        Returns:
            Widget Button creado
        """
        if style == "primary":
            bg_color = UI_COLORS["accent_primary"]
            hover_color = UI_COLORS["accent_hover"]
            font = UI_FONTS["button"]
        else:
            bg_color = UI_COLORS["text_secondary"]
            hover_color = UI_COLORS["text_primary"]
            font = UI_FONTS["body"]
        
        button = tk.Button(
            self.main_frame,
            text=text,
            command=command,
            bg=bg_color,
            fg="white",
            font=font,
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        button.grid(row=row, column=column, pady=15, padx=5)
        
        # Efectos hover
        self._add_hover_effects(button, hover_color)
        
        return button
    
    def create_status_label(self, row: int) -> tk.Label:
        """
        Crea una etiqueta de estado.
        
        Args:
            row: Fila donde colocar la etiqueta
            
        Returns:
            Widget Label creado
        """
        status_label = tk.Label(
            self.main_frame,
            textvariable=self.status_var,
            font=UI_FONTS["body"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_secondary"],
            wraplength=600
        )
        status_label.grid(row=row, column=0, columnspan=3, pady=10)
        return status_label
    
    def _add_hover_effects(self, button: tk.Button, hover_color: str = None):
        """Agrega efectos hover a un botón."""
        if hover_color is None:
            hover_color = UI_COLORS["accent_hover"]
        
        original_color = button.cget("background")
        
        def on_enter(e):
            button.configure(background=hover_color)
        
        def on_leave(e):
            button.configure(background=original_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def show_success(self, message: str):
        """Muestra mensaje de éxito."""
        self.status_var.set(message)
        self.root.after(100, lambda: self._update_status_color(UI_COLORS["success"]))
        messagebox.showinfo("Éxito", message)
    
    def show_error(self, message: str):
        """Muestra mensaje de error."""
        self.status_var.set(f"Error: {message}")
        self.root.after(100, lambda: self._update_status_color(UI_COLORS["error"]))
        messagebox.showerror("Error", message)
    
    def show_warning(self, message: str):
        """Muestra mensaje de advertencia."""
        self.status_var.set(f"Advertencia: {message}")
        self.root.after(100, lambda: self._update_status_color(UI_COLORS["warning"]))
        messagebox.showwarning("Advertencia", message)
    
    def set_processing(self, is_processing: bool, message: str = ""):
        """
        Establece el estado de procesamiento.
        
        Args:
            is_processing: Si está procesando
            message: Mensaje a mostrar
        """
        self.is_processing = is_processing
        
        if is_processing:
            self.status_var.set(f"Procesando... {message}")
            self._update_status_color(UI_COLORS["accent_primary"])
            self.root.configure(cursor="wait")
        else:
            self.root.configure(cursor="")
            if not message:
                self.status_var.set("")
    
    def _update_status_color(self, color: str):
        """Actualiza el color del texto de estado."""
        try:
            for widget in self.main_frame.winfo_children():
                if isinstance(widget, tk.Label) and widget.cget("textvariable") == str(self.status_var):
                    widget.configure(fg=color)
                    break
        except:
            pass
    
    def configure_grid_weights(self):
        """Configura los pesos del grid para redimensionamiento."""
        self.main_frame.grid_columnconfigure(1, weight=1)
    
    def show(self):
        """Muestra la ventana."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def close(self):
        """Cierra la ventana."""
        if self.on_close_callback:
            self.on_close_callback()
        self.root.destroy()
    
    def _on_close(self):
        """Maneja el evento de cierre de ventana."""
        self.close()

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
        height = 650  # Aumentado para acomodar la nueva información
        
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
        
        # Información de versión y desarrollador (NUEVO)
        version_label = tk.Label(
            info_frame,
            text="Versión: 2.1.2",
            font=UI_FONTS["small"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_secondary"]
        )
        version_label.pack()
        
        developer_label = tk.Label(
            info_frame,
            text="Desarrollado por Nicolás Sanhueza mediante uso de Inteligencia Artificial",
            font=UI_FONTS["small"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_secondary"]
        )
        developer_label.pack(pady=(5, 0))
    
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

# ============================================================================
# PÁGINAS DE FUNCIONALIDADES
# ============================================================================

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
                text=f"Mostrando primeras 50 filas de {len(df)} total",
                font=("Helvetica", 10),
                bg="white"
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
            logger.error(f"Error iniciando creación KMZ: {e}")
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
                self.name_col.get(),
                self.x_col.get(),
                self.y_col.get(),
                self.desc_col.get(),
                source_crs
            )
            
            if success:
                message = f"Archivo KMZ creado exitosamente:\n{output_path}"
                self.root.after(0, lambda: self.show_success(message))
            else:
                self.root.after(0, lambda: self.show_error("Error durante la creación del KMZ"))
                
        except Exception as e:
            logger.error(f"Error en creación KMZ: {e}")
            self.root.after(0, lambda: self.show_error(f"Error durante la creación: {e}"))
        finally:
            self.root.after(0, lambda: self.set_processing(False))
    
    def _return_to_menu(self):
        """Regresa al menú principal."""
        self.close()

class GPXConverterPage(BaseWindow):
    """Página para convertir GPX a KMZ."""
    
    def __init__(self, parent=None):
        super().__init__("Convertir GPX → KMZ", 800, 500, True, parent)
        
        self.processor = GPXProcessor()
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        self._create_interface()
        self.configure_grid_weights()
    
    def _create_interface(self):
        """Crea la interfaz de la página."""
        
        # Título
        self.create_title("Convertir GPX a KMZ")
        
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
        
        # Botones de acción
        button_frame = tk.Frame(self.main_frame, bg=self.root.cget("bg"))
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.create_action_button(
            "Convertir a KMZ",
            self._convert_gpx,
            4, 1, "primary"
        )
        
        self.create_action_button(
            "Información GPX",
            self._show_gpx_info,
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
        info_text = """
Información:
• El archivo GPX puede contener tracks, rutas y waypoints
• Los tracks se convierten en líneas rojas
• Las rutas se convierten en líneas azules  
• Los waypoints se convierten en puntos amarillos
• Se preserva toda la información de elevación y descripción
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
        """Abre diálogo para seleccionar archivo GPX de entrada."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo GPX",
            filetypes=[("Archivos GPX", "*.gpx"), ("Todos los archivos", "*.*")]
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
    
    def _show_gpx_info(self):
        """Muestra información del archivo GPX."""
        try:
            InputValidator.validate_file_path_input(self.input_file.get(), "gpx")
            
            info = self.processor.get_gpx_info(self.input_file.get())
            
            if "error" in info:
                self.show_error(f"Error leyendo GPX: {info['error']}")
                return
            
            # Crear ventana de información
            info_window = tk.Toplevel(self.root)
            info_window.title("Información del archivo GPX")
            info_window.geometry("400x300")
            info_window.configure(bg="white")
            
            # Información del GPX
            info_text = f"""
Información del archivo GPX:

Tracks: {info['tracks']}
Rutas: {info['routes']}
Waypoints: {info['waypoints']}
Total de puntos: {info['total_points']}
Distancia total: {info['total_distance']/1000:.2f} km

"""
            
            if info['bounds']:
                bounds = info['bounds']
                info_text += f"""Límites geográficos:
Norte: {bounds['max_lat']:.6f}°
Sur: {bounds['min_lat']:.6f}°
Este: {bounds['max_lon']:.6f}°
Oeste: {bounds['min_lon']:.6f}°
"""
            
            info_label = tk.Label(
                info_window,
                text=info_text,
                font=("Helvetica", 11),
                bg="white",
                justify=tk.LEFT
            )
            info_label.pack(padx=20, pady=20)
            
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            logger.error(f"Error obteniendo información GPX: {e}")
            self.show_error(f"Error obteniendo información: {e}")
    
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
            logger.error(f"Error iniciando conversión GPX: {e}")
            self.show_error(f"Error inesperado: {e}")
    
    def _convert_gpx_thread(self, input_path: str, output_path: str):
        """Ejecuta la conversión en un hilo separado."""
        try:
            self.root.after(0, lambda: self.set_processing(True, "Convirtiendo GPX a KMZ..."))
            
            # Procesar archivo
            result_path = self.processor.convert_gpx_to_kmz(input_path, output_path)
            
            if result_path:
                message = f"Archivo convertido exitosamente a:\n{result_path}"
                self.root.after(0, lambda: self.show_success(message))
            else:
                self.root.after(0, lambda: self.show_error("Error durante la conversión"))
                
        except Exception as e:
            logger.error(f"Error en conversión GPX: {e}")
            self.root.after(0, lambda: self.show_error(f"Error durante la conversión: {e}"))
        finally:
            self.root.after(0, lambda: self.set_processing(False))
    
    def _return_to_menu(self):
        """Regresa al menú principal."""
        self.close()

class BufferGeneratorPage(BaseWindow):
    """Página para generar buffers en archivos KMZ."""
    
    def __init__(self, parent=None):
        super().__init__("Generar Buffers KMZ", 800, 550, True, parent)
        
        self.processor = KMZProcessor()
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.buffer_distance = tk.StringVar(value="100")
        
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
        
        # Botones de acción
        button_frame = tk.Frame(self.main_frame, bg=self.root.cget("bg"))
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        self.create_action_button(
            "Generar Buffer",
            self._generate_buffer,
            5, 1, "primary"
        )
        
        self.create_action_button(
            "Volver al Menú",
            self._return_to_menu,
            5, 2, "secondary"
        )
        
        # Etiqueta de estado
        self.create_status_label(6)
        
        # Información adicional
        info_text = """
Información:
• El buffer se aplica a todas las geometrías del archivo KMZ
• La distancia se especifica en metros
• Puede elegir combinar todos los buffers en una sola geometría
• El resultado mantiene las geometrías originales más los buffers generados
        """
        
        info_label = tk.Label(
            self.main_frame,
            text=info_text,
            font=("Helvetica", 10),
            bg=self.root.cget("bg"),
            fg="#666666",
            justify=tk.LEFT
        )
        info_label.grid(row=7, column=0, columnspan=3, pady=(20, 0), sticky="w")
    
    def _create_buffer_config_frame(self):
        """Crea el frame de configuración de buffer."""
        config_frame = tk.LabelFrame(
            self.main_frame,
            text="Configuración de Buffer",
            font=("Helvetica", 12, "bold"),
            bg=self.root.cget("bg"),
            fg="#E4610F",
            padx=15,
            pady=15
        )
        config_frame.grid(row=3, column=0, columnspan=3, pady=15, sticky="ew", padx=20)
        
        # Distancia del buffer
        distance_frame = tk.Frame(config_frame, bg=self.root.cget("bg"))
        distance_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            distance_frame,
            text="Distancia del buffer (metros):",
            font=("Helvetica", 11),
            bg=self.root.cget("bg")
        ).pack(side=tk.LEFT)
        
        distance_entry = tk.Entry(
            distance_frame,
            textvariable=self.buffer_distance,
            font=("Helvetica", 11),
            width=10,
            bg="white"
        )
        distance_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botones de distancia predefinida
        preset_frame = tk.Frame(config_frame, bg=self.root.cget("bg"))
        preset_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            preset_frame,
            text="Distancias predefinidas:",
            font=("Helvetica", 10),
            bg=self.root.cget("bg")
        ).pack(side=tk.LEFT)
        
        preset_distances = [50, 100, 200, 500, 1000]
        for distance in preset_distances:
            btn = tk.Button(
                preset_frame,
                text=f"{distance}m",
                command=lambda d=distance: self.buffer_distance.set(str(d)),
                bg=UI_COLORS["bg_secondary"],
                fg=UI_COLORS["text_primary"],
                font=("Helvetica", 9),
                relief="solid",
                bd=1,
                padx=8,
                pady=2
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Opción de combinar buffers
        self.combine_buffers = tk.BooleanVar(value=False)
        combine_cb = tk.Checkbutton(
            config_frame,
            text="Combinar todos los buffers en una sola geometría",
            variable=self.combine_buffers,
            font=("Helvetica", 10),
            bg=self.root.cget("bg")
        )
        combine_cb.pack(pady=10)
    
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
        """Abre diálogo para seleccionar ubicación de archivo KMZ."""
        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo KMZ como",
            defaultextension=".kmz",
            filetypes=[("Archivos KMZ", "*.kmz"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.output_file.set(file_path)
    
    def _generate_buffer(self):
        """Genera el buffer para el archivo KMZ."""
        if self.is_processing:
            return
        
        try:
            # Validar entradas
            InputValidator.validate_file_path_input(self.input_file.get(), "kmz")
            output_path = InputValidator.validate_output_path(self.output_file.get(), ".kmz")
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
            self.root.after(0, lambda: self.set_processing(True, "Generando buffer..."))
            
            # Procesar archivo
            success = self.processor.apply_buffer_to_kmz(
                input_path,
                output_path,
                distance,
                self.combine_buffers.get()
            )
            
            if success:
                message = f"Buffer generado exitosamente:\n{output_path}"
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

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

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
            error_msg = f"Dependencia faltante: {e}\n\nPor favor instale las dependencias requeridas:\npip install geopandas shapely pyproj gpxpy pandas openpyxl simplekml"
            messagebox.showerror("Error de Dependencias", error_msg)
            logger.error(f"Dependencia faltante: {e}")
            return
        
        root.destroy()  # Destruir ventana temporal
        
        # Iniciar aplicación principal
        logger.info("Iniciando aplicación SIG unificada v2.1.2")
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
