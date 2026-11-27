"""Interface Gradio du Journal parlé.

Lancer : python -X utf8 app.py
"""

from __future__ import annotations

import gradio as gr

from journal_parle.pipeline import ErreurPipeline, executer
from journal_parle.tts.tts_engine import VOIX_PAR_DEFAUT

VOIX = ["fr-FR-DeniseNeural", "fr-FR-EloiseNeural", "fr-FR-HenriNeural"]

MENTION = (
    "**Contenu synthétique** : cet audio est généré par une voix artificielle "
    "(Edge TTS) à partir du texte du document."
)


def convertir(fichier, voix, evaluer, progression=gr.Progress()):
    """Appelée par le bouton : retourne (mp3, chapitres, message)."""
    if fichier is None:
        return None, "", "Dépose d'abord un fichier PDF."
    try:
        resultat = executer(
            fichier,
            voix=voix,
            evaluer=evaluer,
            progression=lambda f, m: progression(f, desc=m),
        )
    except ErreurPipeline as erreur:
        return None, "", f"Erreur : {erreur}"

    chapitres = resultat.liste_chapitres.read_text(encoding="utf-8")
    message = "Conversion terminée."
    if evaluer:
        if resultat.cer is None:
            message += " CER non calculé : le chapitre 1 dépasse 3 000 caractères."
        else:
            message += f" CER (chapitre 1, Whisper small) : {resultat.cer.cer:.1%}."
    return str(resultat.mp3_final), chapitres, message


with gr.Blocks(title="Journal parlé") as demo:
    gr.Markdown("# Journal parlé\nConvertit un PDF en audio MP3 avec chapitres.")
    gr.Markdown(MENTION)
    entree = gr.File(label="Document PDF", file_types=[".pdf"], type="filepath")
    voix = gr.Dropdown(VOIX, value=VOIX_PAR_DEFAUT, label="Voix")
    evaluer = gr.Checkbox(label="Calculer le CER (plus lent)", value=False)
    bouton = gr.Button("Convertir", variant="primary")
    message = gr.Textbox(label="Statut", interactive=False)
    audio = gr.File(label="MP3 final (téléchargement)")
    chapitres = gr.Textbox(
        label="Chapitres (horodatages)", lines=8, interactive=False
    )
    bouton.click(convertir, [entree, voix, evaluer], [audio, chapitres, message])


if __name__ == "__main__":
    demo.launch()
