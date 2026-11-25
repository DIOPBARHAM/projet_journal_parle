"""Tests de la segmentation en chapitres et en phrases."""

from journal_parle.preprocessing.segmenter import decouper_en_phrases, segmenter


def test_decoupe_simple():
    assert decouper_en_phrases("Il vient. Elle part ! Où va-t-on ? Ici.") == [
        "Il vient.", "Elle part !", "Où va-t-on ?", "Ici.",
    ]


def test_abreviation_non_coupee():
    assert decouper_en_phrases("Le Prof. Fall est là. Il parle.") == [
        "Le Prof. Fall est là.", "Il parle.",
    ]


def test_pas_de_coupure_avant_minuscule():
    assert decouper_en_phrases("Voir fig. 3 pour le détail.") == ["Voir fig. 3 pour le détail."]


def test_chapitres_detectes():
    corps = "Une phrase assez longue pour dépasser le seuil minimal. " * 6
    texte = f"Chapitre 1 : A\n{corps}\nChapitre 2 : B\n{corps}"
    chapitres = segmenter(texte)
    assert [c.titre for c in chapitres] == ["Chapitre 1 : A", "Chapitre 2 : B"]


def test_texte_sans_titre():
    corps = "Une phrase assez longue pour dépasser le seuil minimal. " * 6
    chapitres = segmenter(corps)
    assert len(chapitres) == 1 and chapitres[0].titre == "Document"


def test_chapitre_court_fusionne():
    corps = "Une phrase assez longue pour dépasser le seuil minimal. " * 6
    texte = f"Chapitre 1 : A\nCourt.\nChapitre 2 : B\n{corps}"
    chapitres = segmenter(texte)
    assert len(chapitres) == 1
    assert chapitres[0].titre == "Chapitre 1 : A"


def test_chapitre_long_coupe():
    phrase = "Une phrase de test assez longue pour remplir le chapitre. "
    texte = "Chapitre 1 : Long\n" + phrase * 300
    chapitres = segmenter(texte)
    assert len(chapitres) > 1
    assert chapitres[0].titre == "Chapitre 1 : Long - partie 1"
    assert all(c.nb_caracteres <= 6000 for c in chapitres)