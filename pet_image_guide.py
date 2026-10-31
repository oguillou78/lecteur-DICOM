"""Offline, non-diagnostic PET/CT image guide. Never identifies cancers from pixels."""
from collections import Counter
from pathlib import Path
import math

INTRO = (
    'EXPLORATION AVANT COMPTE RENDU — INFORMATIONS TECHNIQUES UNIQUEMENT\n'
    'Le logiciel ne localise pas les tumeurs, ne détecte pas de métastases, ne classe pas le cancer '
    'et ne déduit pas un diagnostic des zones lumineuses. Une image sans foyer évident ne permet '
    'pas non plus d’exclure une anomalie.\n'
)
EXPLANATIONS = {
    'PT': 'La TEP montre la répartition du radiotraceur. Une forte fixation peut notamment être physiologique, inflammatoire, infectieuse ou tumorale.',
    'PET': 'La TEP montre la répartition du radiotraceur. Une forte fixation ne signifie pas automatiquement cancer.',
    'CT': 'Le scanner montre des structures anatomiques. Certains CT de TEP servent surtout à la correction d’atténuation et ne remplacent pas nécessairement un scanner diagnostique.',
}
CHECKS = [
    'Gencive et mâchoire : demander la localisation exacte et la correspondance anatomique.',
    'Cou : demander si des ganglions nécessitent un commentaire ou des examens complémentaires.',
    'Autres régions : demander quelles constatations sont pertinentes pour votre situation.',
    'Demander si les soins dentaires, une infection ou une intervention récente peuvent influencer la fixation.',
    'Demander comment l’examen s’intègre aux résultats de biopsie et aux autres examens.'
]


def study_inventory(series):
    counts = Counter(str(getattr(s, 'modality', '')).upper() for s in series)
    pt = counts['PT'] + counts['PET']
    ct = counts['CT']
    total = len(series)
    lines = [INTRO, f'Inventaire : {total} série(s), dont {pt} TEP (PT) et {ct} scanner (CT).']
    if pt == 0:
        lines.append('Aucune série TEP identifiée : vérifier que le téléchargement comprend les images originales DICOM PET.')
    if ct == 0:
        lines.append('Aucune série CT identifiée : vérifier la présence du scanner dans le dossier complet.')
    if pt and ct:
        lines.append('Les deux modalités sont présentes, mais leur correspondance spatiale n’est pas vérifiée. Pas de fusion PET/CT dans ce module.')
    lines.append('Une série peut être un repérage, une reconstruction ou une acquisition de plusieurs parties du corps : ne pas compter les séries comme des lésions.')
    return '\n'.join(lines)


def describe_selected(series, dataset=None, image=None, array=None):
    """Return source-tagged metadata only; do not assign anatomical meaning to image brightness."""
    modality = str(getattr(series, 'modality', '')).upper()
    lines = [INTRO, f'Série choisie : {str(getattr(series, "description", "Sans description"))[:150]}',
             f'Modalité déclarée : {modality or "inconnue"}',
             f'Fichiers de la série : {len(getattr(series, "files", []))}',
             EXPLANATIONS.get(modality, 'Type d’acquisition non reconnu : interprétation des pixels impossible.')]
    if dataset is not None:
        def field(name):
            v = dataset.get(name, None)
            if v is None or str(v).strip() == '': return None
            return str(v)[:110]
        for k, label in [
            ('StudyDate','Date de l’examen (métadonnée)'),
            ('SeriesDescription','Description de la série'),
            ('Radiopharmaceutical','Radiotraceur déclaré'),
            ('Units','Unités déclarées des pixels'),
            ('CorrectedImage','Corrections déclarées'),
            ('DecayCorrection','Correction de décroissance'),
            ('ReconstructionMethod','Méthode de reconstruction'),
            ('ImageType','Type d’image')]:
            v = field(k)
            if v: lines.append(f'{label} : {v}')
        if modality in ('PT','PET'):
            units = field('Units') or 'non renseignées'
            if units.upper() == 'GML':
                lines.append('Unité GML annoncée : peut représenter un SUV sous certaines conditions, sans validation quantitative ici.')
            else:
                lines.append(f'Unités de TEP : {units}. Les valeurs numériques ne seront PAS présentées comme des SUV.')
            lines.append('Aucun calcul de SUV/SUVmax : il nécessite des métadonnées complètes, des corrections et une validation des conversions.')
    if image is not None:
        try:
            size = tuple(image.GetSize())
            spacing = tuple(round(float(v), 2) for v in image.GetSpacing())
            lines.append(f'Volume chargé : {size} voxels (X,Y,Z) ; espacement déclaré : {spacing} mm.')
        except (AttributeError, TypeError, ValueError):
            pass
    if array is not None:
        try:
            import numpy as np
            vals = np.asarray(array)
            finite = vals[np.isfinite(vals)]
            if finite.size:
                lo, hi = np.percentile(finite[::max(1, finite.size//100000)], [2,98])
                if math.isfinite(float(lo)) and math.isfinite(float(hi)):
                    lines.append(f'Plage 2–98 % des intensités numériques : {lo:.2f} à {hi:.2f} (unités non validées).')
                    lines.append('Cette plage décrit le signal du fichier, pas une tumeur ni une probabilité de cancer.')
        except (ImportError, ValueError, TypeError):
            pass
    lines.append('\nÀ demander au médecin :\n' + '\n'.join('• '+q for q in CHECKS))
    return '\n'.join(lines)


def safe_read_header(path):
    """Read a DICOM header only (pixel data excluded), never export patient identity."""
    import pydicom
    ds=pydicom.dcmread(str(Path(path)), stop_before_pixels=True, force=False)
    return ds
