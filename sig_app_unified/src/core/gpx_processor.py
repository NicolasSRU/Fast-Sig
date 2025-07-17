
"""
Procesador para archivos GPX - conversión a KMZ.
"""

import os
import tempfile
from typing import List, Dict, Any
import gpxpy
import simplekml

from .config import logger
from .utils import create_kmz_from_kml
from .validators import ValidationError

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
