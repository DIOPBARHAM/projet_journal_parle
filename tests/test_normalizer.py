"""Tests de la normalisation : un cas par piège du sujet."""

import pytest

from journal_parle.preprocessing.normalizer import normaliser_texte

SIGLES = {"UCAD": "oucade", "MESRI": "mesri"}


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
        ("l'UCAD", "l'oucade"),
        ("l'UFR", "l'U F R"),
        ("à 2,45GHz", "à deux virgule quarante-cinq gigahertz"),
    ],
)
def test_pieges_du_sujet(entree, attendu):
    assert normaliser_texte(entree, SIGLES) == attendu


def test_phrase_sans_piege_inchangee():
    phrase = "Les étudiants déposent leur dossier."
    assert normaliser_texte(phrase, SIGLES) == phrase