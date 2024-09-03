from huey import RedisHuey

from overschool import settings

huey = RedisHuey(url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/3")
