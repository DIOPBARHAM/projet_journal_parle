"""Nettoyage du texte extrait d'un PDF : en-têtes, pieds de page, numéros de page.

Lancer pour un essai : python -m journal_parle.preprocessing.cleaner fichier.pdf
Option --debug : affiche aussi les motifs détectés comme en-têtes/pieds de page.
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

# Un bandeau en MAJUSCULES répété sur au moins ce nombre de pages est supprimé
NB_PAGES_BANDEAU = 3

# Il faut au moins ce nombre de pages pour détecter des répétitions
NB_PAGES_MINIMUM = 3

# Une ligne en majuscules doit contenir au moins ce nombre de lettres
NB_LETTRES_MIN_MAJUSCULES = 4

# Lignes qui ne contiennent qu'un numéro de page : "3", "Page 3", "- 3 -", "3 / 12"
MOTIF_NUMERO_PAGE = re.compile(
    r"^\s*[-–—]?\s*(?:page|p\.)?\s*\d{1,4}\s*(?:/|sur|of)?\s*\d{0,4}\s*[-–—]?\s*$",
    re.IGNORECASE,
)

# Titres : "Chapitre 2", "Chapitre 2 : Les bourses", "Partie 1", "1. Introduction"
MOTIF_TITRE = re.compile(
    r"^\s*(?:(?:chapitre|partie|section)\s+\w+\b.*|\d{1,2}(?:\.\d{1,2})*[.)]\s+\S.*)$",
    re.IGNORECASE,
)

# Ponctuation qui termine une phrase
FIN_DE_PHRASE = (".", "!", "?", "…", ":", "»")

# Abréviations après lesquelles un point ne termine pas la phrase
ABREVIATIONS = {"M.", "MM.", "Mme.", "Mlle.", "Dr.", "Pr.", "Prof.", "St.", "Ste."}


def _normaliser_ligne(ligne: str) -> str:
    """Réduit les espaces multiples et retire les espaces aux extrémités."""
    return re.sub(r"\s+", " ", ligne).strip()


def _lignes_non_vides(texte: str) -> list[str]:
    """Retourne les lignes non vides d'une page, normalisées."""
    lignes = [_normaliser_ligne(ligne) for ligne in texte.splitlines()]
    return [ligne for ligne in lignes if ligne]


def _cle_motif(ligne: str) -> str:
    """Transforme une ligne en motif comparable : chiffres -> '#', espaces supprimés.

    Exemple : "N°05 / JUILLET 2024 - 29" et "N°04/ JUILLET 2024 - 30"
    donnent le même motif.
    """
    return re.sub(r"\s+", "", re.sub(r"\d", "#", ligne))


def _est_numero_de_page(ligne: str) -> bool:
    """Retourne True si la ligne ne contient qu'un numéro de page."""
    return bool(MOTIF_NUMERO_PAGE.match(ligne))


def _est_titre(ligne: str) -> bool:
    """Retourne True si la ligne ressemble à un titre de chapitre ou de section."""
    return bool(MOTIF_TITRE.match(ligne))


def _est_en_majuscules(ligne: str) -> bool:
    """Retourne True si la ligne est courte et entièrement en majuscules."""
    lettres = [c for c in ligne if c.isalpha()]
    return (
        len(lettres) >= NB_LETTRES_MIN_MAJUSCULES
        and ligne.upper() == ligne
        and len(ligne.split()) <= 12
    )


def _est_titre_ou_majuscules(ligne: str) -> bool:
    """Retourne True si la ligne doit rester isolée dans son propre paragraphe."""
    return _est_titre(ligne) or _est_en_majuscules(ligne)


def _indices_bordure(nb_lignes: int) -> set[int]:
    """Retourne les positions des premières et dernières lignes d'une page."""
    debut = range(min(NB_LIGNES_BORDURE, nb_lignes))
    fin = range(max(0, nb_lignes - NB_LIGNES_BORDURE), nb_lignes)
    return set(debut) | set(fin)


