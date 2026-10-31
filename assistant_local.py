"""Privacy-preserving deterministic education assistant; NOT diagnostic AI."""
import re

GLOSSARY={
 'scanner':'Le scanner (TDM/CT) utilise des rayons X pour créer des images en coupe.',
 'irm':'L’IRM utilise un champ magnétique et des ondes radio pour créer des images.',
 'radiographie':'La radiographie utilise des rayons X pour représenter une projection.',
 'fenêtre':'La fenêtre (Window/Level) règle l’affichage des niveaux de gris sans modifier les données originales.',
 'mpr':'La reconstruction multiplanaire (MPR) présente le volume sous différents plans. La précision dépend de la qualité et de l’espacement des coupes.',
 'contraste':'Un produit de contraste peut aider à distinguer certains tissus. Son usage doit être confirmé dans le dossier médical.',
 'dicom':'DICOM est un standard de fichiers et d’échange des images médicales, avec des métadonnées sur l’acquisition.',
 'hu':'En scanner, les unités Hounsfield (HU) expriment l’atténuation radiologique, lorsque les données ont été correctement converties.',
}

DISCLAIMER='Information pédagogique uniquement — aucune interprétation diagnostique. Consultez votre radiologue ou médecin.'


def explain(question, modality='', description='', context=''):
    q=(question or '').strip().lower()
    matches=[value for key,value in GLOSSARY.items() if key in q]
    if any(x in q for x in ['cancer','tumeur','fracture','infection','maladie','anormal','diagnostic','grave','lésion']):
        return ('Je ne peux pas confirmer ni exclure une anomalie ou une maladie sur ces images. '
                'Une conclusion exige une interprétation radiologique tenant compte de toutes les séquences, '
                'du contexte clinique et du compte rendu.\n\n'+DISCLAIMER)
    if not matches:
        return (f'Série chargée : {modality or "inconnue"}, {description or "sans description"}.\n'
                'Je peux expliquer les termes DICOM, les vues axiale/coronale/sagittale, '
                'le fenêtrage, ou résumer un compte rendu collé ci-dessous.\n\n'+DISCLAIMER)
    return '\n\n'.join(matches)+'\n\n'+DISCLAIMER


def summarize_report(report):
    t=(report or '').strip()
    if not t: return 'Collez un compte rendu rédigé par un professionnel pour en obtenir une synthèse fidèle.'
    if len(t)>20000: return 'Compte rendu trop long : limite de 20 000 caractères.'
    # Extract the author's conclusion only; no generative model, no added diagnosis.
    match=re.search(r'(?im)^\s*(?:conclusion|impression|synthèse)\s*[:\-]?\s*(.*)$',t)
    if match:
        rest=t[match.end():]
        stop=re.search(r'(?im)^\s*(?:signature|radiologue|médecin|technique|indication|résultat(?:s)?)\s*:',rest)
        content=(match.group(1)+'\n'+rest[:stop.start()] if stop else match.group(1)+'\n'+rest).strip()
        content=content[:2500]
        return ('**Conclusion extraite du compte rendu fourni (texte original, non reformulé)**\n\n'
                + content + '\n\n**Attention :** vérifiez cette extraction avec le document original.\n'+DISCLAIMER)
    return ('Aucune rubrique « Conclusion » ou « Impression » clairement identifiée. '
            'Pour éviter une synthèse trompeuse, aucun diagnostic n’est déduit automatiquement. '
            'Demandez au radiologue de vous expliquer le document.\n\n'+DISCLAIMER)
