import os
from datetime import datetime
from typing import Optional
import redis
from fastapi import HTTPException, Header


class RateLimiter:
    def __init__(self):
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )

    def _get_normal_key(self, user_id: str) -> str:
        return f"rate_limit:normal:{user_id}"

    def _get_priority_key(self, user_id: str) -> str:
        return f"rate_limit:priority:{user_id}"

    def check_rate_limit(
        self,
        x_user_id: str = Header(..., description="User ID for rate limiting"),
        x_priority_request: Optional[str] = Header(None, description="Priority request flag")
    ) -> str:
        is_priority = x_priority_request and x_priority_request.lower() == "true"

        if is_priority:
            priority_key = self._get_priority_key(x_user_id)
            priority_count = self.redis_client.get(priority_key)

            if priority_count and int(priority_count) >= 2:
                raise HTTPException(
                    status_code=429,
                    detail="Priority request limit exceeded. Maximum 2 priority requests per hour."
                )

            pipe = self.redis_client.pipeline()
            pipe.incr(priority_key)
            pipe.expire(priority_key, 3600)
            pipe.execute()

            return x_user_id

        else:
            normal_key = self._get_normal_key(x_user_id)
            current_minute = datetime.utcnow().strftime("%Y-%m-%d-%H-%M")
            minute_key = f"{normal_key}:{current_minute}"

            request_count = self.redis_client.get(minute_key)

            if request_count and int(request_count) >= 5:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Maximum 5 requests per minute."
                )

            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.execute()

            return x_user_id


rate_limiter = RateLimiter()
