# Informe final: kit hidráulico T-Power ECO (concepto no oficial)

Fecha: 14/11/2026. Trabajo hecho de 11:26 a 15:15 (hora de Córdoba).

## Qué se entrega

| Entregable | Dónde está | Estado |
|---|---|---|
| Modelo 3D con 69 piezas | `02_modelo/kit_hidraulico.blend` y `kit_hidraulico_animado.blend` | Terminado |
| Lista de piezas (nombre, grupo, orden, vector de explosión) | `02_modelo/piezas.csv` | Terminado |
| Animación de vista explotada, 12 s, 1920×1080, 24 fps, con clic | `04_animacion/kit_tpower_eco_vista_explotada.mp4` | Terminado y controlado |
| Landing de scroll | `05_landing/index.html` más carpeta `frames` (o el zip) | Terminada y probada |
| Capturas de la landing (3 puntos, escritorio y celular) | `05_landing/capturas/` | Terminado |
| Tabla de medidas | `01_ficha/tabla_de_medidas.md` | Terminado |
| Registro con hora por etapa | `registro.log` | Terminado |
| Imágenes para making of | `06_making_of/` | Terminado |

## Lo real

Sale de la página oficial del producto (hidromasbrasil.com) y del catálogo Hidromas 2025:

- Depósito de 200 litros totales.
- Volumen de trabajo de 145 y 180 litros.
- Presión de trabajo de 190 bar.
- De tus fotos: forma general, bandas del depósito, boca de carga con tapa, dos visores en la tapa, válvula montada arriba sobre el cabezal del filtro, apoyos con tacos de goma, mangueras y rollo de tubo neumático.
- De tu aclaración: la bomba va debajo del depósito, sujeta a la toma de fuerza.

## Corrección posterior

El 14/11 retiré de este informe y de la tabla de medidas la frase "la válvula de fin de carrera no viene en el kit": no figura en el catálogo 2025 y no se pudo confirmar. También corregí el peso de 2,75 kg, que es de la válvula de fin de carrera hidráulica y no de la direccional.

## Lo estimado

- Todas las medidas del modelo. El depósito quedó en Ø 460 × 1.260 mm, sacado de la proporción de tu foto (largo igual a 2,7 diámetros). Da unos 195 litros, cerca de los 200 oficiales.
- Espesores, bulones, tamaño de la bomba y de la válvula.
- La forma de los apoyos y de las placas al chasis: están simplificadas respecto del despiece numerado que mandaste.

## Lo genérico (no son piezas reales de Hidromas)

- Internos de la bomba: engranajes, eje estriado, bujes, retén.
- Internos de la válvula: corredera, resorte, o-rings, pistón neumático, cartucho limitador.
- Rompeolas interno, canasto de la boca de carga y tapón de drenaje.
- El soporte que cuelga la bomba del depósito: es una licencia del concepto, porque en el camión la sostiene la toma de fuerza, que no está modelada.

## Lo que no pude verificar

- Los dos PDF de ficha técnica de la página oficial: el sitio no deja ver sus enlaces sin un navegador real.
- El texto completo de la descripción oficial: la página lo corta en "Working Tank Volume: 145 and 180 liters (at...".
- Qué bomba y qué válvula del catálogo corresponden exactamente a este kit. Por eso en la landing no puse caudal ni cilindrada.
- La landing en un celular físico y en Safari. La probé en Chromium, en 1440×900 y simulando un iPhone 13.
- El sitio hidromas.com.tr no se pudo abrir.
- El video no lo vi reproducido en tiempo real: lo controlé cuadro por cuadro con FFmpeg y con una hoja de contacto.

## Control de calidad de la animación (FFmpeg)

- 288 cuadros, 12,000 s, 1920×1080, 24 fps, H.264. Audio AAC estéreo.
- Sin cuadros negros y sin saltos de brillo entre cuadros.
- El clic suena en el segundo 10,6, justo cuando cierra.
- Primer y último cuadro prácticamente iguales (SSIM 0,9998): se puede poner en bucle.
- Tramo quieto de 0,6 s mientras flota, que es intencional.

Detalle completo en `04_animacion/qa_animacion.txt`.

**Una falla encontrada y corregida:** en el primer render el depósito salió negro desde el cuadro 113. Lo detectó el control de calidad. La causa más probable es un error del motor de render en corridas largas. Rehíce esos 175 cuadros en tandas cortas y el control final dio bien.

## Pruebas de la landing

- Escritorio 1440×900: 59 cuadros por segundo en scroll continuo, 0 errores, 0 pedidos fallidos.
- Celular (iPhone 13 simulado): 60 cuadros por segundo, 0 errores.
- Peso: la página pesa 20 KB. Los 144 cuadros pesan 3,9 MB en escritorio y 3,4 MB en celular; cada equipo baja solo su juego.
- Carga progresiva: primero el cuadro inicial, después 1 de cada 16, de cada 8, de cada 4, de cada 2 y el resto.
- Marca: sin logo de Hidromas, con la leyenda "concepto no oficial" arriba y la línea al pie.

## Pendientes tuyos

1. **Número de WhatsApp.** Hoy tiene uno de ejemplo (5493510000000). Se cambia en una sola línea, al principio del script de `index.html`, donde dice `WHATSAPP_NUMERO`.
2. **Publicarla.** Para verla hay que abrir `index.html` con la carpeta `frames` al lado, o subir las dos cosas a un hosting.
3. Si más adelante querés más nivel de detalle en el modelo, lo más visible sería: apoyos iguales a tu despiece, conexiones y racores sueltos, y la toma de fuerza.

## Costo

- **Tiempo de máquina de render:** unas 3 horas y 10 minutos de CPU en total (100 min del primer render, 80 min de la repetición y unos 10 min de pruebas). Sin placa de video: 4 núcleos, entre 13 y 43 segundos por cuadro.
- **Tiempo total de reloj:** 3 h 50 min, incluida la espera de tu aprobación.
- **Dinero:** cero. Blender y FFmpeg son gratuitos y no se usó ningún servicio pago.
- **Consumo de tu plan:** no lo puedo ver desde acá. Fue un trabajo de consumo alto; el número exacto lo ves en tu panel de uso. La repetición del render gastó tiempo de máquina pero muy poco consumo, porque corrió sola.
- **Ahorro aplicado:** la landing reutiliza los cuadros de la animación (1 de cada 2), así que no hubo un segundo render de 150 cuadros.

## Herramientas

Blender 5.2.4 manejado por Python (bpy), motor Cycles en CPU, 80 muestras con reducción de ruido para la animación y 160 para los cuadros de prueba. FFmpeg para el video, el clic y el control de calidad. Página en HTML, CSS y JavaScript sin librerías.
