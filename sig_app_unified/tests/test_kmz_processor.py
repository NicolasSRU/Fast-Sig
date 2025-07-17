
"""
Tests para el procesador de archivos KMZ.
"""

import pytest
import tempfile
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.kmz_processor import KMZProcessor
from core.validators import ValidationError

class TestKMZProcessor:
    """Tests para KMZProcessor."""
    
    def setup_method(self):
        """Configuración para cada test."""
        self.processor = KMZProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Limpieza después de cada test."""
        self.processor.cleanup_temp_dirs()
    
    def test_processor_initialization(self):
        """Test de inicialización del procesador."""
        assert self.processor is not None
        assert hasattr(self.processor, 'temp_dirs')
        assert isinstance(self.processor.temp_dirs, list)
    
    def test_create_kmz_from_excel_basic(self):
        """Test básico de creación de KMZ desde Excel."""
        # Crear archivo Excel de prueba
        test_data = {
            'nombre': ['Punto 1', 'Punto 2', 'Punto 3'],
            'este': [300000, 301000, 302000],
            'norte': [7500000, 7501000, 7502000],
            'descripcion': ['Desc 1', 'Desc 2', 'Desc 3']
        }
        df = pd.DataFrame(test_data)
        
        excel_path = os.path.join(self.temp_dir, 'test_points.xlsx')
        df.to_excel(excel_path, index=False)
        
        kmz_path = os.path.join(self.temp_dir, 'test_output.kmz')
        
        # Ejecutar conversión
        result = self.processor.create_kmz_from_excel(
            excel_path, kmz_path,
            name_col='nombre',
            x_col='este',
            y_col='norte',
            desc_col='descripcion'
        )
        
        assert result is True
        assert os.path.exists(kmz_path)
    
    def test_create_kmz_missing_columns(self):
        """Test con columnas faltantes."""
        # Crear Excel sin columna requerida
        test_data = {
            'nombre': ['Punto 1'],
            'este': [300000]
            # Falta columna 'norte'
        }
        df = pd.DataFrame(test_data)
        
        excel_path = os.path.join(self.temp_dir, 'test_incomplete.xlsx')
        df.to_excel(excel_path, index=False)
        
        kmz_path = os.path.join(self.temp_dir, 'test_output.kmz')
        
        # Debe fallar por columna faltante
        with pytest.raises(ValidationError):
            self.processor.create_kmz_from_excel(excel_path, kmz_path)
    
    def test_apply_buffer_basic(self):
        """Test básico de aplicación de buffer."""
        # Este test requiere un archivo KMZ real
        # Por ahora solo verificamos que el método existe
        assert hasattr(self.processor, 'apply_buffer_to_kmz')
        assert callable(self.processor.apply_buffer_to_kmz)
    
    def test_cleanup_temp_dirs(self):
        """Test de limpieza de directorios temporales."""
        # Agregar directorio temporal
        temp_test_dir = tempfile.mkdtemp()
        self.processor.temp_dirs.append(temp_test_dir)
        
        # Verificar que existe
        assert os.path.exists(temp_test_dir)
        
        # Limpiar
        self.processor.cleanup_temp_dirs()
        
        # Verificar que se limpió
        assert not os.path.exists(temp_test_dir)
        assert len(self.processor.temp_dirs) == 0

if __name__ == "__main__":
    pytest.main([__file__])
