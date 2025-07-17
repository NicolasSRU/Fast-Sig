
"""
Utilidades compartidas para la aplicación SIG.
Funciones comunes para validación, conversión y manejo de archivos.
"""

import os
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List
import geopandas as gpd
from pyproj import Transformer, CRS
from shapely.geometry import Point
from .config import logger, DEFAULT_CRS, SUPPORTED_FORMATS

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
