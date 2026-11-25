"""Extraction du texte brut d'un fichier PDF avec PyMuPDF.

Lancer pour un essai : python -m journal_parle.extraction.pdf_reader chemin/du/fichier.pdf
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pymupdf


class ErreurExtractionPDF(Exception):
    """Erreur levée quand le PDF ne peut pas être lu ou ne contient pas de texte."""


@dataclass(frozen=True)
class PageTexte:
    """Le texte d'une page du PDF.

    Attributs :
        numero: numéro de la page dans le PDF (la première page vaut 1).
        texte: texte brut de la page, tel que lu par PyMuPDF.
    """

    numero: int
    texte: str


def extraire_pages(chemin_pdf: str | Path) -> list[PageTexte]:
    """Lit un PDF et retourne le texte de chaque page.

    Paramètre :
        chemin_pdf: chemin du fichier PDF.

    Retourne :
        La liste des pages, dans l'ordre, sous forme de PageTexte.

    Lève :
        ErreurExtractionPDF si le fichier est introuvable, n'est pas un PDF,
        est protégé par mot de passe, est illisible ou ne contient aucun texte.
    """
    chemin = Path(chemin_pdf)

    if not chemin.is_file():
        raise ErreurExtractionPDF(f"Fichier introuvable : {chemin}")
    if chemin.suffix.lower() != ".pdf":
        raise ErreurExtractionPDF(f"Ce fichier n'est pas un PDF : {chemin.name}")

    try:
        document = pymupdf.open(str(chemin))
    except Exception as erreur:  # PyMuPDF lève plusieurs types d'erreurs
        raise ErreurExtractionPDF(
            f"Impossible d'ouvrir le PDF (fichier corrompu ?) : {erreur}"
        ) from erreur

    with document:
        if document.needs_pass:
            raise ErreurExtractionPDF("Le PDF est protégé par un mot de passe.")

        # sort=True remet les blocs de texte dans l'ordre de lecture
        pages = [
            PageTexte(numero=numero, texte=page.get_text("text", sort=True))
            for numero, page in enumerate(document, start=1)
        ]

    if not any(page.texte.strip() for page in pages):
        raise ErreurExtractionPDF(
            "Aucun texte trouvé : le PDF est probablement un scan (image). "
            "L'OCR n'est pas pris en charge."
        )

    return pages


def _afficher_apercu(pages: list[PageTexte]) -> None:
    """Affiche un résumé : nombre de caractères, début et fin de chaque page."""
    for page in pages:
        lignes = [ligne for ligne in page.texte.splitlines() if ligne.strip()]
        print(f"--- Page {page.numero} : {len(page.texte)} caractères, "
              f"{len(lignes)} lignes non vides ---")
        print("  Début :", lignes[:3])
        print("  Fin   :", lignes[-2:])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage : python -m journal_parle.extraction.pdf_reader fichier.pdf")
        sys.exit(1)
    try:
        _afficher_apercu(extraire_pages(sys.argv[1]))
    except ErreurExtractionPDF as erreur:
        print(f"Erreur : {erreur}")
        sys.exit(1)
