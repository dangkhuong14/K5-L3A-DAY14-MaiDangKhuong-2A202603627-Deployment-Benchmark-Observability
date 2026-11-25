# Deployment

## Public URL
https://lab14-ai20k-agent.onrender.com

## Platform
Render Free · Singapore

## Test Commands
```bash
BASE=https://lab14-ai20k-agent.onrender.com
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/health"  # 200
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/ready"   # 200
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H 'Content-Type: application/json' -d '{"question":"Hello"}'  # 401
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H 'Content-Type: application/json' -H "X-API-Key: $AGENT_API_KEY" -d '{"question":"Hello"}'  # 200
```

## Environment Variables Set
- `AGENT_API_KEY`
- `REDIS_URL`

## Screenshots
- [Dashboard — agent và Key Value](screenshots/dashboard.png)
- [Deployment Live](screenshots/running.png)
- [Terminal — bốn phép thử HTTP](screenshots/test.png)
