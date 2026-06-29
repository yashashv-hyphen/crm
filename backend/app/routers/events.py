import asyncio
import json
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.config import settings
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/events", tags=["events"])
logger = logging.getLogger(__name__)

CHANNEL = "crm:upload_complete"
KEEPALIVE_INTERVAL = 25.0  # seconds
POLL_SLEEP = 0.5           # seconds between get_message calls


@router.get("/stream")
async def event_stream(current_user: User = Depends(get_current_user)):
    """Server-Sent Events stream. Pushes upload_complete events to authenticated clients."""

    async def generator():
        r = aioredis.from_url(settings.redis_url)
        pubsub = r.pubsub()
        await pubsub.subscribe(CHANNEL)
        last_keepalive = asyncio.get_event_loop().time()

        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                now = asyncio.get_event_loop().time()

                if now - last_keepalive >= KEEPALIVE_INTERVAL:
                    yield ": keepalive\n\n"
                    last_keepalive = now

                if message and message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                    except (json.JSONDecodeError, TypeError):
                        continue

                    if current_user.role == "admin" or str(current_user.id) in data.get("fos_ids", []):
                        yield f"data: {json.dumps(data)}\n\n"
                else:
                    await asyncio.sleep(POLL_SLEEP)

        except (asyncio.CancelledError, GeneratorExit):
            pass
        except Exception as exc:
            logger.warning("SSE generator error: %s", exc)
        finally:
            try:
                await pubsub.unsubscribe(CHANNEL)
                await pubsub.aclose()
                await r.aclose()
            except Exception:
                pass

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
