
from flask import Flask, jsonify, request
import os, sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
DB = Path(os.getenv("MMX_DB_PATH", Path(__file__).parent / "mmx_v5.db"))

def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def token_ok():
    expected = os.getenv("MMX_API_TOKEN", "")
    supplied = request.headers.get("X-MMX-API-TOKEN", "")
    return bool(expected) and supplied == expected

@app.get("/health")
def health():
    return jsonify({"status":"ok","service":"MMX Intelligence API","timestamp":datetime.utcnow().isoformat()+"Z"})

@app.before_request
def auth():
    if request.path == "/health":
        return
    if not token_ok():
        return jsonify({"error":"Unauthorized"}), 401

@app.get("/api/v1/portfolio")
def portfolio():
    c=connect()
    policies=c.execute("SELECT status, COUNT(*) policies, COALESCE(SUM(premium),0) premium FROM policies GROUP BY status").fetchall()
    c.close()
    return jsonify([dict(x) for x in policies])

@app.get("/api/v1/alerts")
def alerts():
    c=connect()
    rows=c.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 200").fetchall()
    c.close()
    return jsonify([dict(x) for x in rows])

@app.post("/api/v1/ingest/claim")
def ingest_claim():
    payload=request.get_json(force=True)
    required=["claim_no","policy_id","claim_date","claim_cost","severity","status","fraud_score"]
    missing=[x for x in required if x not in payload]
    if missing:
        return jsonify({"error":"Missing fields","fields":missing}),400
    c=connect()
    c.execute("""INSERT OR REPLACE INTO claims
        (claim_no,policy_id,claim_date,claim_cost,severity,status,fraud_score)
        VALUES(?,?,?,?,?,?,?)""",
        tuple(payload[x] for x in required))
    c.commit(); c.close()
    return jsonify({"accepted":True,"claim_no":payload["claim_no"]}),201

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("MMX_API_PORT","8080")))
