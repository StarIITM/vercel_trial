from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import pandas as pd
import numpy as np

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
telemetry_df = pd.read_json(root / "telemetry.json")
telemetry_df["uptime"] = telemetry_df["uptime_pct"] / 100.0

@app.post("/")
async def compute_metrics(request: Request):
    req = await request.json()
    regions = req.get("regions", [])
    services = req.get("services", [])
    threshold = req.get("threshold_ms", 180)

    result = {}
    for region in regions:
        query_parts = ["region == @region"]
        if services:
            query_parts.append("service in @services")

        region_df = telemetry_df.query(" and ".join(query_parts))

        if region_df.empty:
            result[region] = {"avg_latency": 0, "p95_latency": 0, "avg_uptime": 0, "breaches": 0}
            continue

        latencies = region_df["latency_ms"]
        uptimes = region_df["uptime"]
        breaches = (latencies > threshold).sum()

        avg_latency = round(latencies.mean(), 2) if not latencies.empty else 0
        p95_latency = round(latencies.quantile(0.95), 2) if not latencies.empty else 0
        avg_uptime = round(uptimes.mean(), 3) if not uptimes.empty else 0

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": int(breaches)
        }

    return result