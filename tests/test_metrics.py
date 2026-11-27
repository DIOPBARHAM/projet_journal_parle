"""Tests du calcul du CER."""

import pytest

from journal_parle.evaluation.metrics import (
    ErreurEvaluation,
    calculer_cer,
    preparer_pour_comparaison,
)


def test_substitution():
    r = calculer_cer("chat", "chut")
    assert (r.substitutions, r.suppressions, r.insertions, r.total_reference) == (1, 0, 0, 4)
    assert r.cer == pytest.approx(0.25)


def test_insertion():
    assert calculer_cer("chat", "chats").insertions == 1


def test_suppression():
    assert calculer_cer("chat", "cat").suppressions == 1


def test_textes_identiques():
    assert calculer_cer("bonjour", "bonjour").cer == 0


def test_reference_vide():
    with pytest.raises(ErreurEvaluation):
        calculer_cer("", "abc")


def test_preparation():
    assert preparer_pour_comparaison("L'UCAD, ouvre !") == "l ucad ouvre"