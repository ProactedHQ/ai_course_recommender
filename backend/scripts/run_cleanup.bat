@echo off
call ..\..\.venv\Scripts\activate.bat
python manage.py clear_non_user_data --force
