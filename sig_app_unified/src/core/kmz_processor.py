
"""
Procesador para archivos KMZ - extracción y generación.
"""

import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict, Any
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer

from src.core.config import logger, DEFAULT_CRS
from src.core.utils import extract_kmz_to_kml, create_kmz_from_kml, convert_coordinates
from src.core.validators import ValidationError

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
                from shapely.ops import unary_union
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
