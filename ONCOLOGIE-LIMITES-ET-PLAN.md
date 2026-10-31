# Module oncologie — périmètre et limites

Cette version apporte un onglet **Oncologie** et une vérification explicite de la modalité, **pas une détection de cancer**. Elle fonctionne sans connexion réseau pour ses fonctions natives. Aucun modèle préentraîné, validé ou autorisé n'est inclus.

## Pourquoi un module spécialisé

Une détection de nodules sur scanner thoracique ne valide ni la détection de tumeurs cérébrales sur IRM, ni la classification bénin/malin. Il faut choisir une indication clinique, un protocole d'acquisition et une population cible précis.

## Feuille de route avant une IA de détection

1. Définir organe, modalité, séquence et population, ainsi que la tâche exacte (localisation, segmentation, catégorisation, etc.).
2. Choisir un modèle et vérifier licence, provenance, compatibilité des données et version des poids. Vérifier séparément le statut réglementaire du dispositif *intégré*.
3. Valider l'orientation DICOM, le spacing, les transformations de pixels et les séries multi-fichiers sur une batterie de cas annotés, y compris DICOM compressé et études atypiques.
4. Évaluation indépendante stratifiée (établissements, fabricants, sous-populations), sensibilité, spécificité, VPP, VPN, courbes ROC/PR, calibration, faux positifs et faux négatifs.
5. Tests Windows 10 réels sur des machines cibles, installateur signé, reproductibilité de build, audit sécurité et protection des données personnelles.
6. Étudier obligations CE/MDR, RGPD et cybersécurité avant toute utilisation médicale ou commercialisation.

## Garde-fous

Aucun modèle n'est installé. Le bouton vérifie une éligibilité de principe et n'analyse aucun pixel. Une réponse « IA clinique non disponible » ne doit jamais être assimilée à une imagerie normale. Aucun diagnostic, triage ou exclusion de cancer n'est possible avec cette version.

Sources générales : National Cancer Institute — https://www.cancer.gov/about-cancer/diagnosis-staging/diagnosis ; FDA — https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/list-artificial-intelligence-enabled-medical-devices
