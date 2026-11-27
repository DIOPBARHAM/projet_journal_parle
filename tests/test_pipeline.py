from types import SimpleNamespace

import pytest

import journal_parle.pipeline as pipeline


def _preparer_pipeline(monkeypatch, tmp_path, reference):
    reference_path = tmp_path / "reference.txt"
    reference_path.write_text(reference, encoding="utf-8")
    audio_path = tmp_path / "chapter.mp3"
    chapitre_audio = SimpleNamespace(texte_lu=reference_path, mp3=audio_path)

    monkeypatch.setattr(pipeline, "extraire_pages", lambda _: ["page"])
    monkeypatch.setattr(pipeline, "nettoyer_pages", lambda pages: pages)
    monkeypatch.setattr(
        pipeline,
        "segmenter",
        lambda _: [SimpleNamespace(titre="Chapitre 1", phrases=[])],
    )
    monkeypatch.setattr(
        pipeline, "synthetiser_chapitre", lambda *args: chapitre_audio
    )
    monkeypatch.setattr(pipeline, "assembler", lambda *args: tmp_path / "final.mp3")
    return audio_path


def test_evaluer_ignore_un_chapitre_trop_long(monkeypatch, tmp_path):
    _preparer_pipeline(
        monkeypatch, tmp_path, "x" * (pipeline.NB_CARACTERES_EVALUATION + 1)
    )
    monkeypatch.setattr(
        pipeline, "transcrire", lambda _: pytest.fail("ne doit pas transcrire")
    )
    monkeypatch.setattr(
        pipeline, "evaluer_audio", lambda *_: pytest.fail("ne doit pas évaluer")
    )

    resultat = pipeline.executer("document.pdf", evaluer=True, dossier=tmp_path)

    assert resultat.cer is None


def test_evaluer_transcrit_la_reference_complete(monkeypatch, tmp_path):
    reference = "x" * pipeline.NB_CARACTERES_EVALUATION
    audio_path = _preparer_pipeline(monkeypatch, tmp_path, reference)
    resultat_cer = object()
    appels = {}

    def transcrire(audio):
        appels["audio"] = audio
        return "transcription"

    def evaluer_audio(texte_reference, transcription):
        appels["reference"] = texte_reference
        appels["transcription"] = transcription
        return resultat_cer

    monkeypatch.setattr(pipeline, "transcrire", transcrire)
    monkeypatch.setattr(pipeline, "evaluer_audio", evaluer_audio)

    resultat = pipeline.executer("document.pdf", evaluer=True, dossier=tmp_path)

    assert resultat.cer is resultat_cer
    assert appels == {
        "audio": audio_path,
        "reference": reference,
        "transcription": "transcription",
    }


def test_avertissement_est_assemble_en_premier_sans_fausser_le_cer(
    monkeypatch, tmp_path
):
    reference = "texte du vrai chapitre"
    reference_path = tmp_path / "reference.txt"
    reference_path.write_text(reference, encoding="utf-8")
    avertissement_path = tmp_path / "avertissement.txt"
    avertissement_path.write_text("texte de l'annonce", encoding="utf-8")
    audio_reel = SimpleNamespace(texte_lu=reference_path, mp3=tmp_path / "chapitre_01.mp3")
    audio_avertissement = SimpleNamespace(
        texte_lu=avertissement_path, mp3=tmp_path / "chapitre_00.mp3"
    )
    appels_synthese = []
    appels_evaluation = {}
    appels_assemblage = {}

    monkeypatch.setattr(pipeline, "extraire_pages", lambda _: ["page"])
    monkeypatch.setattr(pipeline, "nettoyer_pages", lambda pages: pages)
    monkeypatch.setattr(
        pipeline,
        "segmenter",
        lambda _: [SimpleNamespace(titre="Chapitre 1", phrases=[reference])],
    )

    def synthetiser(chapitre, numero, *_):
        appels_synthese.append((chapitre, numero))
        return audio_avertissement if numero == 0 else audio_reel

    def assembler(chapitres, *_):
        appels_assemblage["chapitres"] = chapitres
        return tmp_path / "final.mp3"

    resultat_cer = object()

    def evaluer_audio(texte_reference, transcription):
        appels_evaluation["reference"] = texte_reference
        appels_evaluation["transcription"] = transcription
        return resultat_cer

    monkeypatch.setattr(pipeline, "synthetiser_chapitre", synthetiser)
    monkeypatch.setattr(pipeline, "assembler", assembler)
    monkeypatch.setattr(pipeline, "transcrire", lambda audio: audio)
    monkeypatch.setattr(pipeline, "evaluer_audio", evaluer_audio)

    resultat = pipeline.executer("document.pdf", evaluer=True, dossier=tmp_path)

    chapitre_avertissement, numero_avertissement = appels_synthese[1]
    assert numero_avertissement == 0
    assert chapitre_avertissement.titre == "Avertissement"
    assert chapitre_avertissement.phrases == [pipeline.TEXTE_AVERTISSEMENT]
    assert appels_assemblage["chapitres"] == [audio_avertissement, audio_reel]
    assert appels_evaluation == {
        "reference": reference,
        "transcription": audio_reel.mp3,
    }
    assert resultat.chapitres == [audio_reel]
    assert resultat.cer is resultat_cer
