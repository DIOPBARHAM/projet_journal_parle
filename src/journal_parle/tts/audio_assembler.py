"""Assemble les MP3 de chapitres en un MP3 final avec marqueurs de chapitres.

Essai : python -X utf8 -m journal_parle.tts.audio_assembler
(utilise les chapitres déjà présents dans outputs/chapitres/)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pydub import AudioSegment

from journal_parle.tts.chapter_audio import DOSSIER_SORTIE, ChapitreAudio

MP3_FINAL = Path("outputs/journal_parle.mp3")
LISTE_CHAPITRES = Path("outputs/chapitres.txt")
PAUSE_ENTRE_CHAPITRES_MS = 800


class ErreurAssemblage(Exception):
    """Erreur levée quand l'assemblage audio échoue."""


def _echapper_metadonnee(texte: str) -> str:
    """Échappe les caractères spéciaux du format FFMETADATA (= ; # \\ et saut de ligne)."""
    for caractere in ("\\", "=", ";", "#", "\n"):
        texte = texte.replace(caractere, "\\" + caractere)
    return texte


def _formater_temps(ms: int) -> str:
    """Convertit des millisecondes en 'MM:SS' (ou 'H:MM:SS' au-delà d'une heure)."""
    secondes = ms // 1000
    h, reste = divmod(secondes, 3600)
    m, s = divmod(reste, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def assembler(
    chapitres: list[ChapitreAudio],
    sortie: Path = MP3_FINAL,
    liste: Path = LISTE_CHAPITRES,
) -> Path:
    """Colle les chapitres dans l'ordre et écrit les marqueurs de chapitres.

    Paramètres :
        chapitres: résultats de la synthèse, dans l'ordre de lecture.
        sortie: chemin du MP3 final.
        liste: chemin du fichier texte listant les chapitres et leurs horodatages.

    Retourne :
        Le chemin du MP3 final.

    Lève :
        ErreurAssemblage si la liste est vide, si FFmpeg est absent ou échoue.
    """
    if not chapitres:
        raise ErreurAssemblage("Aucun chapitre à assembler.")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise ErreurAssemblage("FFmpeg introuvable dans le PATH.")

    sortie.parent.mkdir(parents=True, exist_ok=True)
    silence = AudioSegment.silent(duration=PAUSE_ENTRE_CHAPITRES_MS)
    audio_total = AudioSegment.empty()
    metadonnees = [";FFMETADATA1"]
    lignes_liste: list[str] = []

    for chapitre in chapitres:
        debut = len(audio_total)
        audio_total += AudioSegment.from_mp3(str(chapitre.mp3))
        fin = len(audio_total)
        audio_total += silence
        metadonnees += [
            "[CHAPTER]",
            "TIMEBASE=1/1000",
            f"START={debut}",
            f"END={fin}",
            f"title={_echapper_metadonnee(chapitre.titre)}",
        ]
        lignes_liste.append(f"{_formater_temps(debut)}  {chapitre.titre}")

    with tempfile.TemporaryDirectory() as dossier_tmp:
        brut = Path(dossier_tmp) / "brut.mp3"
        meta = Path(dossier_tmp) / "chapitres.ffmeta"
        audio_total.export(str(brut), format="mp3")
        meta.write_text("\n".join(metadonnees) + "\n", encoding="utf-8")
        commande = [
            ffmpeg, "-y", "-loglevel", "error",
            "-i", str(brut), "-i", str(meta),
            "-map_metadata", "1", "-map_chapters", "1",
            "-codec", "copy", str(sortie),
        ]
        resultat = subprocess.run(commande, capture_output=True, text=True, check=False)
        if resultat.returncode != 0:
            raise ErreurAssemblage(f"FFmpeg a échoué : {resultat.stderr.strip()}")

    liste.write_text("\n".join(lignes_liste) + "\n", encoding="utf-8")
    return sortie


def _chapitres_existants(dossier: Path = DOSSIER_SORTIE) -> list[ChapitreAudio]:
    """Reconstruit la liste des chapitres à partir des fichiers déjà générés (pour l'essai)."""
    resultats = []
    for mp3 in sorted(dossier.glob("chapitre_*.mp3")):
        texte = mp3.with_suffix(".txt")
        resultats.append(ChapitreAudio(mp3.stem.replace("_", " ").capitalize(), mp3, texte, 0))
    return resultats


if __name__ == "__main__":
    try:
        final = assembler(_chapitres_existants())
        print(f"MP3 final : {final} ({final.stat().st_size} octets)")
        print(LISTE_CHAPITRES.read_text(encoding="utf-8"))
    except ErreurAssemblage as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)