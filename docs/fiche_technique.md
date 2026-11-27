# Fiche technique : Journal parlé (P2)

## Outils et justification

| Besoin | Outil | Justification |
|---|---|---|
| Lecture PDF | PyMuPDF | Extraction rapide du texte natif. |
| Voix | Edge TTS (`fr-FR-DeniseNeural`) | Voix neurale française, gratuite, sans GPU ni clé ; Internet requis, service non officiel. |
| Audio | Pydub + FFmpeg | Assemblage MP3 et chapitres en métadonnées. |
| ASR | faster-whisper `small`, VAD | Compromis qualité/vitesse CPU ; le VAD réduit les hallucinations sur silences. |
| Métrique | Jiwer | CER = `(S + D + I) / N`. |
| Interface | Gradio | Interface web, partageable depuis le notebook Colab. |

## Normalisation

Dates (`1er`, `3/11`, `11/10/26`), heures, nombres, pourcentages, unités,
ordinaux, sigles (dictionnaire et épellation) et noms propres (dictionnaire).
**34 tests automatiques** couvrent notamment ces règles.

## Mesures

Mesure unique v1 (`mesure-finale-v1`) sur des PDF non utilisés pour le réglage,
avec Whisper `small` et nombres normalisés des deux côtés. L'extrait prend des
phrases entières jusqu'à environ 3 000 caractères ; la dernière peut dépasser
le seuil, d'où les valeurs `N` ci-dessous.

| Document | CER | N |
|---|---:|---:|
| Rapport public 2007 | 2,99 % | 3 816 |
| Infolettre 8e édition (même famille que le PDF de développement) | 3,34 % | 3 235 |

La v2 (dates complètes, noms propres) n'a pas été remesurée sur un PDF neuf. Le
CER compare la transcription au **texte lu normalisé**, pas au texte brut du PDF :
ce n'est donc pas une comparaison directe au document d'origine.

Écoute rapportée : « Ndiaï » est bien prononcé. Sur un PDF, l'A/B favorise
l'épellation « C F A » (CER 4,54 %) à « céfa » (6,27 %), mais Whisper la
retranscrit aussi « Français, phas » : résultat indicatif, à confirmer à l'écoute.
L'annonce est explicite et en tête (00:00 ; chapitre 1 à 00:06) ; son texte et
son placement sont vérifiés, pas son intonation subjective.

## Limites constatées

- Noms propres/toponymes sénégalais (Ziguinchor, Pikine, Kolda) : erreurs
  fréquentes ; pluriels inaudibles et variantes orthographiques gonflent aussi
  le CER sans forcément indiquer un défaut audio.
- Whisper peut halluciner sur les silences (« sous-titres Amara.org ») ; le VAD
  réduit ce risque sans le supprimer. Titres accolés et en-têtes variables
  parfois mal détectés ; aucun OCR pour les PDF scannés.
- Mesure sur un extrait, non le document entier, et sur le texte lu normalisé,
  non le PDF brut. Le test A/B porte sur un seul document.
- Colab utilise Python 3.13 : le notebook installe `audioop-lts` et
  `av==18.0.0`.
