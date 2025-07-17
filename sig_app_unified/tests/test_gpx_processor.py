
"""
Tests para el procesador de archivos GPX.
"""

import pytest
import tempfile
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.gpx_processor import GPXProcessor

class TestGPXProcessor:
    """Tests para GPXProcessor."""
    
    def setup_method(self):
        """Configuración para cada test."""
        self.processor = GPXProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Limpieza después de cada test."""
        self.processor.cleanup_temp_dirs()
    
    def test_processor_initialization(self):
        """Test de inicialización del procesador."""
        assert self.processor is not None
        assert hasattr(self.processor, 'temp_dirs')
        assert isinstance(self.processor.temp_dirs, list)
    
    def test_convert_gpx_to_kmz_method_exists(self):
        """Test que el método de conversión existe."""
        assert hasattr(self.processor, 'convert_gpx_to_kmz')
        assert callable(self.processor.convert_gpx_to_kmz)
    
    def test_get_gpx_info_method_exists(self):
        """Test que el método de información existe."""
        assert hasattr(self.processor, 'get_gpx_info')
        assert callable(self.processor.get_gpx_info)
    
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
