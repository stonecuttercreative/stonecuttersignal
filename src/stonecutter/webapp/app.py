# BEGIN stonecutter extension: FastAPI dashboard
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any
import datetime
from ..persistence.sqlite_store import last_runs, get_run_details
from ..logging_conf import logger

# BEGIN stonecutter fix: ts-seconds
def _fmt_ts(ts):
    """Format timestamp safely, handling None and malformed values."""
    if not ts:
        return ""
    try:
        # ts already normalized to seconds; if not, best-effort fix:
        if ts > 1_000_000_000_000:
            ts = ts // 1000
        return datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)
# END stonecutter fix: ts-seconds

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
        logger.info(f"[dashboard] API returned {len(runs)} runs")
        return runs
    except Exception as e:
        logger.error(f"[dashboard] Error fetching runs: {e}")
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
        logger.info(f"[dashboard] HTML dashboard showing {len(runs)} runs")
        
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
                # BEGIN stonecutter fix: ts-seconds
                # Format timestamp safely
                formatted_time = _fmt_ts(run.get('ts', run.get('timestamp')))
                # END stonecutter fix: ts-seconds
                
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
            
            <hr><h3>Signal Metrics (last 50 runs)</h3>
            <canvas id="timeseries" height="120"></canvas>
            
            <hr><h3>Provider Latency (latest run)</h3>
            <canvas id="providers" height="120"></canvas>
            
            <hr><h3>Provider Participation</h3>
            <canvas id="providerpie" height="120"></canvas>
            
            <hr><h3>Distribution Histogram</h3>
            <canvas id="distribution" height="120"></canvas>
            
            <hr><h3>Latest Run Radar</h3>
            <canvas id="radar" height="120"></canvas>
            
            <hr><h3>Run Activity (last 30 days)</h3>
            <canvas id="activity" height="120"></canvas>
            
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
            async function fetchJSON(u){const r=await fetch(u,{cache:'no-store'});return await r.json();}
            function tsToLabel(s){if(s>1e12) s=Math.floor(s/1000);return new Date(s*1000).toLocaleString();}
            
            async function draw(){
              // 1 Time series
              const ts=await fetchJSON('/metrics/timeseries?limit=50');
              new Chart(document.getElementById('timeseries'),{
                type:'line',data:{labels:(ts.labels||[]).map(tsToLabel),
                  datasets:[
                    {label:'Confidence',data:ts.confidence,borderWidth:2,borderColor:'rgb(75, 192, 192)'},
                    {label:'Consensus',data:ts.consensus,borderWidth:2,borderColor:'rgb(255, 99, 132)'},
                    {label:'Diversity',data:ts.diversity,borderWidth:2,borderColor:'rgb(255, 205, 86)'}]},
                options:{scales:{y:{beginAtZero:true,max:100}}}
              });
            
              // 2 Provider latency
              const pv=await fetchJSON('/metrics/providers');
              const provs=pv.providers||[];
              new Chart(document.getElementById('providers'),{
                type:'bar',data:{labels:provs.map(p=>p.provider),
                  datasets:[{label:'Avg Latency (ms)',data:provs.map(p=>p.avg_latency_ms||0),backgroundColor:'rgba(54, 162, 235, 0.6)'}]}
              });
            
              // 3 Provider participation
              new Chart(document.getElementById('providerpie'),{
                type:'doughnut',
                data:{labels:provs.map(p=>p.provider),
                  datasets:[{label:'Mock vs Real',
                    data:provs.map(p=>p.mock+p.real),
                    backgroundColor:['#ff6384','#36a2eb','#cc65fe','#ffce56','#ff9f40']}]}
              });
            
              // 4 Distribution histogram
              const dist=await fetchJSON('/metrics/distribution?bins=5&limit=200');
              const labelsH=['0-20','20-40','40-60','60-80','80-100'];
              new Chart(document.getElementById('distribution'),{
                type:'bar',
                data:{labels:labelsH,
                  datasets:[
                    {label:'Confidence',data:dist.confidence,backgroundColor:'rgba(75, 192, 192, 0.6)'},
                    {label:'Consensus',data:dist.consensus,backgroundColor:'rgba(255, 99, 132, 0.6)'},
                    {label:'Diversity',data:dist.diversity,backgroundColor:'rgba(255, 205, 86, 0.6)'}]},
                options:{scales:{y:{beginAtZero:true}}}
              });
            
              // 5 Radar
              const latest=await fetchJSON('/metrics/latest');
              new Chart(document.getElementById('radar'),{
                type:'radar',
                data:{labels:['Confidence','Consensus','Diversity'],
                  datasets:[{label:'Latest Run',data:[latest.confidence,latest.consensus,latest.diversity],backgroundColor:'rgba(255, 99, 132, 0.2)',borderColor:'rgba(255, 99, 132, 1)'}]},
                options:{scales:{r:{beginAtZero:true,max:100}}}
              });
            
              // 6 Activity heatmap (simple bar)
              const act=await fetchJSON('/metrics/activity?days=30');
              new Chart(document.getElementById('activity'),{
                type:'bar',
                data:{labels:act.activity.map(a=>a.date),
                  datasets:[{label:'Runs',data:act.activity.map(a=>a.count),backgroundColor:'rgba(153, 102, 255, 0.6)'}]},
                options:{scales:{y:{beginAtZero:true}}}
              });
            }
            draw();
            </script>
            
            <br>
            <p><small>
                <a href="/health">Health Check</a> | 
                <a href="/runs">JSON API</a> |
                <a href="/metrics/timeseries">Timeseries</a> |
                <a href="/metrics/providers">Providers</a> |
                <a href="/metrics/distribution">Distribution</a> |
                <a href="/metrics/latest">Latest</a> |
                <a href="/metrics/activity">Activity</a> |
                <a href="/health/providers">Provider Health</a>
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

