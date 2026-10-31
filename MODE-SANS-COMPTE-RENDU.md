# DICOM Clair Pro — Découvrir son TEP-scan avant le compte rendu

## Utilisation
1. Téléchargez les fichiers d'imagerie **DICOM originaux** du centre d'imagerie (l'ensemble des dossiers, pas uniquement des captures JPG ou PDF).
2. Dans DICOM Clair Pro, ouvrez le dossier contenant les fichiers DICOM.
3. Choisissez une série « PT » (TEP) ou « CT » (scanner) dans la liste de gauche.
4. Dans l'onglet « TEP gencive », cliquez sur **Explorer les images SANS compte rendu**.
5. Lisez les métadonnées, les limites et les questions utiles ; naviguez dans les images via les vues du centre.

## Important
Le logiciel **ne désigne pas les tumeurs, les métastases ou des ganglions anormaux**. Il ne permet pas de dire si le cancer s'est étendu, ni de définir un stade TNM, ni de déduire l'absence de maladie.

La TEP présente des fixations du traceur (souvent FDG) qui peuvent être dues à de nombreux processus, y compris inflammations, infections et activité physiologique. Un affichage visuel plus brillant est aussi influencé par les réglages d'affichage. Même le SUV doit être calculé et interprété dans un contexte médical approprié ; cette version refuse de le calculer sans validation complète.

**Pas de fusion PET/CT anatomiquement validée** ; chaque série est affichée séparément. Les axes des reconstructions MPR ne sont pas réorientés en repère anatomique canonique. Ne pas utiliser pour localiser cliniquement une fixation ou conduire un soin.

Aucune transmission réseau n'est réalisée par le code applicatif. L'environnement Windows et l'installateur restent à auditer pour une promesse de confidentialité complète.

## Installation
Le ZIP contient les **sources**, non un installateur EXE compilé. Sur Windows 10, installer Python 3.11 ou 3.12 et Inno Setup, puis lancer `CONSTRUIRE-WINDOWS.bat`. Le script télécharge les dépendances et crée une version `dist` et éventuellement un installateur. La compatibilité Windows complète reste à tester sur machine réelle.

## Validation à faire avant exploitation étendue
Tester des séries TEP/CT anonymisées sur Windows 10, confirmer la fidélité des pixels et des unités, vérifier les cas multiframe et compressés, le comportement sur gros volumes et les messages d'erreur. Aucun modèle de segmentation/détection oncologique n'est fourni, entraîné ni validé cliniquement.
