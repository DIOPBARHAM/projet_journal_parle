# Journal parlé

Convertit un document PDF en fichier audio MP3 avec chapitres, pour rendre
des documents accessibles aux personnes qui lisent difficilement ou qui
écoutent en se déplaçant. Projet P2 du cours IA Voix et Vidéo.

> **Contenu synthétique** : l'audio est généré par une voix artificielle
> (Edge TTS). Une annonce l'indique au début de chaque MP3.

## Pipeline

```text
PDF
 -> extraction du texte (PyMuPDF)
 -> nettoyage des en-têtes, pieds de page et numéros de page
 -> segmentation en chapitres et phrases
 -> normalisation pour la lecture (nombres, dates, sigles et prononciations)
 -> synthèse vocale (Edge TTS)
 -> assemblage audio et marqueurs de chapitres (Pydub + FFmpeg)
 -> MP3
 -> [optionnel] transcription Whisper et calcul du CER (Jiwer)
```

Le chapitre d'annonce est assemblé en premier et n'est pas inclus dans le texte
de référence utilisé pour calculer le CER.

## Installation

Prérequis : Python 3.10 à 3.12 (testé avec Python 3.12), FFmpeg accessible
depuis le `PATH` et une connexion Internet pour Edge TTS et le premier
téléchargement du modèle Whisper. Le GPU n'est pas nécessaire ; il peut
accélérer Whisper.

```bash
git clone https://github.com/DIOPBARHAM/projet_journal_parle.git
cd projet_journal_parle
python -m venv .venv
```

Active ensuite l'environnement virtuel avec la commande correspondant à ton
système :

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux ou macOS
source .venv/bin/activate
```

Puis installe les dépendances et vérifie l'environnement :

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python scripts/check_setup.py
```

Le script de vérification contrôle la version de Python, les bibliothèques
requises et la disponibilité de FFmpeg.

## Utilisation

- **Interface web** : `python -X utf8 app.py`, puis ouvrir
  <http://127.0.0.1:7860>.
- **Ligne de commande** : `python -X utf8 main.py "document.pdf" [--cer]`.
  L'option `--cer` demande une évaluation du premier vrai chapitre ; elle est
  ignorée si celui-ci dépasse 3 000 caractères.
- **Google Colab** : ouvrir [`notebooks/demo_colab.ipynb`](notebooks/demo_colab.ipynb)
  et exécuter les cellules. Un GPU est conseillé pour accélérer Whisper.
- **Tests** : `python -m pytest tests/ -v`.

Par défaut, les fichiers de sortie sont
`outputs/pipeline/journal_parle.mp3` et `outputs/pipeline/chapitres.txt`.

## Mesure (CER)

Le CER (Character Error Rate) est calculé ainsi : `(S + D + I) / N`, où `S`,
`D` et `I` désignent substitutions, suppressions et insertions, et `N` le
nombre de caractères de référence. Le calcul compare le texte lu à la
transcription Whisper `small` (filtre VAD activé), après normalisation.

Mesure historique unique sur les PDF de test, jamais utilisés pour le réglage,
avec la version de normalisation v1. L'extrait est constitué de phrases entières
prises dans l'ordre jusqu'au seuil de 3 000 caractères ; la dernière phrase
peut faire dépasser ce seuil. La mesure a été enregistrée sous le tag
`mesure-finale-v1` ; les détails sont dans
[`docs/mesure_finale.json`](docs/mesure_finale.json).

| Document | CER |
|---|---:|
| Rapport public (2007) | 2,99 % |
| Infolettre (8e édition) | 3,34 % |

Les règles de normalisation ont évolué depuis cette mesure (v2) ; ces résultats
décrivent la version v1 et ne constituent pas une mesure de la version actuelle.

## Limites connues

- Les noms propres et toponymes sénégalais peuvent être mal prononcés ; le
  dictionnaire [`prononciations.json`](src/journal_parle/preprocessing/prononciations.json)
  est à enrichir.
- Les titres accolés à un paragraphe ne sont pas toujours détectés et les
  en-têtes variables ne sont pas toujours supprimés.
- Edge TTS nécessite Internet, n'est pas une API officielle et peut évoluer.
- Les PDF scannés ne sont pas pris en charge : le projet ne fait pas d'OCR.
- Les dates sont lues au format jour/mois/année ; les sigles inconnus sont
  épelés.

## Sources des données

- `data/dev/exemple_synthetique.pdf` est un exemple généré par
  [`scripts/make_sample_pdf.py`](scripts/make_sample_pdf.py).
- `data/dev/infolettre_5e_edition.pdf` est une copie d'un bulletin de la
  Faculté des Sciences et Techniques de l'UCAD (FST-UCAD), mentionnant son
  Service d'Accueil, d'Information et de la Communication. Le document renvoie
  au site `www.fst.ucad.sn` ; l'URL de téléchargement de cette copie et sa
  licence de réutilisation n'ont pas été vérifiées.
- `data/test/test_infolettre_8e_edition.pdf` est un bulletin FST-UCAD. Il
  contient des références à `www.fst.ucad.sn` et
  `https://editions.ucad.sn/ouvrages/122`, mais l'origine de cette copie PDF et
  sa licence de réutilisation n'ont pas été vérifiées.
- `data/test/rapport_public_2007.pdf` se présente comme une synthèse du rapport
  public 2007 de la Cour des comptes du Sénégal. L'URL d'origine et la licence
  de réutilisation de cette copie n'ont pas été vérifiées.

Les PDF de bulletins et de test sont des fichiers locaux exclus de Git tant que
leurs droits de réutilisation ne sont pas établis. Ils ne sont donc pas inclus
dans un clone du dépôt.

## Éthique

Aucune voix n'est clonée ni destinée à imiter une personne réelle. La voix
utilisée est synthétique (Edge TTS) ; le caractère synthétique est signalé dans
l'interface et au début de l'audio.