# BEGIN stonecutter extension: visuals
@app.get("/metrics/distribution")
def metrics_distribution(bins: int = 5, limit: int = 200):
    """Histogram counts for confidence/consensus/diversity."""
    rows = last_runs(limit)
    out = {"confidence": [], "consensus": [], "diversity": []}
    
    def bucket(vals):
        if not vals: 
            return []
        step = 100 // bins
        buckets = [0] * bins
        for v in vals:
            if v is None: 
                continue
            i = min(v // step, bins - 1)
            buckets[i] += 1
        return buckets
    
    out["confidence"] = bucket([r.get("confidence", 0) for r in rows])
    out["consensus"] = bucket([r.get("consensus", 0) for r in rows])
    out["diversity"] = bucket([r.get("diversity", 0) for r in rows])
    return out

@app.get("/metrics/latest")
def metrics_latest():
    """Return latest run for radar chart."""
    rows = last_runs(1)
    if not rows: 
        return {}
    r = rows[0]
    return {
        "confidence": r.get("confidence"),
        "consensus": r.get("consensus"),
        "diversity": r.get("diversity")
    }

@app.get("/metrics/activity")
def metrics_activity(days: int = 30):
    """Count runs per day for heatmap."""
    from collections import Counter
    import datetime
    
    rows = last_runs(1000)
    ctr = Counter()
    for r in rows:
        ts = r.get("ts")
        if ts:
            d = datetime.date.fromtimestamp(int(ts))
            ctr[d] += 1
    
    out = []
    today = datetime.date.today()
    for i in range(days):
        day = today - datetime.timedelta(days=i)
        out.append({"date": str(day), "count": ctr.get(day, 0)})
    
    return {"activity": list(reversed(out))}

@app.get("/metrics/timeseries")
def metrics_timeseries(limit: int = 50):
    """Time series data for confidence, consensus, diversity."""
    rows = last_runs(limit)
    
    # Reverse to get chronological order
    rows = list(reversed(rows))
    
    return {
        "labels": [r.get("ts") for r in rows],
        "confidence": [r.get("confidence", 0) for r in rows],
        "consensus": [r.get("consensus", 0) for r in rows],
        "diversity": [r.get("diversity", 0) for r in rows]
    }

@app.get("/metrics/providers")
def metrics_providers():
    """Provider latency and participation data."""
    from collections import defaultdict
    
    # Get recent runs to calculate provider stats
    rows = last_runs(10)
    provider_stats = defaultdict(lambda: {"latency_sum": 0, "latency_count": 0, "mock": 0, "real": 0})
    
    for row in rows:
        run_details = get_run_details(row["id"])
        if run_details and run_details.get("providers"):
            for provider in run_details["providers"]:
                name = provider.get("provider", "unknown")
                latency = provider.get("latency_ms", 0)
                is_mock = provider.get("is_mock", False)
                
                if latency > 0:
                    provider_stats[name]["latency_sum"] += latency
                    provider_stats[name]["latency_count"] += 1
                
                if is_mock:
                    provider_stats[name]["mock"] += 1
                else:
                    provider_stats[name]["real"] += 1
    
    providers = []
    for name, stats in provider_stats.items():
        avg_latency = 0
        if stats["latency_count"] > 0:
            avg_latency = stats["latency_sum"] / stats["latency_count"]
        
        providers.append({
            "provider": name,
            "avg_latency_ms": round(avg_latency, 2),
            "mock": stats["mock"],
            "real": stats["real"]
        })
    
    return {"providers": providers}

# BEGIN stonecutter live: providers health endpoint
import os
from ..settings import settings

@app.get("/health/providers")
def providers_health():
    def row(name, enabled, key_env, model):
        key_ok = bool(os.environ.get(key_env) or getattr(settings, key_env.lower(), None))
        return {
            "provider": name,
            "enabled": bool(enabled),
            "key_present": bool(key_ok),
            "model": model,
            "expected_mode": "LIVE" if (enabled and key_ok) else "MOCK"
        }
    return {"providers": [
        row("openai", settings.enable_openai, "OPENAI_API_KEY", settings.openai_model),
        row("claude", settings.enable_claude, "ANTHROPIC_API_KEY", settings.claude_model),
        row("gemini", settings.enable_gemini, "GOOGLE_GENAI_API_KEY", settings.gemini_model),
        row("perplexity", settings.enable_perplexity, "PERPLEXITY_API_KEY", settings.perplexity_model),
        row("grok", settings.enable_grok, "XAI_API_KEY", settings.grok_model),
    ]}
# END stonecutter live: providers health endpoint
# END stonecutter extension: visuals

# END stonecutter extension