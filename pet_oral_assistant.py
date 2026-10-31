"""Non-diagnostic, local PET/CT education for oral-cavity cancer.

Never infers disease, nodal involvement, metastasis, stage or SUV from pixels.
"""
import re
from collections import Counter

LIMIT = ('Ce module explique un compte rendu médical, sans analyser la malignité des images. '
         'Une fixation FDG ou une valeur SUV ne prouve pas à elle seule un cancer. '
         'L’interprétation revient au médecin de médecine nucléaire et à l’équipe soignante.')

GLOSSARY = {
    'TEP / PET': 'Tomographie par émission de positons : visualise la distribution d’un radiotraceur.',
    'TDM / CT': 'Scanner associé au TEP : situe les structures anatomiques et aide à localiser une fixation.',
    'FDG': 'Analogue du glucose marqué au fluor-18. Une forte fixation n’est pas spécifique d’une tumeur.',
    'Hypermétabolisme': 'Fixation accrue du traceur. Peut notamment correspondre à une tumeur, une inflammation ou une infection.',
    'SUVmax': 'Valeur maximale de fixation standardisée dans une région. Ce n’est ni un stade, ni un pourcentage de cellules cancéreuses.',
    'Ganglion cervical': 'Ganglion lymphatique situé dans le cou. Son aspect et sa fixation nécessitent une interprétation médicale.',
    'Métastase': 'Implantation tumorale à distance du foyer d’origine ; ne peut pas être affirmée par simple recherche de mots ou valeur SUV.',
    'Fixation physiologique': 'Fixation normale dans certains tissus comme les muscles, les glandes salivaires ou le cerveau.'
}

QUESTIONS = [
    'Quelle zone exacte de la gencive ou de la mâchoire est décrite comme anormale ?',
    'Le compte rendu mentionne-t-il des ganglions du cou et quelle est leur interprétation ?',
    'Des foyers à distance sont-ils décrits et nécessitent-ils un examen complémentaire ?',
    'Les fixations peuvent-elles être expliquées par une inflammation ou des soins dentaires récents ?',
    'Comment le TEP-scan s’intègre-t-il avec la biopsie, le scanner/IRM et le bilan TNM ?',
    'Quelle est la prochaine étape proposée par la réunion de concertation pluridisciplinaire ?'
]

def audit_pet_ct(series):
    counts=Counter(str(getattr(s,'modality','')).upper() for s in series)
    pet=counts.get('PT',0) + counts.get('PET',0)
    ct=counts.get('CT',0)
    lines=[f'Séries repérées : PET/PT = {pet} ; scanner/CT = {ct}.']
    if not pet: lines.append('Aucune série PET/PT identifiée : vérifiez que tout le dossier DICOM a été sélectionné.')
    if not ct: lines.append('Aucune série CT identifiée : la fusion anatomique PET/CT ne peut pas être envisagée.')
    if pet and ct: lines.append('PET et CT présents. Leur alignement spatial n’a PAS été vérifié ; aucune fusion diagnostique n’est effectuée.')
    lines.append('L’affichage isolé et la navigation d’une série ne valent pas lecture validée d’un TEP-scan.')
    return '\n'.join(lines)

def explain_pet_report(report):
    text=(report or '').strip()
    if not text:return 'Collez le compte rendu du TEP-scan dans le champ prévu.\n\n'+LIMIT
    if len(text)>30000:return 'Texte trop long (30 000 caractères maximum).'
    def section(label,patterns):
        sentences=re.split(r'(?<=[.!?])\s+|\n+',text)
        chosen=[]
        for s in sentences:
            if any(re.search(pattern,s,re.I) for pattern in patterns):
                cleaned=s.strip()
                if cleaned and cleaned not in chosen:chosen.append(cleaned[:380])
        return label+'\n'+ ('\n'.join('• « '+s+' »' for s in chosen[:5]) if chosen else 'Aucune mention trouvée automatiquement dans le texte fourni.')
    sections=[
        section('BOUCHE / GENCIVE / MÂCHOIRE — citations du compte rendu :',[r'gingiv',r'genciv',r'mandibul',r'maxillair',r'cavit[eé] buccale',r'alv[eé]ol']),
        section('GANGLIONS / COU — citations :',[r'ganglion',r'cervical',r'ad[eé]nopath',r'jugul',r'cha[iî]ne']),
        section('AUTRES LOCALISATIONS — citations :',[r'pulmon',r'poumon',r'foie',r'h[eé]pat',r'osseu',r'os\b',r'm[eé]tasta']),
        section('VALEURS SUV — citations :',[r'\bSUV',r'fixation',r'hyperm[eé]tabol']),
        section('CONCLUSION DU MÉDECIN — citations :',[r'conclusion',r'impression',r'synth[eè]se']),
    ]
    return ('LECTURE GUIDÉE — EXTRAITS LITTÉRAUX, PAS DE DIAGNOSTIC AUTOMATIQUE\n\n'
            +'\n\n'.join(sections)+'\n\n'
            +'Mots non trouvés ≠ absence d’anomalie : le logiciel ne sait ni exclure des lésions ni calculer un stade TNM.\n\n'
            +LIMIT)
