@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (echo Python 3.11/3.12 est necessaire. & pause & exit /b 1)
py -3 -m venv .venv
if errorlevel 1 (echo Erreur environnement Python & pause & exit /b 1)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (echo Erreur installation des dependances & pause & exit /b 1)
python -m unittest discover -s tests -v
if errorlevel 1 (echo Echec des tests prealables & pause & exit /b 1)
python -m PyInstaller --noconfirm --clean --windowed --onedir --name "DICOM Clair" --collect-all SimpleITK --collect-all pydicom main.py
if errorlevel 1 (echo Echec compilation & pause & exit /b 1)
where iscc >nul 2>&1
if not errorlevel 1 (iscc installateur.iss & goto done)
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" ("C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installateur.iss & goto done)
echo INSTALLATEUR : installez Inno Setup 6 puis compilez installateur.iss.
:done
echo Fichiers generes dans dist\ et/ou installateur\
pause
