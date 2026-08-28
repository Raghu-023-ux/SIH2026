#!/usr/bin/env bash
# ==============================================================================
# SIH26001: AI-Based Early Warning & Landslide Risk Monitoring System
# Multi-Platform Launch Orchestrator (Linux / macOS)
# ==============================================================================

set -e

echo "======================================================================"
echo "  SIH26001: North Eastern Region Landslide Early Warning System       "
echo "  Starting Backend (FastAPI :8000) & Frontend (Next.js :3000)         "
echo "======================================================================"

# Trap SIGINT to kill background processes on exit
cleanup() {
    echo -e "\nShutting down SIH26001 services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "\n[1/3] Starting Backend (Uvicorn on :8000)..."
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 3

echo -e "[2/3] Starting Frontend (Next.js on :3000)..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo -e "\n======================================================================"
echo "  SYSTEM ACCESS URLS:"
echo "  - Core Expert Command Center:   http://localhost:3000"
echo "  - Field Rescue Operations:      http://localhost:3000/field"
echo "  - Public Safety Portal:         http://localhost:3000/public"
echo "  - Model Calibration Studio:     http://localhost:3000/analytics"
echo "  - CAP v1.2 XML Feed:            http://localhost:8000/api/v1/alerts/cap.xml"
echo "  - Interactive OpenAPI Docs:     http://localhost:8000/docs"
echo "======================================================================"
echo "Press Ctrl+C to stop all services."

wait
