import sys
from pathlib import Path
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QGridLayout,
 QSplitter,QLabel,QPushButton,QListWidget,QTextEdit,QPlainTextEdit,QSlider,QSpinBox,
 QGroupBox,QFileDialog,QMessageBox,QCheckBox,QTabWidget,QScrollArea,QStatusBar,QComboBox)
from dicom_engine import discover, read_series, extract_plane, plane_count, window_pixels, describe_image
from petct_browser import PETCTBrowser
from assistant_local import explain,summarize_report,DISCLAIMER
from oncology_assistant import SUPPORTED_TARGETS,assess_readiness,interpretation_boundary
from pet_oral_assistant import audit_pet_ct, explain_pet_report, GLOSSARY, QUESTIONS
from pet_image_guide import study_inventory, describe_selected, safe_read_header

STYLE='''
QWidget{background:#0d1727;color:#e7edf6;font-family:Segoe UI;font-size:12px}
QPushButton{background:#1e3655;padding:9px;border-radius:6px;border:1px solid #365776}
QPushButton:hover{background:#2b507a}
QTextEdit,QPlainTextEdit,QListWidget,QSpinBox{background:#111f32;border:1px solid #35516b;border-radius:5px;padding:5px}
QGroupBox{border:1px solid #29425b;margin-top:12px;padding:10px;border-radius:7px;font-weight:bold}
QGroupBox::title{subcontrol-origin:margin;left:12px;padding:0 5px}
QSlider::groove:horizontal{height:5px;background:#34506a}
QSlider::handle:horizontal{background:#77c5e9;width:13px;margin:-5px 0;border-radius:6px}
'''

class ScanThread(QThread):
    result=Signal(object); failure=Signal(str)
    def __init__(self,path): super().__init__();self.path=path
    def run(self):
        try:self.result.emit(discover(self.path))
        except Exception as e:self.failure.emit(str(e))

class LoadThread(QThread):
    result=Signal(object,object); failure=Signal(str)
    def __init__(self,s): super().__init__();self.s=s
    def run(self):
        try:self.result.emit(*read_series(self.s))
        except Exception as e:self.failure.emit(str(e))

