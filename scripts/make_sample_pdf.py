"""Génère un PDF d'essai de 5 pages (en-tête, numéro de page, pièges de lecture).

Lancer avec : python scripts/make_sample_pdf.py
Ce PDF est synthétique : il sert uniquement à tester l'extraction.
"""

from pathlib import Path

import pymupdf

SORTIE = Path("data/dev/exemple_synthetique.pdf")

CORPS_PAGES = [
    "Chapitre 1 : Les inscriptions\n\n"
    "Le 1er mars 2025, l'UCAD a ouvert les inscriptions. "
    "Les frais sont de 10 000 F CFA pour les nouveaux étudiants. "
    "La réunion d'information aura lieu le 3/11 à 14 h 30.",
    "Les étudiants doivent déposer leur dossier avant le 15 avril. "
    "Le dossier comprend 3 pièces : un acte de naissance, une photo et un reçu.",
    "Chapitre 2 : Les bourses\n\n"
    "En 2024, environ 2 500 bourses ont été attribuées. "
    "Le MESRI publie la liste le 2e lundi du mois.",
    "Le montant moyen d'une bourse est de 40 000 F CFA par mois. "
    "Les résultats sont disponibles sur le site officiel.",
    "Chapitre 3 : Conclusion\n\n"
    "Ce bulletin résume les principales informations de la rentrée. "
    "Pour plus de détails, consultez le secrétariat de l'UFR.",
]


def main() -> None:
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    document = pymupdf.open()
    for numero, corps in enumerate(CORPS_PAGES, start=1):
        page = document.new_page()  # format A4 par défaut
        page.insert_text((72, 45), "Bulletin d'information - Université de Dakar",
                         fontsize=9, fontname="helv")
        page.insert_textbox(pymupdf.Rect(72, 100, 523, 700), corps,
                            fontsize=12, fontname="helv")
        page.insert_text((280, 805), f"Page {numero}", fontsize=9, fontname="helv")
    document.save(str(SORTIE))
    document.close()
    print(f"PDF créé : {SORTIE}")


if __name__ == "__main__":
    main()