"""Oncology workflow: educational only; no pixel-based malignancy inference.

This deliberately does not run a clinical model. A detected mass is not equivalent
 to a confirmed malignancy and no negative result may rule out cancer.
"""
from dataclasses import dataclass

SUPPORTED_TARGETS = {
    'Poumon — scanner thoracique': ('CT', 'poumon', 'nodule ou masse pulmonaire'),
    'Cerveau — IRM': ('MR', 'cerveau', 'lésion intracrânienne'),
    'Foie — scanner ou IRM': (None, 'foie', 'lésion hépatique'),
    'Sein — mammographie': ('MG', 'sein', 'anomalie mammaire'),
    'Autre localisation': (None, None, 'anomalie'),
}

@dataclass(frozen=True)
class OncologyAssessment:
    target: str
    exam_modality: str
    status: str
    clinical_inference_performed: bool
    text: str


def assess_readiness(target, modality, model_registry=None):
    if target not in SUPPORTED_TARGETS:
        raise ValueError('Localisation non reconnue.')
    expected_modality, anatomy, lesion = SUPPORTED_TARGETS[target]
    modality = (modality or '').upper().strip()
    if expected_modality and modality and expected_modality != modality:
        return OncologyAssessment(target, modality, 'EXAMEN HORS PÉRIMÈTRE', False,
            f'Ce protocole vise la modalité {expected_modality}, alors que la série chargée est {modality}. '
            'Aucune détection ni conclusion ne peut être produite.')
    return OncologyAssessment(target, modality, 'IA CLINIQUE NON DISPONIBLE', False,
        f'Cible pédagogique : {lesion}. Aucun modèle de détection de tumeur n’est livré, '
        'entraîné ou validé dans cette version. Il est impossible de localiser ou de qualifier '
        'automatiquement une anomalie, ou d’exclure un cancer. Une suspicion sur imagerie '
        'ne prouve pas la malignité ; une biopsie et une analyse anatomopathologique peuvent être nécessaires. '
        'Faites interpréter les examens par un professionnel de santé.')


def interpretation_boundary():
    return ('Aucune conclusion diagnostique. Le logiciel ne détermine ni présence ni absence '
            'de cancer, ni stade, ni bénignité/malignité, ni décision de traitement.')
