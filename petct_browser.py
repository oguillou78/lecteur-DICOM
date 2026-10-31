"""PET/CT local side-by-side explorer; never performs diagnosis or PET/CT image fusion."""
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pydicom
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QComboBox,
 QLabel,QSlider,QTextEdit,QFileDialog,QMessageBox,QSplitter)

@dataclass
class Slice:
    path: str
    z: float | None
    normal: tuple | None
    origin: tuple | None
    frame: str
    modality: str
    desc: str
    units: str
    instance: int


def spatial_info(ds):
    try:
        iop=np.asarray(ds.ImageOrientationPatient,dtype=float)
        ipp=np.asarray(ds.ImagePositionPatient,dtype=float)
        if iop.size!=6 or ipp.size!=3:return None,None,None
        normal=np.cross(iop[:3],iop[3:]);normal/=np.linalg.norm(normal)
        return float(np.dot(ipp,normal)),tuple(float(v) for v in normal),tuple(float(v) for v in ipp)
    except (AttributeError,ValueError,TypeError,ZeroDivisionError):return None,None,None


def audit_folder(root):
    """Read headers only, ignore non-DICOM files and avoid patient identifiers."""
    groups=defaultdict(list); rejected=0
    for path in Path(root).rglob('*'):
        if not path.is_file():continue
        try:
            ds=pydicom.dcmread(str(path),stop_before_pixels=True)
            mod=str(getattr(ds,'Modality','')).upper()
            if mod not in ('CT','PT'):continue
            if not hasattr(ds,'PixelData') and not hasattr(ds,'Rows'):continue
            uid=str(getattr(ds,'SeriesInstanceUID',''))
            if not uid:continue
            z,normal,origin=spatial_info(ds)
            it=Slice(str(path),z,normal,origin,str(getattr(ds,'FrameOfReferenceUID','')),
                     mod,str(getattr(ds,'SeriesDescription','Sans description')),
                     str(getattr(ds,'Units','')),int(getattr(ds,'InstanceNumber',0)))
            groups[(uid,mod)].append(it)
        except Exception:rejected+=1
    result=[]
    for (uid,mod),items in groups.items():
        normals={tuple(round(v,4) for v in s.normal) for s in items if s.normal is not None}
        frames={s.frame for s in items}
        # If orientation or FrameOfReference varies, reject spatial comparison for this series.
        valid=len(normals)==1 and len(frames)==1 and all(s.z is not None for s in items)
        items.sort(key=lambda s:(s.z if valid else float(s.instance),s.path))
        result.append({'uid':uid,'mod':mod,'desc':items[0].desc,'items':items,'spatial':valid,
                       'label':f'{mod} · {items[0].desc} · {len(items)} image(s)'})
    result.sort(key=lambda g:(g['mod']!='PT',g['desc']))
    return result,rejected


def paired_slice(pet, ct_items, max_distance=4.0):
    """Match slice planes only; no interpolation/registration. Never claim image fusion."""
    if pet.z is None or pet.normal is None or not pet.frame:return None,'PET sans géométrie fiable.'
    matches=[]
    for ct in ct_items:
        if ct.frame!=pet.frame or ct.normal is None or ct.origin is None:continue
        dot=abs(float(np.dot(pet.normal,ct.normal)))
        if dot<0.999:continue
        # Project CT position onto PET normal, rather than compare raw Z of different orientations.
        distance=abs(float(np.dot(np.asarray(ct.origin),np.asarray(pet.normal)))-pet.z)
        matches.append((distance,ct))
    if not matches:return None,'Aucune correspondance géométrique vérifiable (orientation/référentiel).'
    dist,item=min(matches,key=lambda x:x[0])
    if dist>max_distance:return None,f'Coupe CT la plus proche à {dist:.1f} mm : correspondance refusée.'
    return item,f'Plans proches : écart de {dist:.2f} mm. Alignement des pixels NON vérifié.'


def display_frame(path, modality):
    ds=pydicom.dcmread(path)
    if int(getattr(ds,'NumberOfFrames',1))!=1:raise ValueError('Images multiframe non prises en charge dans cette vue.')
    arr=np.asarray(ds.pixel_array,dtype=np.float32)
    if arr.ndim!=2:raise ValueError('Image non monochrome : non prise en charge.')
    slope=float(getattr(ds,'RescaleSlope',1));intercept=float(getattr(ds,'RescaleIntercept',0))
    arr=arr*slope+intercept
    finite=arr[np.isfinite(arr)]
    if not finite.size:raise ValueError('Pixels non exploitables')
    if modality=='CT':
        lower,upper=-160,240
        info='Fenêtre tissus mous approximative : 40/400 UH'
    else:
        lower,upper=np.percentile(finite,[1,99.5])
        info='Contraste automatique uniquement. PAS de calcul SUV.'
    if upper<=lower:upper=lower+1
    display=(np.clip((arr-lower)/(upper-lower),0,1)*255).astype(np.uint8)
    display=np.ascontiguousarray(display)
    height,width=display.shape
    qimg=QImage(display.data,width,height,display.strides[0],QImage.Format_Grayscale8).copy()
    return qimg,info

class Scan(QThread):
    done=Signal(object,int); failed=Signal(str)
    def __init__(self,path):super().__init__();self.path=path
    def run(self):
        try:self.done.emit(*audit_folder(self.path))
        except Exception as exc:self.failed.emit(str(exc))

