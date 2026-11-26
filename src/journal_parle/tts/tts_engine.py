"""Synthèse vocale avec Edge TTS (nécessite une connexion Internet).

Essai : python -X utf8 -m journal_parle.tts.tts_engine "Bonjour, ceci est un test."
        python -X utf8 -m journal_parle.tts.tts_engine --voix
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import edge_tts

VOIX_PAR_DEFAUT = "fr-FR-DeniseNeural"


class ErreurSynthese(Exception):
    """Erreur levée quand la synthèse vocale échoue."""


async def lister_voix_francaises() -> list[str]:
    """Retourne les noms des voix françaises disponibles."""
    voix = await edge_tts.list_voices()
    return sorted(v["ShortName"] for v in voix if v["Locale"].startswith("fr-"))


async def synthetiser_async(
    texte: str, sortie: Path, voix: str = VOIX_PAR_DEFAUT
) -> Path:
    """Convertit un texte en fichier MP3.

    Paramètres :
        texte: texte à lire (déjà normalisé).
        sortie: chemin du MP3 à créer.
        voix: nom de la voix Edge TTS.

    Retourne :
        Le chemin du MP3 créé.

    Lève :
        ErreurSynthese si le texte est vide, si Internet est coupé ou si le service échoue.
    """
    if not texte.strip():
        raise ErreurSynthese("Texte vide : rien à synthétiser.")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    try:
        await edge_tts.Communicate(texte, voix).save(str(sortie))
    except Exception as erreur:
        raise ErreurSynthese(
            f"Échec Edge TTS (Internet coupé ? voix inconnue ?) : {erreur}"
        ) from erreur
    if not sortie.is_file() or sortie.stat().st_size == 0:
        raise ErreurSynthese("Le MP3 produit est vide.")
    return sortie


def synthetiser(
    texte: str, sortie: str | Path, voix: str = VOIX_PAR_DEFAUT
) -> Path:
    """Version synchrone de synthetiser_async (plus simple à appeler)."""
    return asyncio.run(synthetiser_async(texte, Path(sortie), voix))


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["--voix"]:
            print("\n".join(asyncio.run(lister_voix_francaises())))
        elif len(sys.argv) == 2:
            chemin = synthetiser(sys.argv[1], "outputs/essai.mp3")
            print(f"MP3 créé : {chemin} ({chemin.stat().st_size} octets)")
        else:
            print('Usage : python -X utf8 -m journal_parle.tts.tts_engine "texte" | --voix')
            sys.exit(1)
    except ErreurSynthese as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)
