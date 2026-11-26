"""Transcription d'un fichier audio avec faster-whisper (reconnaissance vocale).

Essai : python -X utf8 -m journal_parle.evaluation.transcriber outputs/chapitres/chapitre_01.mp3
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel

MODELE_PAR_DEFAUT = "small"

_cache_modeles: dict[str, WhisperModel] = {}


class ErreurTranscription(Exception):
    """Erreur levée quand la transcription échoue."""


def _charger_modele(nom: str) -> WhisperModel:
    """Charge le modèle une seule fois (le chargement est lent)."""
    if nom not in _cache_modeles:
        try:
            # device="auto" : GPU s'il existe (Colab), sinon CPU
            _cache_modeles[nom] = WhisperModel(nom, device="auto", compute_type="auto")
        except Exception as erreur:
            raise ErreurTranscription(
                f"Impossible de charger le modèle Whisper '{nom}' "
                f"(Internet pour le premier téléchargement ?) : {erreur}"
            ) from erreur
    return _cache_modeles[nom]


def transcrire(audio: str | Path, modele: str = MODELE_PAR_DEFAUT) -> str:
    """Transcrit un fichier audio en texte français.

    Paramètres :
        audio: chemin du fichier audio (MP3, WAV...).
        modele: taille du modèle Whisper (tiny, base, small, medium).

    Retourne :
        Le texte transcrit.

    Lève :
        ErreurTranscription si le fichier est absent ou si Whisper échoue.
    """
    chemin = Path(audio)
    if not chemin.is_file():
        raise ErreurTranscription(f"Fichier audio introuvable : {chemin}")
    whisper = _charger_modele(modele)
    try:
        segments, _ = whisper.transcribe(str(chemin), language="fr", beam_size=5)
        return " ".join(s.text.strip() for s in segments).strip()
    except Exception as erreur:
        raise ErreurTranscription(f"Échec de la transcription : {erreur}") from erreur


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage : python -X utf8 -m journal_parle.evaluation.transcriber "audio.mp3"')
        sys.exit(1)
    try:
        debut = time.time()
        print(transcrire(sys.argv[1]))
        print(f"\n(temps : {time.time() - debut:.1f} s, modèle : {MODELE_PAR_DEFAUT})")
    except ErreurTranscription as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)