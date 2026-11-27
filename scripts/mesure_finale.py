"""Mesure finale du CER sur les PDF de data/test/ (à lancer UNE seule fois).

Lancer : python -X utf8 scripts/mesure_finale.py
Résultats : outputs/mesure_finale.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from journal_parle.evaluation.metrics import evaluer_audio, preparer_pour_comparaison
from journal_parle.evaluation.error_analysis import lister_erreurs
from journal_parle.evaluation.transcriber import MODELE_PAR_DEFAUT, transcrire
from journal_parle.extraction.pdf_reader import extraire_pages
from journal_parle.preprocessing.cleaner import nettoyer_pages
from journal_parle.preprocessing.normalizer import normaliser_texte
from journal_parle.preprocessing.segmenter import Chapitre, segmenter
from journal_parle.tts.chapter_audio import synthetiser_chapitre

DOSSIER_TEST = Path("data/test")
SORTIE = Path("outputs/mesure_finale.json")
NB_CARACTERES_MAX = 3000


def extrait(chapitres: list[Chapitre], limite: int) -> Chapitre:
    """Prend les premières phrases (dans l'ordre) jusqu'à `limite` caractères."""
    phrases: list[str] = []
    total = 0
    for chap in chapitres:
        for phrase in chap.phrases:
            if total >= limite:
                return Chapitre("Extrait", phrases)
            phrases.append(phrase)
            total += len(phrase)
    return Chapitre("Extrait", phrases)


def mesurer(pdf: Path) -> dict:
    """Pipeline complet sur un PDF : texte -> voix -> Whisper -> CER."""
    chapitres = segmenter(nettoyer_pages(extraire_pages(pdf)))
    chap = extrait(chapitres, NB_CARACTERES_MAX)
    dossier = Path("outputs/mesure") / pdf.stem
    audio = synthetiser_chapitre(chap, 1, dossier)
    reference = audio.texte_lu.read_text(encoding="utf-8")
    transcription = transcrire(audio.mp3)
    r = evaluer_audio(reference, transcription)
    erreurs = lister_erreurs(
        preparer_pour_comparaison(reference),
        preparer_pour_comparaison(normaliser_texte(transcription)),
    )
    return {
        "pdf": pdf.name,
        "modele_whisper": MODELE_PAR_DEFAUT,
        "nb_phrases": len(chap.phrases),
        "duree_audio_s": round(audio.duree_ms / 1000, 1),
        "S": r.substitutions, "D": r.suppressions, "I": r.insertions,
        "N": r.total_reference,
        "cer_pourcent": round(100 * r.cer, 2),
        "erreurs": [vars(e) for e in erreurs],
    }


if __name__ == "__main__":
    if SORTIE.exists():
        print(f"{SORTIE} existe déjà : la mesure finale ne se relance pas.")
        sys.exit(1)
    resultats = []
    for pdf in sorted(DOSSIER_TEST.glob("*.pdf")):
        debut = time.time()
        print(f"Mesure de {pdf.name}...")
        res = mesurer(pdf)
        res["temps_calcul_s"] = round(time.time() - debut)
        resultats.append(res)
        print(f"  CER = {res['cer_pourcent']} %  (N={res['N']}, {res['duree_audio_s']} s d'audio)")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(json.dumps(resultats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Résultats enregistrés : {SORTIE}")