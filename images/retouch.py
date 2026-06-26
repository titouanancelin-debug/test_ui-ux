"""
Retouche des photos physalis pour le hero parallax.
Pose tes 5 photos brutes dans /home/user/test_ui-ux/images/raw/
puis lance :  python3 images/retouch.py

Sortie : images/p1.jpg … p5.jpg  (prêts pour le site)
"""

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import os, pathlib

RAW_DIR = pathlib.Path(__file__).parent / "raw"
OUT_DIR = pathlib.Path(__file__).parent

# Palette cible : terracotta #B84A2E  ambre #E4A03A  papier #F5EDE0
# On pousse les rouges/oranges chauds et on atténue les bleus/gris parasites
TERRA_R, TERRA_G, TERRA_B = 184, 74, 46

def warm_grade(img: Image.Image, strength: float = 0.18) -> Image.Image:
    """Ajoute une teinte chaude terracotta/ambre en soft-light."""
    import numpy as np
    arr = np.array(img, dtype=float)
    # Boost rouge, légère réduction bleu
    arr[:,:,0] = np.clip(arr[:,:,0] * (1 + strength * 0.6), 0, 255)
    arr[:,:,1] = np.clip(arr[:,:,1] * (1 + strength * 0.15), 0, 255)
    arr[:,:,2] = np.clip(arr[:,:,2] * (1 - strength * 0.35), 0, 255)
    return Image.fromarray(arr.astype("uint8"))

def retouch(src: pathlib.Path, dest: pathlib.Path, crop: tuple, is_main: bool = False):
    """
    src   : fichier source
    dest  : fichier de sortie
    crop  : (left%, top%, right%, bottom%) entre 0 et 1 — zone à garder
    """
    img = Image.open(src).convert("RGB")
    w, h = img.size

    # Recadrage
    l = int(crop[0] * w)
    t = int(crop[1] * h)
    r = int(crop[2] * w)
    b = int(crop[3] * h)
    img = img.crop((l, t, r, b))

    # Redimensionnement
    target = (1800, 1200) if is_main else (900, 1200)
    img = ImageOps.fit(img, target, Image.LANCZOS)

    # Contraste + luminosité
    img = ImageEnhance.Contrast(img).enhance(1.22)
    img = ImageEnhance.Brightness(img).enhance(0.96 if is_main else 1.02)

    # Saturation : on pousse un peu les couleurs
    img = ImageEnhance.Color(img).enhance(1.18)

    # Netteté douce
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3))

    # Grade chaud terracotta
    img = warm_grade(img, strength=0.14)

    img.save(dest, "JPEG", quality=88, optimize=True)
    print(f"  {src.name}  →  {dest.name}  ({target[0]}×{target[1]})")

def main():
    raws = sorted(RAW_DIR.glob("*"))
    raws = [f for f in raws if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    if not raws:
        print("❌  Aucune photo trouvée dans images/raw/")
        print("    Dépose tes 5 photos physalis dans ce dossier puis relance.")
        return

    print(f"📸  {len(raws)} photo(s) trouvée(s) dans raw/\n")

    # Règles de recadrage par position (ajuste si tu veux autre chose)
    configs = [
        # (crop_box,              is_main)
        ((0.0, 0.0, 1.0, 1.0),   True),   # p1 — image principale plein écran
        ((0.1, 0.0, 0.9, 1.0),   False),  # p2 — flottante gauche haute
        ((0.0, 0.1, 1.0, 0.95),  False),  # p3 — flottante droite
        ((0.05, 0.0, 0.95, 1.0), False),  # p4 — flottante gauche basse
        ((0.0, 0.05, 1.0, 1.0),  False),  # p5 — réserve / non utilisée pour l'instant
    ]

    for i, raw in enumerate(raws[:5]):
        crop, is_main = configs[i]
        dest = OUT_DIR / f"p{i+1}.jpg"
        retouch(raw, dest, crop, is_main)

    print("\n✅  Retouche terminée — fichiers dans images/")
    print("   Le site chargera automatiquement p1.jpg … p4.jpg")

if __name__ == "__main__":
    main()
