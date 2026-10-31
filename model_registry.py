"""Strict policy gate for future clinical inference plugins.

No AI weights are shipped. A regulatory authorization of another product or model
is not transferable to this software. Validation and licensing are per integration.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

class ClinicalModelUnavailable(RuntimeError):
    pass

@dataclass(frozen=True)
class ClinicalModelManifest:
    name: str
    version: str
    indication: str
    modality: str
    anatomy: str
    weights_sha256: str
    validation_report: str
    regulatory_evidence: str
    approved_for_local_deployment: bool
    expected_input: str

REQUIRED = set(ClinicalModelManifest.__dataclass_fields__)

def verify_model_manifest(path, weights_path, exam_modality, exam_anatomy):
    """Verify basic gate prerequisites; NOT proof of clinical validity.

    Real deployment additionally requires independent evidence review, clinical
    evaluation, test datasets, licensing, quality management and expert signoff.
    """
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if set(data) != REQUIRED:
        raise ClinicalModelUnavailable('Manifeste incomplet ou avec champs inconnus.')
    m = ClinicalModelManifest(**data)
    if not m.approved_for_local_deployment:
        raise ClinicalModelUnavailable('Module non autorisé pour un déploiement local.')
    if not m.validation_report or not Path(m.validation_report).is_file():
        raise ClinicalModelUnavailable('Rapport de validation indépendant absent.')
    if not m.regulatory_evidence or not Path(m.regulatory_evidence).is_file():
        raise ClinicalModelUnavailable('Justificatif réglementaire absent.')
    if m.modality.upper() != exam_modality.upper() or m.anatomy.lower() != exam_anatomy.lower():
        raise ClinicalModelUnavailable('Modalité ou anatomie hors indication du module.')
    if not Path(weights_path).is_file():
        raise ClinicalModelUnavailable('Poids du modèle absents.')
    h = hashlib.sha256()
    with open(weights_path, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    if h.hexdigest() != m.weights_sha256.lower():
        raise ClinicalModelUnavailable('Intégrité du modèle non vérifiée.')
    return m

def run_detection(*args, **kwargs):
    """Fail closed: no validated clinical inference backend is bundled."""
    raise ClinicalModelUnavailable(
        'Détection automatique indisponible : aucun modèle clinique validé '
        'et intégré à cette installation. Ne pas utiliser pour le diagnostic.'
    )
