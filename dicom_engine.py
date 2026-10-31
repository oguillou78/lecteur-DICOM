"""Acquisition and reconstruction engine. No network requests."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import SimpleITK as sitk
import pydicom

@dataclass
class Series:
    key: str
    folder: str
    files: list[str]
    title: str
    modality: str
    description: str


def inspect_file(path):
    return pydicom.dcmread(str(path), stop_before_pixels=True, force=False,
                          specific_tags=['SeriesInstanceUID','SeriesDescription','Modality','StudyDescription',
                                         'PatientName','PatientID','Rows','Columns','NumberOfFrames'])


def discover(root):
    """Group via GDCM, respecting scan-direction rather than lexical ordering."""
    directories = sorted({str(p.parent) for p in Path(root).rglob('*') if p.is_file()})
    found=[]
    for folder in directories:
        try:
            ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(folder, useSeriesDetails=True) or []
        except RuntimeError:
            continue
        for sid in ids:
            try:
                paths=list(sitk.ImageSeriesReader.GetGDCMSeriesFileNames(folder,sid,True))
                if not paths: continue
                ds=inspect_file(paths[0]); modality=str(ds.get('Modality','?'))
                desc=str(ds.get('SeriesDescription','Sans description'))
                found.append(Series(f'{folder}|{sid}',folder,paths,f'{modality} · {desc} ({len(paths)} fichiers)',modality,desc))
            except Exception:
                continue
    # Single-file enhanced multi-frame or other DICOM files not enumerated as a GDCM series.
    used={str(Path(p).resolve()) for s in found for p in s.files}
    for folder in directories:
        for p in Path(folder).iterdir():
            if not p.is_file() or str(p.resolve()) in used: continue
            try:
                ds=inspect_file(p)
                if not getattr(ds,'SOPClassUID',None):
                    # SOPClassUID is not read when specific_tags is provided: use minimal check
                    ds=pydicom.dcmread(str(p),stop_before_pixels=True)
                if not getattr(ds,'SOPClassUID',None): continue
                desc=str(ds.get('SeriesDescription','Image DICOM'))
                found.append(Series(str(p),str(p.parent),[str(p)],f'{ds.get("Modality","?")} · {desc} (fichier)',str(ds.get('Modality','?')),desc))
            except Exception: pass
    return found


def read_series(series):
    if len(series.files)>1:
        rdr=sitk.ImageSeriesReader(); rdr.SetFileNames(series.files)
        image=rdr.Execute()
    else:
        image=sitk.ReadImage(series.files[0])
    array=sitk.GetArrayFromImage(image)
    if array.ndim == 2: array=array[np.newaxis,:,:]
    if array.ndim != 3:
        raise ValueError('Volume non scalaire ou dimensions non prises en charge (4D, couleurs, segmentation).')
    if array.size > 300_000_000:
        raise ValueError('Volume supérieur à la limite de sécurité mémoire de cette version.')
    return image, array


def extract_plane(volume,plane,idx):
    if plane=='axial': return volume[idx,:,:]
    if plane=='coronal': return volume[:,idx,:]
    if plane=='sagittal': return volume[:,:,idx]
    raise ValueError(plane)


def plane_count(volume,plane):
    return {'axial':volume.shape[0],'coronal':volume.shape[1],'sagittal':volume.shape[2]}[plane]


def window_pixels(arr,center,width,invert=False):
    """Display-only linear window; not a quantitative intensity transform."""
    a=np.asarray(arr,dtype=np.float32)
    lo=float(center)-max(1.0,float(width))/2
    u=np.clip((a-lo)/max(1.0,float(width)),0,1)
    if invert: u=1-u
    return np.ascontiguousarray((u*255).astype(np.uint8))


def describe_image(arr, spacing, modality, plane):
    a=np.asarray(arr,dtype=np.float64)
    a=a[np.isfinite(a)]
    if not a.size: return 'Image sans valeurs numériques finies exploitables.'
    p=np.percentile(a,[1,50,99])
    return (f'Observation descriptive de la coupe {plane} ({modality}) : '
            f'valeurs numériques min={np.min(a):.1f}, médiane={p[1]:.1f}, max={np.max(a):.1f}; '
            f'percentiles 1–99 % : {p[0]:.1f} à {p[2]:.1f}. '
            'Ces valeurs dépendent de la modalité et des paramètres d’acquisition. '
            'Elles ne permettent pas d’identifier une lésion, une fracture ou une maladie.')
