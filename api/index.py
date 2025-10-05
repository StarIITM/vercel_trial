from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import statistics

app = FastAPI()

# Enable CORS for POST requests from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data
root = Path(__file__).parent
with open(root / "telemetry.json") as f:
    telemetry_raw = json.load(f)

# Convert flat list into per-region dictionary
telemetry_data = {}
for row in telemetry_raw:
    region = row["region"]
    telemetry_data.setdefault(region, []).append({
        "latency_ms": row["latency_ms"],
        "uptime": row["uptime_pct"] / 100.0  # convert % to 0-1
    })

@app.post("/")
async def compute_metrics(request: Request):
    req = await request.json()
    regions = req.get("regions", [])
    threshold = req.get("threshold_ms", 180)

    result = {}
    for region in regions:
        entries = telemetry_data.get(region, [])
        if not entries:
            result[region] = {"avg_latency": 0, "p95_latency": 0, "avg_uptime": 0, "breaches": 0}
            continue

        latencies = [e["latency_ms"] for e in entries]
        uptimes = [e["uptime"] for e in entries]
        breaches = sum(1 for l in latencies if l > threshold)

        avg_latency = round(sum(latencies)/len(latencies), 2)
        try:
            p95_latency = round(statistics.quantiles(latencies, n=100)[94], 2)
        except Exception:
            p95_latency = max(latencies)
        avg_uptime = round(sum(uptimes)/len(uptimes), 3)

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return result
