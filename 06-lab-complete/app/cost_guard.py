from datetime import datetime, timezone

from fastapi import HTTPException
from utils.mock_llm import MOCK_RESPONSES

from .config import settings
from .redis_client import r

# Estimated tokens for the mock model. Prices are integer nano-USD per token.
INPUT_PRICE = 150
OUTPUT_PRICE = 600


def tokens(text: str) -> int:
    return max(1, len(text.split()) * 2)


MAX_OUTPUT = max(tokens(reply) for replies in MOCK_RESPONSES.values() for reply in replies)
reserve = r.register_script("""
local spent = tonumber(redis.call('GET', KEYS[1]) or 0)
if spent + tonumber(ARGV[1]) > tonumber(ARGV[2]) then return 0 end
redis.call('INCRBY', KEYS[1], ARGV[1])
redis.call('EXPIRE', KEYS[1], 172800)
return 1
""")


def check_budget(question: str) -> tuple[str, int]:
    day = datetime.now(timezone.utc).date().isoformat()
    key = f"agent:cost:{day}"
    amount = tokens(question) * INPUT_PRICE + MAX_OUTPUT * OUTPUT_PRICE
    if not reserve(keys=[key], args=[amount, int(settings.daily_budget_usd * 10**9)]):
        raise HTTPException(402, "Insufficient daily budget")
    return key, amount


def record_cost(key: str, reserved: int, input_tokens: int, output_tokens: int) -> None:
    actual = input_tokens * INPUT_PRICE + output_tokens * OUTPUT_PRICE
    r.incrby(key, actual - reserved)
