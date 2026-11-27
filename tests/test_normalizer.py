"""Tests de la normalisation : un cas par piège du sujet."""

import pytest

from journal_parle.preprocessing.normalizer import normaliser_texte

SIGLES = {"UCAD": "ucade", "MESRI": "mesri"}


@pytest.mark.parametrize(
    "entree, attendu",
    [
        ("Le 1er mars 2025", "Le premier mars deux mille vingt-cinq"),
        ("la réunion du 3/11", "la réunion du trois novembre"),
        ("à 14 h 30", "à quatorze heures trente"),
        ("10 000 F CFA", "dix mille francs C F A"),
        ("52 %", "cinquante-deux pour cent"),
        ("le 2e lundi", "le deuxième lundi"),
        ("2 500 bourses", "deux mille cinq cents bourses"),
        ("l'UCAD", "l'ucade"),
        ("l'UFR", "l'U F R"),
        ("à 2,45GHz", "à deux virgule quarante-cinq gigahertz"),
    ],
)
def test_pieges_du_sujet(entree, attendu):
    assert normaliser_texte(entree, SIGLES) == attendu


def test_phrase_sans_piege_inchangee():
    phrase = "Les étudiants déposent leur dossier."
    assert normaliser_texte(phrase, SIGLES) == phrase


@pytest.mark.parametrize(
    "entree, attendu",
    [
        ("le 11/10/26", "le onze octobre deux mille vingt-six"),
        ("le 1/3/2025", "le premier mars deux mille vingt-cinq"),
        ("le 15.04.2024", "le quinze avril deux mille vingt-quatre"),
    ],
)
def test_dates_completes(entree, attendu):
    assert normaliser_texte(entree, SIGLES, {}) == attendu


def test_nom_en_majuscules_non_epele():
    assert normaliser_texte("Momar NDIAYE", SIGLES, {"Ndiaye": "Ndiaï"}) == "Momar Ndiaï"


def test_slash_restant_non_lu():
    assert "/" not in normaliser_texte("SOACHIM/SN", SIGLES, {})