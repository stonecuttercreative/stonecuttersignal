# BEGIN stonecutter extension: FastAPI dashboard
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any
import datetime
from ..persistence.sqlite_store import last_runs, get_run_details

app = FastAPI(title="Stonecutter Signal Dashboard", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"ok": True}

@app.get("/runs", response_model=List[Dict[str, Any]])
async def get_runs():
    """Get last 50 runs."""
    try:
        runs = last_runs(limit=50)
        return runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching runs: {str(e)}")

@app.get("/runs/{run_id}")
async def get_run_details_endpoint(run_id: str):
    """Get full run details by ID."""
    try:
        details = get_run_details(run_id)
        if details is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching run details: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Simple HTML dashboard showing recent runs."""
    try:
        runs = last_runs(limit=20)
        
        # Build HTML table
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Stonecutter Signal Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .timestamp { white-space: nowrap; }
                .concept { max-width: 300px; overflow: hidden; text-overflow: ellipsis; }
                .metrics { text-align: center; }
                a { color: #007bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Stonecutter Signal Dashboard</h1>
            <p>Recent analysis runs (last 20)</p>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Brand</th>
                        <th>Category</th>
                        <th>Audience</th>
                        <th>Confidence</th>
                        <th>Consensus</th>
                        <th>Diversity</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        if not runs:
            html_content += """
                    <tr>
                        <td colspan="8" style="text-align: center; color: #666;">
                            No runs found. Run some analyses to see data here.
                        </td>
                    </tr>
            """
        else:
            for run in runs:
                # Format timestamp
                if run.get('timestamp'):
                    dt = datetime.datetime.fromtimestamp(run['timestamp'])
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    formatted_time = 'Unknown'
                
                # Truncate long text fields
                brand = (run.get('brand') or 'Unknown')[:30]
                category = (run.get('category') or 'Unknown')[:30]
                audience = (run.get('audience') or '')[:40]
                
                # Format metrics
                confidence = run.get('confidence', 0)
                consensus = run.get('consensus', 0) 
                diversity = run.get('diversity', 0)
                
                html_content += f"""
                    <tr>
                        <td class="timestamp">{formatted_time}</td>
                        <td>{brand}</td>
                        <td>{category}</td>
                        <td>{audience}</td>
                        <td class="metrics">{confidence}%</td>
                        <td class="metrics">{consensus}%</td>
                        <td class="metrics">{diversity}%</td>
                        <td><a href="/runs/{run['id']}">View Details</a></td>
                    </tr>
                """
        
        html_content += """
                </tbody>
            </table>
            <br>
            <p><small>
                <a href="/health">Health Check</a> | 
                <a href="/runs">JSON API</a>
            </small></p>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Dashboard Error</title></head>
        <body>
            <h1>Dashboard Error</h1>
            <p>Error loading dashboard: {str(e)}</p>
            <p><a href="/health">Health Check</a></p>
        </body>
        </html>
        """
        return error_html
# END stonecutter extension