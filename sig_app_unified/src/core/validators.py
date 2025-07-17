
"""
Validadores para datos de entrada de la aplicación SIG.
"""

import re
from typing import List, Dict, Any, Optional
import pandas as pd
import geopandas as gpd
from .config import logger, SUPPORTED_FORMATS
from .utils import validate_file_exists, validate_coordinates

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
        import zipfile
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
            import gpxpy
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
        import os
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            raise ValidationError(f"El directorio no existe: {parent_dir}")
        
        return path
