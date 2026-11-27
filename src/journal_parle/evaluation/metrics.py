"""Calcul du CER (Character Error Rate) entre un texte de référence et une transcription.

Essai : python -X utf8 -m journal_parle.evaluation.metrics outputs/chapitres/chapitre_01.txt outputs/chapitres/chapitre_01.mp3
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import jiwer

from journal_parle.evaluation.transcriber import ErreurTranscription, transcrire
from journal_parle.preprocessing.normalizer import normaliser_texte


class ErreurEvaluation(Exception):
    """Erreur levée quand le CER ne peut pas être calculé."""


@dataclass(frozen=True)
class ResultatCER:
    """Détail d'un calcul de CER."""

    substitutions: int
    suppressions: int
    insertions: int
    total_reference: int

    @property
    def cer(self) -> float:
        """CER = (S + D + I) / N."""
        erreurs = self.substitutions + self.suppressions + self.insertions
        return erreurs / self.total_reference


def preparer_pour_comparaison(texte: str) -> str:
    """Minuscules, ponctuation retirée, espaces réduits (accents conservés)."""
    texte = texte.lower()
    texte = re.sub(r"[^\w\s]|_", " ", texte)  # apostrophes, tirets, ponctuation -> espace
    return re.sub(r"\s+", " ", texte).strip()


def calculer_cer(reference: str, hypothese: str) -> ResultatCER:
    """Calcule le CER entre deux textes déjà préparés.

    Lève ErreurEvaluation si la référence est vide.
    """
    if not reference.strip():
        raise ErreurEvaluation("Texte de référence vide : CER impossible.")
    mesure = jiwer.process_characters(reference, hypothese)
    n = mesure.hits + mesure.substitutions + mesure.deletions
    return ResultatCER(mesure.substitutions, mesure.deletions, mesure.insertions, n)


def evaluer_audio(texte_reference: str, transcription: str) -> ResultatCER:
    """CER équitable : la transcription est normalisée comme le texte lu."""
    ref = preparer_pour_comparaison(texte_reference)
    hyp = preparer_pour_comparaison(normaliser_texte(transcription))
    return calculer_cer(ref, hyp)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage : python -X utf8 -m journal_parle.evaluation.metrics "reference.txt" "audio.mp3"')
        sys.exit(1)
    try:
        reference = Path(sys.argv[1]).read_text(encoding="utf-8")
        transcription = transcrire(sys.argv[2])
        r = evaluer_audio(reference, transcription)
        print("Référence  :", preparer_pour_comparaison(reference))
        print("Whisper    :", preparer_pour_comparaison(normaliser_texte(transcription)))
        print(f"S={r.substitutions}  D={r.suppressions}  I={r.insertions}  N={r.total_reference}")
        print(f"CER = {r.cer:.1%}")
    except (OSError, ErreurTranscription, ErreurEvaluation) as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)