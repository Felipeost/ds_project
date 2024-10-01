@echo off
REM Activate the Anaconda environment (if applicable)
CALL "C:\Users\lalka\anaconda3\Scripts\activate.bat" base

REM Run the Python script
python "C:\Users\lalka\OneDrive\Skrivbord\Studier\Projekt\etl_polis_data.py"

REM Pause to keep the command window open
pause