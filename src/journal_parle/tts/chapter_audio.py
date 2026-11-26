"""Génère un MP3 par chapitre : normalisation, synthèse phrase par phrase, assemblage.

Essai : python -X utf8 -m journal_parle.tts.chapter_audio data/dev/exemple_synthetique.pdf
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

from pydub import AudioSegment

from journal_parle.extraction.pdf_reader import ErreurExtractionPDF, extraire_pages
from journal_parle.preprocessing.cleaner import nettoyer_pages
from journal_parle.preprocessing.normalizer import charger_sigles, normaliser_texte
from journal_parle.preprocessing.segmenter import Chapitre, segmenter
from journal_parle.tts.tts_engine import VOIX_PAR_DEFAUT, ErreurSynthese, synthetiser

PAUSE_ENTRE_PHRASES_MS = 300
NB_ESSAIS = 3
DOSSIER_SORTIE = Path("outputs/chapitres")


@dataclass(frozen=True)
class ChapitreAudio:
    """Résultat de la synthèse d'un chapitre."""

    titre: str
    mp3: Path
    texte_lu: Path
    duree_ms: int


def _synthetiser_avec_reessais(texte: str, sortie: Path, voix: str) -> None:
    """Appelle Edge TTS, avec NB_ESSAIS tentatives en cas d'échec réseau."""
    for essai in range(1, NB_ESSAIS + 1):
        try:
            synthetiser(texte, sortie, voix)
            return
        except ErreurSynthese:
            if essai == NB_ESSAIS:
                raise
            time.sleep(2 * essai)


def synthetiser_chapitre(
    chapitre: Chapitre, numero: int, dossier: Path = DOSSIER_SORTIE, voix: str = VOIX_PAR_DEFAUT
) -> ChapitreAudio:
    """Génère le MP3 d'un chapitre et le fichier texte de ce qui a été lu.

    Le titre du chapitre est lu en premier, puis chaque phrase.
    """
    dossier.mkdir(parents=True, exist_ok=True)
    sigles = charger_sigles()
    morceaux_texte = [chapitre.titre] + chapitre.phrases
    phrases_lues = [normaliser_texte(p, sigles) for p in morceaux_texte]

    audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=PAUSE_ENTRE_PHRASES_MS)
    temporaire = dossier / f"_tmp_{numero:02d}.mp3"
    try:
        for phrase in phrases_lues:
            if not phrase.strip():
                continue
            _synthetiser_avec_reessais(phrase, temporaire, voix)
            audio += AudioSegment.from_mp3(str(temporaire)) + silence
    finally:
        temporaire.unlink(missing_ok=True)

    mp3 = dossier / f"chapitre_{numero:02d}.mp3"
    texte_lu = dossier / f"chapitre_{numero:02d}.txt"
    audio.export(str(mp3), format="mp3")
    texte_lu.write_text("\n".join(phrases_lues), encoding="utf-8")
    return ChapitreAudio(chapitre.titre, mp3, texte_lu, len(audio))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage : python -X utf8 -m journal_parle.tts.chapter_audio "fichier.pdf"')
        sys.exit(1)
    try:
        chapitres = segmenter(nettoyer_pages(extraire_pages(sys.argv[1])))
        for i, chap in enumerate(chapitres, start=1):
            resultat = synthetiser_chapitre(chap, i)
            print(f"[{i}] {resultat.titre} : {resultat.duree_ms / 1000:.1f} s -> {resultat.mp3}")
    except (ErreurExtractionPDF, ErreurSynthese) as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)