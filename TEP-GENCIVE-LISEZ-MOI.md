# DICOM Clair Pro — TEP-scan / cancer de la gencive

Cette adaptation est **pédagogique**, sans analyse visuelle par IA ni dispositif médical certifié.

## Ce qui est disponible
- Détection, dans l'inventaire des séries DICOM, des modalités PT et CT.
- Un onglet « TEP gencive » permettant de coller le compte rendu de médecine nucléaire.
- Regroupement **d'extraits exacts** du texte du compte rendu : bouche, mâchoire, ganglions cervicaux, autres sites, SUV, conclusion.
- Questions préparatoires à la consultation et mini-glossaire.
- Fonctionnement local du code Python (pas d'appel réseau dans le traitement des comptes rendus).

## Ce qui n'est PAS disponible
- Fusion spatiale PET/CT (la co-registration est à développer et vérifier).
- Calcul SUV fiable, segmentation de tumeur, diagnostic ou stade TNM.
- Détection automatique de métastases ou interprétation clinique.
- Preuve de validation Windows 10 ou de conformité réglementaire.

## Utilisation
1. Lire LISEZ-MOI.txt pour construire l'application Windows. Aucun installateur EXE compilé n'est fourni.
2. Utiliser « Ouvrir un dossier DICOM » sur l'export intégral de l'examen (CT et PT).
3. Ouvrir l'onglet « TEP gencive » et consulter le bilan des séries.
4. Coller le compte rendu **en retirant les données identifiantes**, cliquer sur « Expliquer les mentions ».
5. Confronter la synthèse avec la conclusion originale et l'équipe de médecine nucléaire / oncologie ORL.

Important : une hyperfixation FDG peut être d'origine inflammatoire, et un TEP-scan négatif ne garantit pas l'absence de maladie. La valeur SUV ne correspond pas à une probabilité de cancer.
