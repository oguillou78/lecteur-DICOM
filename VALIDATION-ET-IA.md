# DICOM Clair Pro — Etat vérifiable et validation nécessaire

## Ce qui est réellement livré
- Lecteur de séries SimpleITK/GDCM et vues MPR suivant les axes du volume.
- Assistant pédagogique de vocabulaire et de compte rendu.
- Registre de modèles avec contrôle de manifeste, indications, empreinte SHA-256 et existence de pièces justificatives.
- Blocage systématique de toute détection automatique de fracture, tumeur ou lésion.
- Tests unitaires de géométrie élémentaire et de politique de désactivation clinique.

## Ce qui n'est PAS livré
- Aucun modèle d'inférence diagnostique, aucune pondération et aucune autorisation d'usage clinique.
- Aucune validation clinique, aucun dossier CE/MDR et aucune évaluation de performances.
- Aucun essai confirmé sur Windows 10 ni sur jeux de données DICOM représentatifs.
- La présence de documents dans le manifeste ne prouve pas leur qualité ni leur portée réglementaire.

## Procédure minimale de qualification technique Windows 10
1. Utiliser une machine Windows 10 64 bits avec versions Python et dépendances consignées.
2. Installer les dépendances puis lancer : python -m unittest discover -s tests -v
3. Tester des examens DICOM déidentifiés représentatifs : CT, MR, CR, DX, séries multiframe, syntaxes JPEG/JPEG2000/RLE.
4. Pour chaque cas : vérifier SeriesInstanceUID, nombre et ordre des coupes, orientation patient, PixelSpacing,
   ImagePositionPatient, ImageOrientationPatient, intensités CT après rescale, fenêtre, photométrie MONOCHROME1/2.
5. Comparer géométrie et intensités à un visualiseur de référence indépendant, documenter écarts et tolérances.
6. Vérifier séries obliques, acquisitions irrégulières, coupures, données corrompues, volumes très grands et erreurs explicites.
7. Documenter versions, journaux, captures et résultats signés ; sans cela, ne pas écrire « validé sous Windows ».

## Validation d'une IA médicale par indication
- Définir séparément fracture (localisation et modalité), tumeur (organe et modalité) et lésion (type et organe).
- Vérifier les droits d'utilisation des poids et la possibilité de déployer le modèle dans un logiciel tiers.
- Réaliser évaluation externe indépendante avec labels de référence d'experts, analyses par sous-groupes,
  sensibilité, spécificité, PPV, NPV, faux négatifs et qualité de calibration ; définir les seuils a priori.
- Examiner représentativité des patients/scanners/protocoles, dérive, traçabilité, cybersécurité et confidentialité.
- Evaluer les obligations réglementaires UE (MDR/AI Act selon usage, classification et calendrier).
- La présence d'un dispositif dans une liste d'autorisations FDA ne couvre pas une intégration logicielle tierce.
- Ne jamais faire inférer « absence de maladie » par défaut ; signaler les examens non supportés.

## Confidentialité
- Aucune requête réseau explicite depuis le moteur d'imagerie et l'assistant fournis.
- Les métadonnées peuvent être nominatives ; ne pas publier de captures, logs ou examens de patients.
- Audit réseau et audit de dépendances restent nécessaires avant promesse de confidentialité vérifiée.
