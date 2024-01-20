import os 
from celery import Celery
from kombu import Exchange, Queue
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sleety.settings")
app = Celery("sleety")
app.config_from_object("django.conf:settings", namespace="CELERY")


# app.conf.task_queues = [
#     Queue('tasks', Exchange('tasks'), routing_key='tasks',
#           queue_arguments={'x-max-priority': 10}),
#     Queue('dead_letter', routing_key='dead_letter')
# ]

app.conf.task_acks_late = True # tasks will be acknowledged after they are executed, not before
app.conf.task_default_priority = 5  # default priority of all tasks
app.conf.worker_prefetch_multiplier = 1 # number of tasks a worker can prefetch at a time
app.conf.worker_concurrency = 1 #number of worker processes celery will spawn

base_dir = os.getcwd()
task_folder = os.path.join(base_dir, 'sleety', 'celery_tasks')

if os.path.exists(task_folder) and os.path.isdir(task_folder):
    task_modules = []
    for filename in os.listdir(task_folder):
        if filename.startswith('ex') and filename.endswith('.py'):
            module_name = f'sleety.celery_tasks.{filename[:-3]}'

            module = __import__(module_name, fromlist=['*'])

            for name in dir(module):
                obj = getattr(module, name)
                if callable(obj):
                    task_modules.append(f'{module_name}.{name}')
   

    app.autodiscover_tasks(task_modules)

app.autodiscover_tasks()
