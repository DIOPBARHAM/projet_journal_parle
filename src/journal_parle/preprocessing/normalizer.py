"""Normalisation du texte : nombres, dates, heures, monnaies, ordinaux, sigles.

Objectif : transformer le texte écrit en texte prononçable par une voix de synthèse.
Lancer pour un essai : python -m journal_parle.preprocessing.normalizer "Le 1er mars, 10 000 F CFA"
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from num2words import num2words

FICHIER_SIGLES = Path(__file__).with_name("sigles.json")
FICHIER_PRONONCIATIONS = Path(__file__).with_name("prononciations.json")

MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre",
]

# Mots courts en majuscules à ne jamais épeler (mots français usuels)
MOTS_MAJUSCULES_A_GARDER = {"A", "LA", "LE", "LES", "ET", "OU", "EN", "UN", "UNE", "DE", "DU", "DES"}

# Un nombre avec séparateur de milliers (espace, espace insécable) : 10 000, 2 500
MOTIF_NOMBRE = r"\d{1,3}(?:[ \u00a0\u202f]\d{3})+|\d+"


def charger_sigles(chemin: Path = FICHIER_SIGLES) -> dict[str, str]:
    """Charge le dictionnaire de prononciation des sigles (vide s'il est absent)."""
    if not chemin.is_file():
        return {}
    with chemin.open(encoding="utf-8") as fichier:
        return json.load(fichier)


def charger_prononciations(chemin: Path = FICHIER_PRONONCIATIONS) -> dict[str, str]:
    """Charge le dictionnaire de prononciation des mots (noms propres, lieux)."""
    return charger_sigles(chemin)


def _en_entier(texte: str) -> int:
    """Convertit '10 000' ou '10\u00a0000' en entier 10000."""
    return int(re.sub(r"[ \u00a0\u202f]", "", texte))


def nombre_en_lettres(nombre: int) -> str:
    """Écrit un entier en toutes lettres, en français (ex. 2025 -> deux mille vingt-cinq)."""
    return num2words(nombre, lang="fr")


def _decimal_en_lettres(partie_entiere: str, partie_decimale: str) -> str:
    """Lit un nombre décimal : '2,45' -> 'deux virgule quarante-cinq'.

    Les zéros initiaux de la partie décimale sont lus un par un
    ('0,05' -> 'zéro virgule zéro cinq').
    """
    zeros = len(partie_decimale) - len(partie_decimale.lstrip("0"))
    reste = partie_decimale.lstrip("0")
    texte = f"{nombre_en_lettres(int(partie_entiere))} virgule"
    texte += " zéro" * zeros
    if reste:
        texte += f" {nombre_en_lettres(int(reste))}"
    return texte


# --- Règles, appliquées dans cet ordre -------------------------------------------------


def _normaliser_dates_completes(texte: str) -> str:
    """'11/10/26' -> 'onze octobre deux mille vingt-six' (jour/mois/année).

    Séparateurs acceptés : / . - (le même des deux côtés).
    Année sur 2 chiffres : 00-49 -> 20xx, 50-99 -> 19xx (hypothèse de ma part).
    """

    def date(m: re.Match) -> str:
        jour, mois, annee = int(m.group(1)), int(m.group(3)), m.group(4)
        if not (1 <= jour <= 31 and 1 <= mois <= 12):
            return m.group(0)
        valeur = int(annee)
        if len(annee) == 2:
            valeur += 2000 if valeur <= 49 else 1900
        premier = "premier" if jour == 1 else nombre_en_lettres(jour)
        return f"{premier} {MOIS[mois - 1]} {nombre_en_lettres(valeur)}"

    motif = r"(?<![\d/.\-])(\d{1,2})([/.\-])(\d{1,2})\2(\d{4}|\d{2})(?![\d/])"
    return re.sub(motif, date, texte)


def _normaliser_dates(texte: str) -> str:
    """'1er mars 2025' -> 'premier mars 2025' ; '3/11' -> 'trois novembre'."""
    texte = re.sub(r"\b1(?:er|ER)\b(?=\s+(?:" + "|".join(MOIS) + r")\b)", "premier", texte)

    def date_numerique(m: re.Match) -> str:
        jour, mois = int(m.group(1)), int(m.group(2))
        if 1 <= jour <= 31 and 1 <= mois <= 12:
            premier = "premier" if jour == 1 else nombre_en_lettres(jour)
            return f"{premier} {MOIS[mois - 1]}"
        return m.group(0)  # pas une date plausible : on laisse la règle des fractions

    return re.sub(r"(?<![\d/])(\d{1,2})/(\d{1,2})(?![\d/])", date_numerique, texte)


def _normaliser_heures(texte: str) -> str:
    """'14 h 30' -> 'quatorze heures trente' ; '11h' -> 'onze heures'."""

    def heure(m: re.Match) -> str:
        h, minutes = int(m.group(1)), m.group(2)
        if h > 24:
            return m.group(0)
        mot = "heure" if h in (0, 1) else "heures"
        resultat = f"{nombre_en_lettres(h)} {mot}"
        if minutes and int(minutes) > 0:
            resultat += f" {nombre_en_lettres(int(minutes))}"
        return resultat

    return re.sub(r"\b(\d{1,2})\s?[hH]\s?(?:(\d{2})\b)?", heure, texte)


def _normaliser_monnaies(texte: str) -> str:
    """'10 000 F CFA' -> 'dix mille francs CFA' ; '5 000 FCFA' idem."""

    def montant(m: re.Match) -> str:
        valeur = _en_entier(m.group(1))
        mot = "franc" if valeur == 1 else "francs"
        return f"{nombre_en_lettres(valeur)} {mot} CFA"

    return re.sub(rf"({MOTIF_NOMBRE})\s?(?:F\s?CFA|FCFA|XOF)\b", montant, texte)


def _normaliser_pourcentages(texte: str) -> str:
    """'52 %' -> 'cinquante-deux pour cent' ; '40,74 %' -> 'quarante virgule soixante-quatorze pour cent'."""

    def pourcent(m: re.Match) -> str:
        entier = m.group(1).replace(",", ".").split(".")
        if len(entier) == 2:
            return _decimal_en_lettres(entier[0], entier[1]) + " pour cent"
        return nombre_en_lettres(int(entier[0])) + " pour cent"

    return re.sub(r"(\d+(?:[.,]\d+)?)\s?%", pourcent, texte)


def _normaliser_ordinaux(texte: str) -> str:
    """'2e' / '15ème' / '46ème' -> 'deuxième' ; '1er' -> 'premier'."""

    def ordinal(m: re.Match) -> str:
        n = int(m.group(1))
        return "premier" if n == 1 else num2words(n, lang="fr", to="ordinal")

    return re.sub(r"\b(\d+)\s?(?:er|ère|e|ème|eme|è)\b", ordinal, texte)


def _normaliser_unites(texte: str) -> str:
    """'2,45GHz' -> 'deux virgule quarante-cinq gigahertz' (unités courantes)."""
    unites = {"GHz": "gigahertz", "MHz": "mégahertz", "kHz": "kilohertz", "Hz": "hertz",
              "dB": "décibels", "mm": "millimètres", "nm": "nanomètres", "km": "kilomètres"}
    motif = "|".join(sorted(unites, key=len, reverse=True))

    def avec_unite(m: re.Match) -> str:
        nombre = m.group(1).replace("−", "-")
        signe = "moins " if nombre.startswith("-") else ""
        nombre = nombre.lstrip("-")
        parties = nombre.replace(",", ".").split(".")
        lettres = (_decimal_en_lettres(parties[0], parties[1]) if len(parties) == 2
                   else nombre_en_lettres(int(parties[0])))
        return f"{signe}{lettres} {unites[m.group(2)]}"

    return re.sub(rf"([−-]?\d+(?:[.,]\d+)?)\s?({motif})\b", avec_unite, texte)


def _normaliser_nombres(texte: str) -> str:
    """Lit les nombres restants : '2 500' -> 'deux mille cinq cents' ; '57,11' -> 'cinquante-sept virgule onze'."""

    def nombre(m: re.Match) -> str:
        brut = m.group(0)
        if "," in brut or "." in brut:
            entier, decimale = re.split(r"[.,]", brut)
            return _decimal_en_lettres(entier, decimale)
        return nombre_en_lettres(_en_entier(brut))

    return re.sub(rf"\d+[.,]\d+|{MOTIF_NOMBRE}", nombre, texte)


def _normaliser_mots(texte: str, mots: dict[str, str]) -> str:
    """Remplace les mots du dictionnaire (insensible à la casse), mots longs d'abord."""
    if not mots:
        return texte
    motif = "|".join(re.escape(m) for m in sorted(mots, key=len, reverse=True))
    table = {m.lower(): v for m, v in mots.items()}
    return re.sub(
        rf"\b(?:{motif})\b",
        lambda m: table[m.group(0).lower()],
        texte,
        flags=re.IGNORECASE,
    )


def _normaliser_sigles(texte: str, sigles: dict[str, str]) -> str:
    """Remplace les sigles : dictionnaire d'abord, sinon épellation lettre par lettre.

    Un mot de 2 à 8 majuscules (ex. 'UFR') est épelé 'U F R'. Les mots usuels
    en majuscules ('LA', 'ET') sont ignorés.
    """

    def sigle(m: re.Match) -> str:
        mot = m.group(0)
        if mot in sigles:
            return sigles[mot]
        if mot in MOTS_MAJUSCULES_A_GARDER:
            return mot
        return " ".join(mot)

    return re.sub(r"\b[A-ZÉÈÀ]{2,8}\b", sigle, texte)


def normaliser_texte(
    texte: str,
    sigles: dict[str, str] | None = None,
    prononciations: dict[str, str] | None = None,
) -> str:
    """Applique toutes les règles de normalisation dans le bon ordre.

    Paramètres :
        texte: texte nettoyé (sortie de cleaner.py).
        sigles: dictionnaire des sigles ; chargé depuis sigles.json si absent.
        prononciations: dictionnaire des mots ; chargé depuis prononciations.json si absent.

    Retourne :
        Le texte prêt à être lu par la synthèse vocale.
    """
    if sigles is None:
        sigles = charger_sigles()
    if prononciations is None:
        prononciations = charger_prononciations()

    texte = texte.replace("\u00a0", " ").replace("\u202f", " ")
    texte = _normaliser_monnaies(texte)       # avant les nombres simples
    texte = _normaliser_dates_completes(texte)  # avant jour/mois
    texte = _normaliser_dates(texte)
    texte = _normaliser_heures(texte)
    texte = _normaliser_pourcentages(texte)
    texte = _normaliser_ordinaux(texte)
    texte = _normaliser_unites(texte)
    texte = _normaliser_nombres(texte)
    texte = _normaliser_mots(texte, prononciations)  # avant les sigles
    texte = _normaliser_sigles(texte, sigles)
    texte = texte.replace("/", " ")           # "/" restant : jamais lu à voix haute
    return re.sub(r"[ \t]+", " ", texte)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage : python -m journal_parle.preprocessing.normalizer "texte à normaliser"')
        sys.exit(1)
    print(normaliser_texte(sys.argv[1]))