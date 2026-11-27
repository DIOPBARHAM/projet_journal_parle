"""Lance le pipeline en ligne de commande.

Usage : python -X utf8 main.py document.pdf [--cer]
"""

from __future__ import annotations

import sys

from journal_parle.pipeline import ErreurPipeline, executer


def main() -> int:
    arguments = [argument for argument in sys.argv[1:] if argument != "--cer"]
    if len(arguments) != 1:
        print('Usage : python -X utf8 main.py "document.pdf" [--cer]')
        return 1
    try:
        resultat = executer(
            arguments[0],
            evaluer="--cer" in sys.argv,
            progression=lambda fraction, message: print(
                f"[{fraction:4.0%}] {message}"
            ),
        )
    except ErreurPipeline as erreur:
        print(f"Erreur : {erreur}")
        return 1

    print(f"MP3 final : {resultat.mp3_final}")
    print(resultat.liste_chapitres.read_text(encoding="utf-8"))
    if resultat.cer is not None:
        print(f"CER (chapitre 1) : {resultat.cer.cer:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
