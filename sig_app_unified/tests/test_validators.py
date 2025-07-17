
"""
Tests para los validadores de la aplicación.
"""

import pytest
import tempfile
import os
import pandas as pd

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.validators import FileValidator, DataValidator, InputValidator, ValidationError

class TestFileValidator:
    """Tests para FileValidator."""
    
    def setup_method(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
    
    def test_validate_excel_file_valid(self):
        """Test de validación de archivo Excel válido."""
        # Crear archivo Excel de prueba
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        excel_path = os.path.join(self.temp_dir, 'test.xlsx')
        df.to_excel(excel_path, index=False)
        
        # Debe pasar la validación
        result = FileValidator.validate_excel_file(excel_path)
        assert result is True
    
    def test_validate_excel_file_not_exists(self):
        """Test de validación con archivo inexistente."""
        non_existent_path = os.path.join(self.temp_dir, 'no_existe.xlsx')
        
        with pytest.raises(ValidationError):
            FileValidator.validate_excel_file(non_existent_path)
    
    def test_validate_excel_file_wrong_extension(self):
        """Test de validación con extensión incorrecta."""
        # Crear archivo con extensión incorrecta
        txt_path = os.path.join(self.temp_dir, 'test.txt')
        with open(txt_path, 'w') as f:
            f.write('test')
        
        with pytest.raises(ValidationError):
            FileValidator.validate_excel_file(txt_path)

class TestDataValidator:
    """Tests para DataValidator."""
    
    def test_validate_buffer_distance_valid(self):
        """Test de validación de distancia válida."""
        result = DataValidator.validate_buffer_distance("100")
        assert result == 100.0
        
        result = DataValidator.validate_buffer_distance("50.5")
        assert result == 50.5
    
    def test_validate_buffer_distance_invalid(self):
        """Test de validación de distancia inválida."""
        with pytest.raises(ValidationError):
            DataValidator.validate_buffer_distance("0")
        
        with pytest.raises(ValidationError):
            DataValidator.validate_buffer_distance("-10")
        
        with pytest.raises(ValidationError):
            DataValidator.validate_buffer_distance("abc")
        
        with pytest.raises(ValidationError):
            DataValidator.validate_buffer_distance("200000")  # Muy grande
    
    def test_validate_coordinates_data_valid(self):
        """Test de validación de datos de coordenadas válidos."""
        df = pd.DataFrame({
            'este': [300000, 301000, 302000],
            'norte': [7500000, 7501000, 7502000]
        })
        
        errors = DataValidator.validate_coordinates_data(df)
        assert len(errors) == 0
    
    def test_validate_coordinates_data_missing_columns(self):
        """Test de validación con columnas faltantes."""
        df = pd.DataFrame({
            'este': [300000, 301000, 302000]
            # Falta columna 'norte'
        })
        
        errors = DataValidator.validate_coordinates_data(df)
        assert len(errors) > 0
        assert any("norte" in error for error in errors)

class TestInputValidator:
    """Tests para InputValidator."""
    
    def setup_method(self):
        """Configuración para cada test."""
        self.temp_dir = tempfile.mkdtemp()
    
    def test_validate_output_path_adds_extension(self):
        """Test que agrega extensión si no la tiene."""
        path = os.path.join(self.temp_dir, 'output')
        result = InputValidator.validate_output_path(path, '.kmz')
        assert result.endswith('.kmz')
    
    def test_validate_output_path_keeps_extension(self):
        """Test que mantiene extensión existente."""
        path = os.path.join(self.temp_dir, 'output.kmz')
        result = InputValidator.validate_output_path(path, '.kmz')
        assert result == path
    
    def test_validate_output_path_empty(self):
        """Test con ruta vacía."""
        with pytest.raises(ValidationError):
            InputValidator.validate_output_path("", '.kmz')
        
        with pytest.raises(ValidationError):
            InputValidator.validate_output_path("   ", '.kmz')

if __name__ == "__main__":
    pytest.main([__file__])
