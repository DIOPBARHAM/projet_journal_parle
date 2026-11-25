"""Vérifie que l'environnement du projet Journal parlé est correctement installé.

Lancer avec : python scripts/check_setup.py
"""

import importlib
import shutil
import subprocess
import sys
from importlib import metadata

# (nom du module à importer, nom du paquet pip pour lire sa version)
BIBLIOTHEQUES = [
    ("fitz", "pymupdf"),
    ("edge_tts", "edge-tts"),
    ("pydub", "pydub"),
    ("faster_whisper", "faster-whisper"),
    ("jiwer", "jiwer"),
    ("gradio", "gradio"),
    ("num2words", "num2words"),
    ("pytest", "pytest"),
]


def verifier_python() -> bool:
    """Affiche la version de Python et indique si elle est dans la plage conseillée."""
    version = sys.version_info
    texte = f"{version.major}.{version.minor}.{version.micro}"
    if (3, 10) <= (version.major, version.minor) <= (3, 12):
        print(f"[OK]  Python {texte}")
        return True
    print(f"[ATTENTION] Python {texte} : la plage conseillée est 3.10 à 3.12")
    return False


def verifier_bibliotheque(module: str, paquet: str) -> bool:
    """Tente d'importer une bibliothèque et affiche sa version."""
    try:
        importlib.import_module(module)
        version = metadata.version(paquet)
        print(f"[OK]  {paquet} {version}")
        return True
    except Exception as erreur:  # on veut capturer toute erreur d'import
        print(f"[ECHEC] {paquet} : {type(erreur).__name__}: {erreur}")
        return False


def verifier_ffmpeg() -> bool:
    """Vérifie que FFmpeg est accessible depuis Python (donc utilisable par pydub)."""
    chemin = shutil.which("ffmpeg")
    if chemin is None:
        print("[ECHEC] ffmpeg introuvable dans le PATH")
        return False
    resultat = subprocess.run(
        [chemin, "-version"], capture_output=True, text=True, check=False
    )
    premiere_ligne = resultat.stdout.splitlines()[0] if resultat.stdout else "?"
    print(f"[OK]  {premiere_ligne}")
    return True


def main() -> int:
    """Lance toutes les vérifications et retourne 0 si tout est bon, 1 sinon."""
    resultats = [verifier_python()]
    resultats += [verifier_bibliotheque(m, p) for m, p in BIBLIOTHEQUES]
    resultats.append(verifier_ffmpeg())

    print()
    if all(resultats):
        print("Tout est prêt.")
        return 0
    print("Certaines vérifications ont échoué : regarde les lignes [ECHEC].")
    return 1


if __name__ == "__main__":
    sys.exit(main())