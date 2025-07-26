from redis import Redis
from rq import Queue
from tasks import say_hello

q = Queue("default", connection=Redis())
job = q.enqueue(say_hello, "Sid")
print("Job ID:", job.id)

