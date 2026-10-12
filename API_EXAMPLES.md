
# API examples

## Health
curl http://localhost:8080/health

## Portfolio
curl -H "X-MMX-API-TOKEN: YOUR_TOKEN" http://localhost:8080/api/v1/portfolio

## Alerts
curl -H "X-MMX-API-TOKEN: YOUR_TOKEN" http://localhost:8080/api/v1/alerts

## Claim ingestion
curl -X POST http://localhost:8080/api/v1/ingest/claim \
  -H "Content-Type: application/json" \
  -H "X-MMX-API-TOKEN: YOUR_TOKEN" \
  -d '{"claim_no":"CLM-NEW-001","policy_id":1,"claim_date":"2026-10-12","claim_cost":25000,"severity":"High","status":"Open","fraud_score":71}'
