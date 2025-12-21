# 레디스 사용 시 기본 설정
import redis.asyncio as redis
import os

from dotenv import load_dotenv

load_dotenv()

redis_client = None

async def init_redis():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

async def close_redis():
    global redis_client

    if redis_client:
        await redis_client.close()
    
async def get_cached_style(file_hash: str):
    if redis_client:
        return await redis_client.get(file_hash)
    return None

async def set_cached_style(file_hash: str, style_result: str, expire: int = 60 * 60 * 24):
    if redis_client:
        await redis_client.set(file_hash, style_result, ex=expire)
