"""Convierte 1 de cada 2 cuadros de la animacion en WebP para la landing (escritorio 1600x900, celular 900x900)."""
import os, sys
from multiprocessing import Pool
from PIL import Image
SRC, OUT = sys.argv[1], sys.argv[2]
def one(i):
    f = i * 2
    p = f"{SRC}/f_{f:04d}.png"
    if not os.path.exists(p): p = f"{SRC}/../frames_malos/f_{f:04d}.png"
    im = Image.open(p).convert("RGB")
    im.resize((1600, 900), Image.LANCZOS).save(f"{OUT}/d/f_{i:03d}.webp", "WEBP", quality=74, method=6)
    im.crop((420, 0, 1500, 1080)).resize((900, 900), Image.LANCZOS).save(f"{OUT}/m/f_{i:03d}.webp", "WEBP", quality=70, method=6)
if __name__ == "__main__":
    os.makedirs(OUT + "/d", exist_ok=True); os.makedirs(OUT + "/m", exist_ok=True)
    with Pool(2) as p: p.map(one, range(144))
