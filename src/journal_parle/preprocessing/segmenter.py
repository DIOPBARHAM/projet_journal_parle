"""Segmentation du texte nettoyé en chapitres, puis en phrases.

Lancer pour un essai : python -X utf8 -m journal_parle.preprocessing.segmenter fichier.pdf
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field

from journal_parle.extraction.pdf_reader import ErreurExtractionPDF, extraire_pages
from journal_parle.preprocessing.cleaner import (
    ABREVIATIONS,
    _est_titre_ou_majuscules,
    nettoyer_pages,
)

# Un chapitre plus court que ce nombre de caractères est fusionné avec le suivant
LONGUEUR_MIN_CHAPITRE = 200

TITRE_PAR_DEFAUT = "Document"

# Fin de phrase : ponctuation suivie d'espace(s) puis d'une majuscule ou d'un guillemet
MOTIF_COUPURE = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀÂÉÈÊËÎÏÔÙÛÇ«\"“(])")


@dataclass
class Chapitre:
    """Un chapitre : un titre et la liste de ses phrases."""

    titre: str
    phrases: list[str] = field(default_factory=list)

    @property
    def nb_caracteres(self) -> int:
        return sum(len(p) for p in self.phrases)


def decouper_en_phrases(texte: str) -> list[str]:
    """Découpe un paragraphe en phrases, sans couper après une abréviation.

    Exemple : "Le Prof. Fall est là. Il parle." -> ["Le Prof. Fall est là.", "Il parle."]
    """
    morceaux = MOTIF_COUPURE.split(texte.strip())
    phrases: list[str] = []
    for morceau in morceaux:
        morceau = morceau.strip()
        if not morceau:
            continue
        if phrases and phrases[-1].split()[-1] in ABREVIATIONS:
            phrases[-1] = f"{phrases[-1]} {morceau}"  # on recolle après "Prof."
        else:
            phrases.append(morceau)
    return phrases


def _fusionner_chapitres_courts(chapitres: list[Chapitre]) -> list[Chapitre]:
    """Fusionne chaque chapitre trop court avec le suivant (ou le précédent pour le dernier)."""
    resultat: list[Chapitre] = []
    en_attente: Chapitre | None = None

    for chapitre in chapitres:
        if en_attente is not None:
            # le titre du chapitre court est lu comme une phrase du chapitre fusionné
            chapitre = Chapitre(
                titre=en_attente.titre,
                phrases=[chapitre.titre] + en_attente.phrases + chapitre.phrases
                if False
                else en_attente.phrases + [chapitre.titre] + chapitre.phrases,
            )
            en_attente = None
        if chapitre.nb_caracteres < LONGUEUR_MIN_CHAPITRE:
            en_attente = chapitre
        else:
            resultat.append(chapitre)

    if en_attente is not None:
        if resultat:
            resultat[-1].phrases += [en_attente.titre] + en_attente.phrases
        else:
            resultat.append(en_attente)
    return resultat


def segmenter(texte_nettoye: str) -> list[Chapitre]:
    """Découpe le texte nettoyé en chapitres contenant des phrases.

    Paramètre :
        texte_nettoye: sortie de nettoyer_pages (un paragraphe ou titre par ligne).

    Retourne :
        La liste des chapitres, dans l'ordre. Toujours au moins un chapitre
        si le texte n'est pas vide.
    """
    chapitres: list[Chapitre] = []
    courant: Chapitre | None = None

    for ligne in texte_nettoye.splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        if _est_titre_ou_majuscules(ligne):
            courant = Chapitre(titre=ligne)
            chapitres.append(courant)
            continue
        if courant is None:
            courant = Chapitre(titre=TITRE_PAR_DEFAUT)
            chapitres.append(courant)
        courant.phrases.extend(decouper_en_phrases(ligne))

    chapitres = [c for c in chapitres if c.phrases]
    return _fusionner_chapitres_courts(chapitres)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage : python -X utf8 -m journal_parle.preprocessing.segmenter "fichier.pdf"')
        sys.exit(1)
    try:
        for numero, chap in enumerate(segmenter(nettoyer_pages(extraire_pages(sys.argv[1]))), 1):
            print(f"[{numero}] {chap.titre} : {len(chap.phrases)} phrases, {chap.nb_caracteres} caractères")
            print(f"     1re phrase : {chap.phrases[0][:90]}")
    except ErreurExtractionPDF as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)