class ImagePane(QLabel):
    def __init__(self):
        super().__init__('Aucune image');self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(250,260);self.setStyleSheet('background:#050b14;border:1px solid #31475c')
        self.img=None
    def set_image(self,img):self.img=img;self.update_view()
    def update_view(self):
        if self.img is not None:
            self.setPixmap(QPixmap.fromImage(self.img).scaled(self.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
        else:
            self.clear();self.setText("Aucune image comparable")
    def resizeEvent(self,event):super().resizeEvent(event);self.update_view()

class PETCTBrowser(QWidget):
    def __init__(self):
        super().__init__();self.groups=[];self.root=None;self.scanner=None
        layout=QVBoxLayout(self)
        t=QLabel('EXPLORATEUR PET/CT · SANS COMPTE RENDU');t.setStyleSheet('font-size:17px;font-weight:bold')
        layout.addWidget(t)
        layout.addWidget(QLabel('Exploration pédagogique locale. Aucun modèle ne détecte de cancer. Pas de SUV calculé ni de fusion d’images.'))
        open_btn=QPushButton('Choisir le dossier principal du TEP-scan (sous-dossiers inclus)')
        open_btn.clicked.connect(self.open);layout.addWidget(open_btn)
        selectors=QHBoxLayout();self.pet=QComboBox();self.ct=QComboBox()
        selectors.addWidget(QLabel('PET :'));selectors.addWidget(self.pet,1)
        selectors.addWidget(QLabel('CT :'));selectors.addWidget(self.ct,1);layout.addLayout(selectors)
        self.pet.currentIndexChanged.connect(self.configure);self.ct.currentIndexChanged.connect(self.render)
        images=QSplitter(Qt.Horizontal)
        self.pet_image=ImagePane();self.ct_image=ImagePane();images.addWidget(self.pet_image);images.addWidget(self.ct_image)
        layout.addWidget(images,1)
        self.slider=QSlider(Qt.Horizontal);self.slider.valueChanged.connect(self.render);layout.addWidget(self.slider)
        self.status=QLabel('Sélectionne le dossier racine de ton examen.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.info=QTextEdit();self.info.setReadOnly(True);self.info.setMaximumHeight(150);layout.addWidget(self.info)
    def open(self):
        folder=QFileDialog.getExistingDirectory(self,'Dossier principal du TEP-scan')
        if not folder:return
        self.root=folder;self.status.setText('Inventaire des fichiers DICOM en cours…')
        self.scanner=Scan(folder);self.scanner.done.connect(self.found);self.scanner.failed.connect(self.error);self.scanner.start()
    def found(self,groups,rejected):
        self.groups=groups;self.pet.blockSignals(True);self.ct.blockSignals(True)
        self.pet.clear();self.ct.clear();self.ct.addItem('Aucune série CT',None)
        for n,g in enumerate(groups):
            if g['mod']=='PT':self.pet.addItem(g['label'],n)
            if g['mod']=='CT':self.ct.addItem(g['label'],n)
        self.pet.blockSignals(False);self.ct.blockSignals(False)
        if self.ct.count()>1:self.ct.setCurrentIndex(1)
        self.configure()
        self.status.setText(f'{len(groups)} séries PET/CT repérées. {rejected} fichiers ignorés/non reconnus. Données locales.')
    def configure(self,*args):
        g=self.get_group(self.pet)
        self.slider.blockSignals(True);self.slider.setRange(0,max(0,len(g['items'])-1) if g else 0)
        self.slider.setValue(len(g['items'])//2 if g else 0);self.slider.blockSignals(False);self.render()
    def get_group(self,combo):
        n=combo.currentData();return self.groups[n] if isinstance(n,int) and 0<=n<len(self.groups) else None
    def render(self,*args):
        p=self.get_group(self.pet);c=self.get_group(self.ct)
        if not p:return
        sl=p['items'][self.slider.value()]
        try:
            image,desc=display_frame(sl.path,'PT');self.pet_image.set_image(image)
        except Exception as exc:
            self.pet_image.set_image(None);desc=f'PET illisible : {exc}'
        ct=None;pair_msg='Sélectionne une série CT.'
        if c and p['spatial'] and c['spatial']:ct,pair_msg=paired_slice(sl,c['items'])
        elif c:pair_msg='Comparaison spatiale refusée : géométrie manquante ou incohérente.'
        if ct:
            try:img,_=display_frame(ct.path,'CT');self.ct_image.set_image(img)
            except Exception as exc:self.ct_image.set_image(None);pair_msg+=f' CT illisible : {exc}'
        else:self.ct_image.set_image(None)
        self.info.setPlainText(f'PET : {p["desc"]} · image {self.slider.value()+1}/{len(p["items"])}\n'
            f'Instance DICOM {sl.instance} · Position projetée : {sl.z if sl.z is not None else "inconnue"} mm\n'
            f'Unités déclarées : {sl.units or "non renseignées"} · {desc}\n'
            f'CT : {c["desc"] if c else "non choisi"}\n{pair_msg}\n'
            'ATTENTION : une coupe PET et une coupe CT proches ne sont pas nécessairement recalées pixel par pixel. '
            'Aucune identification de lésion, ni conclusion de malignité ou de métastase.')
    def error(self,exc):QMessageBox.warning(self,'Inventaire DICOM impossible',exc)
