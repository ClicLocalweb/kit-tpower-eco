# Kit hidráulico T-Power ECO: concepto 3D

Landing de scroll donde el kit hidráulico se desarma pieza por pieza a medida que bajás, más el modelo 3D y la animación de vista explotada.

**Concepto no oficial.** No es la página del fabricante ni usa su logo. Las medidas del modelo son estimadas y las piezas internas de la bomba y de la válvula son genéricas. El detalle está en `docs/`.

## Qué hay acá

| Carpeta o archivo | Contenido |
|---|---|
| `index.html`, `frames/` y `zoom/` | La landing. Un solo archivo HTML, sin librerías, con 144 cuadros WebP para escritorio, 144 para celular y 6 primeros planos de bomba, válvula y joystick |
| `modelo/` | Scripts de Blender (Python) que generan las 69 piezas, los archivos `.blend` y la lista `piezas.csv`. `kit_build_v2.py` es la versión nueva, con válvula y joystick según el catálogo, usada en los primeros planos |
| `animacion/` | Video de 12 segundos (1920×1080, 24 fps) y su control de calidad |
| `capturas/` | Capturas de la landing en escritorio y celular |
| `docs/` | Tabla de medidas e informe final: lo real, lo estimado y lo que no se pudo verificar |

## Cómo verla

Abrí `index.html` desde un servidor web, con las carpetas `frames` y `zoom` al lado. Por ejemplo:

```
python3 -m http.server 8000
```

y entrá a `http://localhost:8000`.

Para publicarla gratis con GitHub Pages: Settings, Pages, rama `main`, carpeta raíz.

## Cómo se hizo

Blender 5.2 manejado por Python, render con Cycles, FFmpeg para el video y el control de calidad, y HTML, CSS y JavaScript sin librerías para la página.
