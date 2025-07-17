
# Aplicación SIG Unificada

Una aplicación de escritorio completa para el procesamiento de datos geoespaciales con interfaz moderna en tono naranja.

## Características

### Funcionalidades Principales
- **Extractor de Coordenadas KMZ → Excel**: Extrae coordenadas de archivos KMZ y las exporta a Excel
- **Creador KMZ Excel → KMZ**: Crea archivos KMZ desde datos de coordenadas en Excel
- **Conversor GPX → KMZ**: Convierte archivos GPX a formato KMZ
- **Generador de Buffers**: Aplica buffers a geometrías en archivos KMZ

### Características Técnicas
- Interfaz gráfica moderna con diseño en tono naranja
- Menú central interactivo
- Manejo robusto de errores
- Procesamiento en hilos separados (no bloquea la interfaz)
- Soporte para múltiples sistemas de coordenadas
- Validación completa de datos de entrada
- Logging detallado

## Instalación

### Requisitos del Sistema
- Python 3.8 o superior
- Sistema operativo: Windows, macOS, o Linux

### Instalación de Dependencias

1. Clonar o descargar el proyecto
2. Navegar al directorio del proyecto
3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

### Dependencias Principales
- `geopandas`: Procesamiento de datos geoespaciales
- `shapely`: Operaciones geométricas
- `pyproj`: Transformaciones de coordenadas
- `simplekml`: Creación de archivos KML
- `gpxpy`: Procesamiento de archivos GPX
- `pandas`: Manipulación de datos
- `openpyxl`: Lectura/escritura de archivos Excel

## Uso

### Ejecutar la Aplicación

```bash
python -m src.app
```

O desde el directorio src:

```bash
python app.py
```

### Funcionalidades

#### 1. Extraer Coordenadas (KMZ → Excel)
- Selecciona un archivo KMZ con puntos geográficos
- Elige el sistema de coordenadas de salida
- Exporta a Excel con columnas: Nombre, Descripción, Longitud, Latitud, Este, Norte

#### 2. Crear KMZ (Excel → KMZ)
- Selecciona archivo Excel con datos de coordenadas
- Configura nombres de columnas (nombre, este, norte, descripción)
- Especifica sistema de coordenadas de origen
- Genera archivo KMZ compatible con Google Earth

#### 3. Convertir GPX → KMZ
- Selecciona archivo GPX
- Analiza contenido (tracks, rutas, waypoints)
- Convierte a KMZ preservando toda la información

#### 4. Generar Buffers
- Selecciona archivo KMZ con geometrías
- Especifica distancia de buffer en metros
- Opción para combinar buffers en un solo polígono
- Genera nuevo KMZ con buffers aplicados

## Estructura del Proyecto

```
sig_app_unified/
├── src/
│   ├── core/                 # Lógica de negocio
│   │   ├── config.py        # Configuración global
│   │   ├── utils.py         # Utilidades compartidas
│   │   ├── validators.py    # Validadores de datos
│   │   ├── kmz_processor.py # Procesador de KMZ
│   │   └── gpx_processor.py # Procesador de GPX
│   ├── ui/                  # Interfaz de usuario
│   │   ├── base_window.py   # Ventana base
│   │   └── main_window.py   # Ventana principal
│   ├── pages/               # Páginas de funcionalidades
│   │   ├── kmz_extractor_page.py
│   │   ├── excel_to_kmz_page.py
│   │   ├── gpx_converter_page.py
│   │   └── buffer_generator_page.py
│   └── app.py              # Punto de entrada
├── tests/                  # Tests unitarios
├── data/                   # Archivos de datos
├── temp/                   # Archivos temporales
├── logs/                   # Archivos de log
├── requirements.txt        # Dependencias
└── README.md              # Este archivo
```

## Testing

Ejecutar tests unitarios:

```bash
pytest tests/
```

O test específico:

```bash
pytest tests/test_kmz_processor.py
```

## Archivos de Prueba

La aplicación incluye soporte para los archivos de prueba:
- `Puntos.kmz`: 15 puntos geográficos de fauna en Chile
- `Transectas.gpx`: 28 tracks/transectas para estudios de fauna

## Configuración

### Sistemas de Coordenadas Soportados
- **WGS84 (EPSG:4326)**: Coordenadas geográficas
- **UTM Zona 19S (EPSG:32719)**: Para Chile
- **Auto-detección**: Detecta automáticamente la zona UTM apropiada

### Personalización
- Colores y estilos: Modificar `src/core/config.py`
- Configuración de buffer: Ajustar rangos en `BUFFER_CONFIG`
- Logging: Configurar nivel y formato en `LOGGING_CONFIG`

## Solución de Problemas

### Errores Comunes

1. **Error de dependencias faltantes**
   - Solución: `pip install -r requirements.txt`

2. **Error al leer archivos KMZ**
   - Verificar que el archivo no esté corrupto
   - Asegurar que contiene archivos KML válidos

3. **Error de coordenadas fuera de rango**
   - Verificar sistema de coordenadas correcto
   - Validar que las coordenadas estén en el formato esperado

4. **Error de memoria con archivos grandes**
   - Procesar archivos en lotes más pequeños
   - Aumentar memoria disponible para Python

### Logs
Los logs se guardan en `logs/sig_app.log` con información detallada sobre:
- Operaciones realizadas
- Errores encontrados
- Advertencias del sistema

## Desarrollo

### Agregar Nueva Funcionalidad

1. Crear procesador en `src/core/`
2. Crear página en `src/pages/`
3. Agregar botón en `src/ui/main_window.py`
4. Crear tests en `tests/`

### Estilo de Código
- Seguir PEP 8
- Documentar funciones con docstrings
- Usar type hints cuando sea posible
- Manejar excepciones apropiadamente

## Licencia

Este proyecto está desarrollado para uso interno y educativo.

## Soporte

Para reportar problemas o solicitar funcionalidades:
1. Revisar logs en `logs/sig_app.log`
2. Verificar configuración en `src/core/config.py`
3. Ejecutar tests para identificar problemas

## Versión

**Versión 1.0** - Aplicación SIG unificada completa con todas las funcionalidades integradas.
