from pathlib import Path
from types import SimpleNamespace

import main


def test_main_transmet_le_pdf_et_l_option_cer(monkeypatch, tmp_path, capsys):
    liste_chapitres = tmp_path / "chapitres.txt"
    liste_chapitres.write_text("00:00  Avertissement", encoding="utf-8")
    resultat_cer = SimpleNamespace(cer=0.034)
    resultat = SimpleNamespace(
        mp3_final=Path("outputs/journal_parle.mp3"),
        liste_chapitres=liste_chapitres,
        cer=resultat_cer,
    )
    appels = {}

    def executer(pdf, evaluer, progression):
        appels["pdf"] = pdf
        appels["evaluer"] = evaluer
        appels["progression"] = progression
        progression(0.5, "Synthèse")
        return resultat

    monkeypatch.setattr(main, "executer", executer)
    monkeypatch.setattr(main.sys, "argv", ["main.py", "document.pdf", "--cer"])

    assert main.main() == 0

    assert appels["pdf"] == "document.pdf"
    assert appels["evaluer"] is True
    assert capsys.readouterr().out == (
        "[ 50%] Synthèse\n"
        "MP3 final : outputs\\journal_parle.mp3\n"
        "00:00  Avertissement\n"
        "CER (chapitre 1) : 3.4%\n"
    )


def test_main_affiche_usage_sans_pdf(monkeypatch, capsys):
    monkeypatch.setattr(main.sys, "argv", ["main.py"])

    assert main.main() == 1
    assert capsys.readouterr().out == (
        'Usage : python -X utf8 main.py "document.pdf" [--cer]\n'
    )
