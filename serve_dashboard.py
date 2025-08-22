# BEGIN stonecutter extension: dashboard server
"""
Stonecutter Signal Dashboard Server

Run this script to start the web dashboard for viewing recent analysis runs.
Visit http://localhost:8000 to see the dashboard.
"""

if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    
    # Add src to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    from src.stonecutter.webapp.app import app
    
    print("Starting Stonecutter Signal Dashboard...")
    print("Visit http://localhost:8000 to view the dashboard")
    print("Health check: http://localhost:8000/health")
    print("API endpoint: http://localhost:8000/runs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
# END stonecutter extension