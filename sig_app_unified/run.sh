
#!/bin/bash

# Script para ejecutar la aplicación SIG unificada

echo "=== Aplicación SIG Unificada ==="
echo "Iniciando aplicación..."

# Verificar que estamos en el directorio correcto
if [ ! -f "src/app.py" ]; then
    echo "Error: No se encuentra src/app.py"
    echo "Ejecute este script desde el directorio raíz del proyecto"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado"
    exit 1
fi

# Verificar dependencias críticas
echo "Verificando dependencias..."
python3 -c "
import sys
try:
    import geopandas, shapely, pyproj, gpxpy, pandas, openpyxl
    print('✓ Todas las dependencias están instaladas')
except ImportError as e:
    print(f'✗ Dependencia faltante: {e}')
    print('Ejecute: pip install -r requirements.txt')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Crear directorios necesarios
mkdir -p data temp logs

# Ejecutar aplicación
echo "Ejecutando aplicación SIG..."
python3 -m src.app

echo "Aplicación finalizada."
