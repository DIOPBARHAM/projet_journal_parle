"""Nettoyage du texte extrait d'un PDF : en-têtes, pieds de page, numéros de page.

Lancer pour un essai : python -m journal_parle.preprocessing.cleaner chemin/du/fichier.pdf
"""

from __future__ import annotations

import re
import sys
from collections import Counter

from journal_parle.extraction.pdf_reader import (
    ErreurExtractionPDF,
    PageTexte,
    extraire_pages,
)

# Nombre de lignes examinées en haut et en bas de chaque page
NB_LIGNES_BORDURE = 3

# Une ligne répétée sur au moins cette part des pages est un en-tête/pied de page
SEUIL_REPETITION = 0.5

# Il faut au moins ce nombre de pages pour détecter des répétitions
NB_PAGES_MINIMUM = 3

# Lignes qui ne contiennent qu'un numéro de page : "3", "Page 3", "- 3 -", "3 / 12", "Page 3 sur 12"
MOTIF_NUMERO_PAGE = re.compile(
    r"^\s*[-–—]?\s*(?:page|p\.)?\s*\d{1,4}\s*(?:/|sur|of)?\s*\d{0,4}\s*[-–—]?\s*$",
    re.IGNORECASE,
)

# Titres de chapitre : "Chapitre 2", "Chapitre 2 : Les bourses", "Partie 1", "1. Introduction"
MOTIF_TITRE = re.compile(
    r"^\s*(?:(?:chapitre|partie|section)\s+\w+\b.*|\d{1,2}(?:\.\d{1,2})*[.)]\s+\S.*)$",
    re.IGNORECASE,
)

# Ponctuation qui termine une phrase
FIN_DE_PHRASE = (".", "!", "?", "…", ":", "»")


def _normaliser_ligne(ligne: str) -> str:
    """Réduit les espaces multiples et retire les espaces aux extrémités."""
    return re.sub(r"\s+", " ", ligne).strip()


def _est_numero_de_page(ligne: str) -> bool:
    """Retourne True si la ligne ne contient qu'un numéro de page."""
    return bool(MOTIF_NUMERO_PAGE.match(ligne))


def _est_titre(ligne: str) -> bool:
    """Retourne True si la ligne ressemble à un titre de chapitre ou de section."""
    return bool(MOTIF_TITRE.match(ligne))


def _lignes_de_bordure(lignes: list[str]) -> set[str]:
    """Retourne les premières et dernières lignes non vides d'une page."""
    return set(lignes[:NB_LIGNES_BORDURE]) | set(lignes[-NB_LIGNES_BORDURE:])


def detecter_lignes_repetees(pages: list[PageTexte]) -> set[str]:
    """Repère les lignes qui reviennent en bordure de la plupart des pages.

    Paramètre :
        pages: les pages extraites du PDF.

    Retourne :
        L'ensemble des lignes (normalisées) à considérer comme en-têtes ou pieds de page.
        Retourne un ensemble vide si le document a trop peu de pages.
    """
    if len(pages) < NB_PAGES_MINIMUM:
        return set()

    compteur: Counter[str] = Counter()
    for page in pages:
        lignes = [_normaliser_ligne(l) for l in page.texte.splitlines()]
        lignes = [l for l in lignes if l]
        compteur.update(_lignes_de_bordure(lignes))

    seuil = SEUIL_REPETITION * len(pages)
    return {ligne for ligne, nombre in compteur.items() if nombre >= seuil}


def _recoller_paragraphes(lignes: list[str]) -> list[str]:
    """Regroupe les lignes d'un même paragraphe et garde les titres à part.

    Une ligne est collée à la précédente si celle-ci ne se termine pas par une
    ponctuation de fin de phrase et n'est pas un titre. Un tiret de coupure
    en fin de ligne ("informa-" + "tion") est recollé sans espace.
    """
    paragraphes: list[str] = []
    courant = ""

    for ligne in lignes:
        if _est_titre(ligne):
            if courant:
                paragraphes.append(courant)
                courant = ""
            paragraphes.append(ligne)
            continue

        if not courant:
            courant = ligne
        elif courant.endswith("-") and not courant.endswith(" -"):
            courant = courant[:-1] + ligne  # mot coupé par un tiret
        else:
            courant = f"{courant} {ligne}"

        if courant.endswith(FIN_DE_PHRASE):
            paragraphes.append(courant)
            courant = ""

    if courant:
        paragraphes.append(courant)
    return paragraphes


def nettoyer_pages(pages: list[PageTexte]) -> str:
    """Nettoie les pages et retourne le texte final.

    Paramètre :
        pages: les pages extraites du PDF.

    Retourne :
        Le texte nettoyé : un paragraphe ou un titre par ligne, séparés par un saut de ligne.
    """
    lignes_a_supprimer = detecter_lignes_repetees(pages)
    lignes_gardees: list[str] = []

    for page in pages:
        for brute in page.texte.splitlines():
            ligne = _normaliser_ligne(brute)
            if not ligne:
                continue
            if ligne in lignes_a_supprimer or _est_numero_de_page(ligne):
                continue
            lignes_gardees.append(ligne)

    return "\n".join(_recoller_paragraphes(lignes_gardees))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage : python -m journal_parle.preprocessing.cleaner fichier.pdf")
        sys.exit(1)
    try:
        print(nettoyer_pages(extraire_pages(sys.argv[1])))
    except ErreurExtractionPDF as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)