@echo off
echo Starting ClusterIQ Backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt --quiet
python main.py
pause