class PlaneWidget(QWidget):
    def __init__(self,name):
        super().__init__();self.name=name;self.array=None;self.image=None
        lay=QVBoxLayout(self);lay.setContentsMargins(3,3,3,3)
        self.title=QLabel(name.upper());self.title.setAlignment(Qt.AlignCenter);lay.addWidget(self.title)
        self.pic=QLabel('Aucune image');self.pic.setMinimumSize(220,180);self.pic.setAlignment(Qt.AlignCenter)
        self.pic.setStyleSheet('background:#000;border:1px solid #243e59');lay.addWidget(self.pic,1)
        self.slider=QSlider(Qt.Horizontal);self.slider.valueChanged.connect(self.on_change);lay.addWidget(self.slider)
        self.n=QLabel('0 / 0');self.n.setAlignment(Qt.AlignCenter);lay.addWidget(self.n)
        self.on_change_callback=None
    def set_volume(self,array):
        self.array=array;cnt=plane_count(array,self.name)
        self.slider.blockSignals(True);self.slider.setRange(0,cnt-1);self.slider.setValue(cnt//2);self.slider.blockSignals(False)
        self.n.setText(f'{cnt//2+1} / {cnt}')
    def on_change(self,_):
        self.n.setText(f'{self.slider.value()+1} / {self.slider.maximum()+1}')
        if self.on_change_callback:self.on_change_callback()
    def set_frame(self,image):
        self.image=image;self.rescale()
    def rescale(self):
        if self.image is None:return
        self.pic.setPixmap(QPixmap.fromImage(self.image).scaled(self.pic.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
    def resizeEvent(self,event):super().resizeEvent(event);self.rescale()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('DICOM Clair Pro — Explorateur pédagogique, NON DIAGNOSTIQUE')
        self.resize(1520,920);self.volume=None;self.sitk_image=None;self.series=[];self.selected=None
        root=QWidget();self.setCentralWidget(root);main=QVBoxLayout(root)
        header=QHBoxLayout();ttl=QLabel('DICOM CLAIR  ·  EXPLORATION MULTIPLANAIRE');ttl.setStyleSheet('font-size:20px;font-weight:bold;color:#94d4ee')
        header.addWidget(ttl);header.addStretch()
        btn=QPushButton('Ouvrir un dossier DICOM');btn.clicked.connect(self.open_folder);header.addWidget(btn)
        main.addLayout(header)
        warning=QLabel('USAGE PÉDAGOGIQUE UNIQUEMENT — Aucun diagnostic, ni triage, ni exclusion de pathologie. Données traitées localement.')
        warning.setWordWrap(True);warning.setStyleSheet('background:#3c3020;color:#ffdeb0;padding:9px;border-radius:5px');main.addWidget(warning)
        splitter=QSplitter(Qt.Horizontal);main.addWidget(splitter,1)
        left=QWidget();lv=QVBoxLayout(left);lv.addWidget(QLabel('Séries disponibles'))
        self.list=QListWidget();self.list.currentRowChanged.connect(self.select_series);lv.addWidget(self.list,1)
        self.meta=QPlainTextEdit();self.meta.setReadOnly(True);self.meta.setPlaceholderText('Métadonnées techniques');lv.addWidget(self.meta,1)
        splitter.addWidget(left)
        center=QWidget();cv=QVBoxLayout(center)
        tools=QHBoxLayout();tools.addWidget(QLabel('Centre :'))
        self.wc=QSpinBox();self.wc.setRange(-50000,50000);self.wc.setValue(40);tools.addWidget(self.wc)
        tools.addWidget(QLabel('Largeur :'));self.ww=QSpinBox();self.ww.setRange(1,100000);self.ww.setValue(400);tools.addWidget(self.ww)
        auto=QPushButton('Fenêtre auto');auto.clicked.connect(self.auto_window);tools.addWidget(auto)
        self.inv=QCheckBox('Inverser');tools.addWidget(self.inv);tools.addStretch();cv.addLayout(tools)
        self.wc.valueChanged.connect(self.render);self.ww.valueChanged.connect(self.render);self.inv.stateChanged.connect(self.render)
        views=QGridLayout();self.planes={}
        for i,name in enumerate(['axial','coronal','sagittal']):
            p=PlaneWidget(name);p.on_change_callback=self.render;views.addWidget(p,i//2,i%2);self.planes[name]=p
        cv.addLayout(views,1)
        self.measure=QLabel('MPR : les plans sont calculés à partir du volume chargé. Orientation anatomique non réorientée en RAS.')
        self.measure.setWordWrap(True);cv.addWidget(self.measure)
        splitter.addWidget(center)
        right=QTabWidget();helper=QWidget();hv=QVBoxLayout(helper)
        hv.addWidget(QLabel('Assistant pédagogique local (sans modèle IA clinique)'))
        self.question=QPlainTextEdit();self.question.setPlaceholderText('Exemple : Que signifie MPR ? Que sont les unités HU ?');self.question.setMaximumHeight(85);hv.addWidget(self.question)
        ask=QPushButton('Expliquer');ask.clicked.connect(self.ask);hv.addWidget(ask)
        obs=QPushButton('Décrire les pixels de la coupe axiale');obs.clicked.connect(self.observe);hv.addWidget(obs)
        self.answer=QTextEdit();self.answer.setReadOnly(True);self.answer.setPlainText(DISCLAIMER);hv.addWidget(self.answer,1)
        right.addTab(helper,'Assistant')
        report=QWidget();rv=QVBoxLayout(report);rv.addWidget(QLabel('Coller le compte rendu radiologique (texte) :'))
        self.report=QPlainTextEdit();rv.addWidget(self.report,1)
        report_btn=QPushButton('Extraire la conclusion sans réinterprétation');report_btn.clicked.connect(self.summarize);rv.addWidget(report_btn)
        self.summary=QTextEdit();self.summary.setReadOnly(True);rv.addWidget(self.summary,1)
        right.addTab(report,'Compte rendu')
        pet=QWidget();pv=QVBoxLayout(pet)
        pet_title=QLabel('TEP-SCAN (PET/CT) — CANCER DE LA GENCIVE / CAVITÉ BUCCALE')
        pet_title.setWordWrap(True);pv.addWidget(pet_title)
        self.pet_audit=QPlainTextEdit();self.pet_audit.setReadOnly(True);self.pet_audit.setMaximumHeight(115)
        self.pet_audit.setPlainText('Ouvrez le dossier DICOM complet du TEP-scan pour repérer les séries PET et CT.')
        pv.addWidget(self.pet_audit)
        guide_btn=QPushButton('Explorer les images SANS compte rendu');guide_btn.clicked.connect(self.explore_pet);pv.addWidget(guide_btn)
        self.pet_without_report=QPlainTextEdit();self.pet_without_report.setReadOnly(True)
        self.pet_without_report.setPlaceholderText('Ouvrez le dossier DICOM, puis choisissez une série PET/PT ou CT. Cliquez ensuite sur Explorer les images SANS compte rendu.')
        pv.addWidget(self.pet_without_report,2)
        pv.addWidget(QLabel('Facultatif — collez le compte rendu quand vous le recevrez :'))
        self.pet_report=QPlainTextEdit();self.pet_report.setPlaceholderText('Compte rendu de TEP-scan, idéalement sans nom, date de naissance, adresse ni identifiant patient.')
        pv.addWidget(self.pet_report,1)
        pet_btn=QPushButton('Expliquer les mentions du compte rendu');pet_btn.clicked.connect(self.explain_pet);pv.addWidget(pet_btn)
        self.pet_result=QTextEdit();self.pet_result.setReadOnly(True)
        self.pet_result.setPlainText('Le TEP-scan ne suffit pas à lui seul pour confirmer ou exclure une lésion. Le module ne calcule pas de diagnostic ni de stade TNM.')
        pv.addWidget(self.pet_result,1)
        reference=QLabel('REPÈRES : '+ ' | '.join(GLOSSARY.keys()))
        reference.setWordWrap(True);pv.addWidget(reference)
        right.addTab(pet,'TEP gencive')
        right.addTab(PETCTBrowser(),'Explorateur PET/CT')
        oncology=QWidget();ov=QVBoxLayout(oncology)
        ov.addWidget(QLabel('PARCOURS ONCOLOGIE — assistant informatif, non diagnostique'))
        self.onco_target=QComboBox();self.onco_target.addItems(SUPPORTED_TARGETS.keys());ov.addWidget(self.onco_target)
        onco_btn=QPushButton('Vérifier l’éligibilité du module');onco_btn.clicked.connect(self.check_oncology);ov.addWidget(onco_btn)
        self.onco_output=QTextEdit();self.onco_output.setReadOnly(True)
        self.onco_output.setPlainText('Aucun modèle clinique de détection de cancer installé.\n\n'+interpretation_boundary())
        ov.addWidget(self.onco_output,1)
        right.addTab(oncology,'Oncologie')
        splitter.addWidget(right);splitter.setSizes([260,850,360])
        self.setStatusBar(QStatusBar());self.statusBar().showMessage('Prêt — aucune donnée médicale transmise sur Internet.')
    def open_folder(self):
        folder=QFileDialog.getExistingDirectory(self,'Sélectionner un dossier contenant les séries DICOM')
        if not folder:return
        self.list.clear();self.volume=None;self.statusBar().showMessage('Recherche des séries…')
        self.scan=ScanThread(folder);self.scan.result.connect(self.found);self.scan.failure.connect(self.fail);self.scan.start()
    def found(self,series):
        self.series=series
        self.pet_audit.setPlainText(audit_pet_ct(series))
        self.pet_without_report.setPlainText(study_inventory(series))
        for s in series:self.list.addItem(s.title)
        self.statusBar().showMessage(f'{len(series)} série(s) identifiée(s).')
        if not series:QMessageBox.information(self,'Aucune série','Aucune série DICOM prise en charge n’a été trouvée.')
    def select_series(self,row):
        if row<0 or row>=len(self.series):return
        self.selected=self.series[row];self.volume=None;self.sitk_image=None;self.statusBar().showMessage('Chargement de la série…')
        self.load=LoadThread(self.selected);self.load.result.connect(self.loaded);self.load.failure.connect(self.fail);self.load.start()
    def loaded(self,img,array):
        self.sitk_image=img;self.volume=array
        for p in self.planes.values():p.set_volume(array)
        spacing=img.GetSpacing();dims=img.GetSize();direction=img.GetDirection()
        self.meta.setPlainText(f'Modalité : {self.selected.modality}\nDescription : {self.selected.description}\n'
            f'Dimensions (X,Y,Z) : {dims}\nEspacement mm : {tuple(round(float(x),3) for x in spacing)}\n'
            f'Origine : {img.GetOrigin()}\nDirection : {direction}\nFichiers : {len(self.selected.files)}\n'
            'Attention : réorientation canonique non appliquée. Le plan affiché dépend de la géométrie source.')
        self.measure.setText(f'Volume : {dims} voxels · espacement : {tuple(round(float(x),2) for x in spacing)} mm. '
             'Les étiquettes axiale/coronale/sagittale désignent ici les axes du tableau ; '
             'une orientation oblique doit être réorientée avant toute utilisation anatomique stricte.')
        self.auto_window();self.statusBar().showMessage('Série chargée localement.')
    def auto_window(self):
        if self.volume is None:return
        sample=self.volume.ravel()[::max(1,self.volume.size//100000)]
        sample=sample[np.isfinite(sample)]
        if not sample.size:return
        low,high=np.percentile(sample,[2,98]);self.wc.setValue(int(np.clip((low+high)/2,-50000,50000)))
        self.ww.setValue(int(np.clip(max(1,high-low),1,100000)));self.render()
    def render(self,*_):
        if self.volume is None:return
        for name,p in self.planes.items():
            arr=extract_plane(self.volume,name,p.slider.value());pixels=window_pixels(arr,self.wc.value(),self.ww.value(),self.inv.isChecked())
            h,w=pixels.shape;frame=QImage(pixels.data,w,h,pixels.strides[0],QImage.Format_Grayscale8).copy()
            p.set_frame(frame)
    def observe(self):
        if self.volume is None:self.answer.setPlainText('Chargez d’abord un volume DICOM.');return
        p=self.planes['axial'];slice_=extract_plane(self.volume,'axial',p.slider.value())
        self.answer.setPlainText(describe_image(slice_,self.sitk_image.GetSpacing(),self.selected.modality,'axiale')+'\n\n'+DISCLAIMER)
    def ask(self):
        s=self.selected;self.answer.setPlainText(explain(self.question.toPlainText(),s.modality if s else '',s.description if s else ''))
    def summarize(self):self.summary.setPlainText(summarize_report(self.report.toPlainText()))
    def explore_pet(self):
        if not self.series:
            self.pet_without_report.setPlainText('Ouvrez d’abord le dossier DICOM complet de votre TEP-scan.\n\n'+study_inventory([]))
            return
        if self.selected is None:
            self.pet_without_report.setPlainText(study_inventory(self.series)+'\n\nSélectionnez une série à gauche pour afficher ses métadonnées.')
            return
        header=None
        try:
            if self.selected.files: header=safe_read_header(self.selected.files[0])
        except Exception:
            pass
        self.pet_without_report.setPlainText(study_inventory(self.series)+'\n\n'+describe_selected(self.selected, header, self.sitk_image if self.volume is not None else None, self.volume))
    def explain_pet(self):self.pet_result.setPlainText(explain_pet_report(self.pet_report.toPlainText()) + "\n\nQUESTIONS POUR VOTRE ÉQUIPE SOIGNANTE :\n" + "\n".join("• "+q for q in QUESTIONS))
    def check_oncology(self):
        modality=self.selected.modality if self.selected else ''
        result=assess_readiness(self.onco_target.currentText(),modality)
        self.onco_output.setPlainText(result.status+'\n\n'+result.text+'\n\n'+interpretation_boundary())
    def fail(self,error):
        self.statusBar().showMessage('Erreur de lecture DICOM');QMessageBox.warning(self,'Lecture impossible',error+'\n\nCertains formats compressés ou Enhanced DICOM peuvent ne pas être pris en charge.')

def main():
    app=QApplication(sys.argv);app.setStyleSheet(STYLE)
    w=MainWindow();w.show();sys.exit(app.exec())
if __name__=='__main__':main()
