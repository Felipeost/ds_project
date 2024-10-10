@echo off
REM Activate the virtual environment
CALL "C:\Users\lalka\OneDrive\Skrivbord\Studier\Projekt\working repo\ds_project\env\Scripts\activate.bat"

REM Run the Python script
python "C:\Users\lalka\OneDrive\Skrivbord\Studier\Projekt\working repo\ds_project\etl_polis_data.py"

REM Pause to keep the command window open
pause
