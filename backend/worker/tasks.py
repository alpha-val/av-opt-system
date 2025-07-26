from rq import Worker, Queue, Connection
from redis import Redis

listen = ["default"]
redis_url = "redis://localhost:6379"  # Update Redis URL if needed

conn = Redis.from_url(redis_url)

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()