def detecter_lignes_repetees(pages: list[PageTexte]) -> set[str]:
    """Repère les motifs de lignes qui reviennent en bordure de page.

    Paramètre :
        pages: les pages extraites du PDF.

    Retourne :
        L'ensemble des motifs (voir _cle_motif) à considérer comme en-têtes,
        pieds de page ou bandeaux. Ensemble vide si le document a trop peu de pages.
    """
    if len(pages) < NB_PAGES_MINIMUM:
        return set()

    compteur: Counter[str] = Counter()
    compteur_majuscules: Counter[str] = Counter()

    for page in pages:
        lignes = _lignes_non_vides(page.texte)
        cles: set[str] = set()
        cles_majuscules: set[str] = set()
        for position in _indices_bordure(len(lignes)):
            ligne = lignes[position]
            if _est_titre(ligne):
                continue  # un titre de chapitre n'est jamais un en-tête
            cle = _cle_motif(ligne)
            cles.add(cle)
            if _est_en_majuscules(ligne):
                cles_majuscules.add(cle)
        compteur.update(cles)
        compteur_majuscules.update(cles_majuscules)

    seuil = SEUIL_REPETITION * len(pages)
    generales = {cle for cle, nombre in compteur.items() if nombre >= seuil}
    bandeaux = {
        cle for cle, nombre in compteur_majuscules.items() if nombre >= NB_PAGES_BANDEAU
    }
    return generales | bandeaux


def _phrase_terminee(texte: str) -> bool:
    """Retourne True si le texte se termine par une fin de phrase (hors abréviation)."""
    if not texte.endswith(FIN_DE_PHRASE):
        return False
    dernier_mot = texte.split()[-1]
    return dernier_mot not in ABREVIATIONS


def _recoller_paragraphes(lignes: list[str]) -> list[str]:
    """Regroupe les lignes d'un même paragraphe et garde les titres à part.

    Un paragraphe se termine quand la phrase est terminée ET que la ligne
    suivante ne commence pas par une minuscule. Un tiret de coupure en fin de
    ligne ("informa-" + "tion") est recollé sans espace.
    """
    paragraphes: list[str] = []
    courant = ""

    for position, ligne in enumerate(lignes):
        if _est_titre_ou_majuscules(ligne):
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

        suivante = lignes[position + 1] if position + 1 < len(lignes) else ""
        suite_en_minuscule = bool(suivante) and suivante[0].islower()
        if _phrase_terminee(courant) and not suite_en_minuscule:
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
        Le texte nettoyé : un paragraphe ou un titre par ligne.
    """
    a_supprimer = detecter_lignes_repetees(pages)
    lignes_gardees: list[str] = []

    for page in pages:
        lignes = _lignes_non_vides(page.texte)
        bordure = _indices_bordure(len(lignes))
        for position, ligne in enumerate(lignes):
            if _est_numero_de_page(ligne):
                continue
            # On ne supprime une ligne répétée que si elle est en bordure de page
            if (
                position in bordure
                and not _est_titre(ligne)
                and _cle_motif(ligne) in a_supprimer
            ):
                continue
            lignes_gardees.append(ligne)

    return "\n".join(_recoller_paragraphes(lignes_gardees))


if __name__ == "__main__":
    arguments = [a for a in sys.argv[1:] if a != "--debug"]
    mode_debug = "--debug" in sys.argv[1:]
    if len(arguments) != 1:
        print('Usage : python -m journal_parle.preprocessing.cleaner "fichier.pdf" [--debug]')
        sys.exit(1)
    try:
        pages_extraites = extraire_pages(arguments[0])
        if mode_debug:
            print("Motifs supprimés :")
            for motif in sorted(detecter_lignes_repetees(pages_extraites)):
                print("  ", motif)
            print("-" * 40)
        print(nettoyer_pages(pages_extraites))
    except ErreurExtractionPDF as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)