"""Analyse des erreurs : liste des mots mal retrouvés entre référence et transcription.

Essai : python -X utf8 -m journal_parle.evaluation.error_analysis outputs/chapitres/chapitre_01.txt outputs/chapitres/chapitre_01.mp3
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import jiwer

from journal_parle.evaluation.metrics import preparer_pour_comparaison
from journal_parle.evaluation.transcriber import ErreurTranscription, transcrire
from journal_parle.preprocessing.normalizer import normaliser_texte


@dataclass(frozen=True)
class ErreurMot:
    """Un écart entre la référence et la transcription."""

    type: str  # "substitution", "suppression" ou "insertion"
    reference: str
    transcription: str


def lister_erreurs(reference: str, hypothese: str) -> list[ErreurMot]:
    """Compare deux textes préparés mot à mot et liste les écarts."""
    mesure = jiwer.process_words(reference, hypothese)
    mots_ref = reference.split()
    mots_hyp = hypothese.split()
    erreurs: list[ErreurMot] = []
    for chunk in mesure.alignments[0]:
        if chunk.type == "equal":
            continue
        ref = " ".join(mots_ref[chunk.ref_start_idx:chunk.ref_end_idx])
        hyp = " ".join(mots_hyp[chunk.hyp_start_idx:chunk.hyp_end_idx])
        nom = {"substitute": "substitution", "delete": "suppression", "insert": "insertion"}[chunk.type]
        erreurs.append(ErreurMot(nom, ref, hyp))
    return erreurs


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage : python -X utf8 -m journal_parle.evaluation.error_analysis "reference.txt" "audio.mp3"')
        sys.exit(1)
    try:
        ref = preparer_pour_comparaison(Path(sys.argv[1]).read_text(encoding="utf-8"))
        hyp = preparer_pour_comparaison(normaliser_texte(transcrire(sys.argv[2])))
        erreurs = lister_erreurs(ref, hyp)
        print(f"{len(erreurs)} écart(s) :")
        for e in erreurs:
            print(f"  {e.type:13} | référence : {e.reference!r:25} | Whisper : {e.transcription!r}")
    except (OSError, ErreurTranscription) as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)