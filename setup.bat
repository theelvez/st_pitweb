@echo off

echo Installing Python...
start /wait python-3.10.11-amd64.exe /quiet PrependPath=1

echo Creating virtual environment...
python -m venv pitwebenv_tst

echo Activating virtual environment...
call pitwebenv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing required packages...
python -m pip install -r requirements.txt

echo.
echo Setup completed successfully!
echo.
echo Activating pitweb environment
call pitwebenv\Scripts\activate.bat

echo To start the pitweb server run:
echo python app.py
echo.
echo.
echo To launch a chrome browser with the site running in it, run launchpitwebbrowser.bat

