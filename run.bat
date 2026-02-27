@echo off
echo ==================================================
echo  UPI Intelligence Platform — Full Stack
echo  React + FastAPI
echo ==================================================
echo.
echo Starting FastAPI backend on port 8000...
start "UPI Backend" cmd /k "cd /d %~dp0backend && py -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak > nul
echo Starting React frontend on port 5173...
start "UPI Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 3 /nobreak > nul
echo.
echo ==================================================
echo  Backend:  http://localhost:8000/api/health
echo  Frontend: http://localhost:5173
echo ==================================================
echo.
start http://localhost:5173
