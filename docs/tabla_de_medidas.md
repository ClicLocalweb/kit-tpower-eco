# Kit hidráulico T-Power ECO: tabla de medidas

Fuentes consultadas el 14/11/2026:

- Página oficial del producto: hidromasbrasil.com/en, "Hydraulic oil tank kit T-Power ECO"
- Catálogo oficial Hidromas 2025 (PDF en cdn.hidromasglobal.com)

La ficha oficial publica muy pocos números. No da diámetro, largo, espesor ni peso, y los dos PDF de descarga de la página no se pudieron abrir. Todo lo marcado como ESTIMADO sale de las proporciones de tus fotos y de medidas habituales del rubro.

## Datos oficiales (REAL)

| Dato | Valor | Fuente |
|---|---|---|
| Volumen total del depósito | 200 litros | Página del producto |
| Volumen de trabajo | 145 y 180 litros | Página del producto (texto cortado) y catálogo (180 L) |
| Presión de trabajo del kit | 190 bar | Catálogo 2025 |
| Códigos de producto | HTC1802 y B0453C71180 | Página del producto (figuran los dos) |
| Uso | Kit para vuelco en semirremolque | Catálogo 2025 |

## Datos del catálogo sin confirmar para este kit (NO VERIFICADO)

La tabla del catálogo sale desordenada al leerla, así que no pude confirmar qué renglón corresponde al T-Power ECO.

| Dato | Valor | Nota |
|---|---|---|
| Válvula direccional | Modelo 3B de 140 L/min, rosca 1"-11 BSP, 190 bar, montaje sobre tanque, con mando por aire comprimido, válvula de alivio y retención | Código TM140010401; figura en la fila del kit T-Power ECO del catálogo 2025 (página 15). Antes decía 2,75 kg: ese peso es de la válvula de fin de carrera hidráulica, no de esta |
| Bomba de engranajes | 82 cm³/rev (ISO 7653 o SAE B); también hay de 105 cm³/rev | Códigos GP08242210000 y GP08222300000 |
| Filtro de aceite | 150 L/min | Elemento 88510152 |
| Filtro de aire de la boca de carga | Con sistema anti salpicadura | Código FCAF001 |

## Medidas usadas en el modelo 3D (ESTIMADO)

| Pieza | Medida usada | Cómo se estimó |
|---|---|---|
| Depósito, diámetro | 460 mm | Proporción de la foto (largo = 2,7 diámetros) y volumen de 200 L |
| Depósito, largo total | 1.260 mm | Parte cilíndrica de 1.060 mm más dos tapas bombeadas de 100 mm |
| Depósito, espesor de chapa | 3 mm | Habitual en el rubro |
| Volumen que da esa geometría | 195 litros aprox. | Cuenta de control: cerca de los 200 L oficiales |
| Cuello de carga | Ø 72 mm, 160 mm de alto | Proporción de la foto |
| Tapa con respiradero | Ø 110 mm | Proporción de la foto |
| Cabezal del filtro de retorno | Ø 144 mm, 72 mm de alto | Proporción de la foto |
| Elemento filtrante | Ø 80 mm, 190 mm de largo | Genérico |
| Cuerpo de la válvula | 168 × 100 × 92 mm | Proporción de la foto |
| Cuerpo de la bomba | 100 × 124 × 176 mm | Proporción de la foto |
| Engranajes de la bomba | 12 dientes, Ø 64 mm, 50 mm de ancho | Genérico |
| Travesaños de apoyo | Perfil U de 80 × 60 mm, 620 mm de largo | Proporción de la foto y del despiece |
| Tacos de goma | Ø 66 mm, 32 mm de alto | Proporción del despiece |
| Manguera de succión | Ø 42 mm exterior | Proporción de la foto |
| Manguera de presión | Ø 28 mm exterior | Proporción de la foto |
| Medida total del conjunto armado | 1.416 × 735 × 1.005 mm aprox. | Sale del modelo |

## Piezas internas: son genéricas

No hay despiece público de la bomba ni de la válvula. Los internos del modelo son genéricos y creíbles, no son las piezas reales de Hidromas:

- Bomba: par de engranajes rectos, eje estriado, dos bloques de bujes, retén, brida, tapa trasera y cuatro bulones pasantes.
- Válvula: corredera, resorte de centrado, o-rings, pistón del mando neumático y cartucho limitador de presión.
- Depósito: chapa rompeolas interna, canasto de la boca de carga y tapón de drenaje.

## Dos decisiones de concepto

- La bomba está colgada bajo el depósito para que el kit se vea como una sola unidad. En el camión la bomba va en la toma de fuerza.
- El depósito lleva el nombre "T-POWER ECO" en texto simple, sin el logo de Hidromas, y la leyenda "concepto".

La lista completa de las 69 piezas, con grupo, orden y vector de explosión, está en `02_modelo/piezas.csv`.

## Corrección del 14/11/2026

En una versión anterior esta tabla decía que la válvula de fin de carrera no viene en el kit. Ese dato no figura en el catálogo 2025 que subiste: venía del resumen de una lectura automática de la web y no se puede confirmar. Lo saqué. Si el kit la incluye o no, hay que preguntárselo a Hidromas.
