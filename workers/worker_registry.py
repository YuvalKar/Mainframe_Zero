# core_utils/worker_registry.py

# A global, neutral dictionary to hold references to our active background workers
active_workers = {}

# We can also move worker_tasks here to keep things organized
worker_tasks = []