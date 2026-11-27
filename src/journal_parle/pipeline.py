"""Orchestration du pipeline complet : PDF -> MP3 avec chapitres (+ CER optionnel).

Essai : python -X utf8 -m journal_parle.pipeline data/dev/exemple_synthetique.pdf
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from journal_parle.evaluation.metrics import ResultatCER, evaluer_audio
from journal_parle.evaluation.transcriber import ErreurTranscription, transcrire
from journal_parle.extraction.pdf_reader import ErreurExtractionPDF, extraire_pages
from journal_parle.preprocessing.cleaner import nettoyer_pages
from journal_parle.preprocessing.segmenter import segmenter
from journal_parle.tts.audio_assembler import ErreurAssemblage, assembler
from journal_parle.tts.chapter_audio import ChapitreAudio, synthetiser_chapitre
from journal_parle.tts.tts_engine import VOIX_PAR_DEFAUT, ErreurSynthese

DOSSIER_RESULTATS = Path("outputs/pipeline")
NB_CARACTERES_EVALUATION = 3000

ErreurPipeline = (ErreurExtractionPDF, ErreurSynthese, ErreurAssemblage, ErreurTranscription)


@dataclass(frozen=True)
class ResultatPipeline:
    """Ce que le pipeline retourne à l'appelant (Gradio, main.py)."""

    mp3_final: Path
    liste_chapitres: Path
    chapitres: list[ChapitreAudio]
    cer: ResultatCER | None


def executer(
    pdf: str | Path,
    voix: str = VOIX_PAR_DEFAUT,
    evaluer: bool = False,
    dossier: Path = DOSSIER_RESULTATS,
    progression: Callable[[float, str], None] | None = None,
) -> ResultatPipeline:
    """Convertit un PDF en MP3 avec chapitres.

    Paramètres :
        pdf: chemin du PDF.
        voix: voix Edge TTS.
        evaluer: si True, transcrit le 1er chapitre avec Whisper et calcule le CER.
        dossier: dossier de sortie.
        progression: fonction (fraction 0-1, message), pour afficher l'avancement.

    Lève :
        Une des erreurs de ErreurPipeline en cas d'échec.
    """
    def avancer(fraction: float, message: str) -> None:
        if progression:
            progression(fraction, message)

    avancer(0.0, "Lecture du PDF")
    chapitres = segmenter(nettoyer_pages(extraire_pages(pdf)))
    if not chapitres:
        raise ErreurExtractionPDF("Aucun texte exploitable après nettoyage.")

    dossier_chapitres = dossier / "chapitres"
    audios: list[ChapitreAudio] = []
    for i, chapitre in enumerate(chapitres, start=1):
        avancer(0.1 + 0.7 * (i - 1) / len(chapitres), f"Synthèse {i}/{len(chapitres)} : {chapitre.titre}")
        audios.append(synthetiser_chapitre(chapitre, i, dossier_chapitres, voix))

    avancer(0.85, "Assemblage du MP3 final")
    mp3 = assembler(audios, dossier / "journal_parle.mp3", dossier / "chapitres.txt")

    cer = None
    if evaluer:
        avancer(0.9, "Transcription Whisper et calcul du CER")
        reference = audios[0].texte_lu.read_text(encoding="utf-8")
        cer = evaluer_audio(reference[:NB_CARACTERES_EVALUATION], transcrire(audios[0].mp3))
    avancer(1.0, "Terminé")
    return ResultatPipeline(mp3, dossier / "chapitres.txt", audios, cer)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage : python -X utf8 -m journal_parle.pipeline "fichier.pdf"')
        sys.exit(1)
    try:
        r = executer(sys.argv[1], progression=lambda f, m: print(f"[{f:4.0%}] {m}"))
        print(f"MP3 final : {r.mp3_final}")
    except ErreurPipeline as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)