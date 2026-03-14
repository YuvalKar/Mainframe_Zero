import asyncio
import abc

# The Base Worker Architecture
class BaseWorker(abc.ABC):
    def __init__(self, name: str):
        self.name = name
        self.queue = asyncio.Queue()
        self.is_running = False

    async def add_task(self, task_data: dict):
        """
        Adds a new task to the agent's queue without blocking the main thread.
        """
        await self.queue.put(task_data)
        print(f"[{self.name}] Task queued.")

    async def start(self):
        """
        The continuous background loop. Waits for tasks and processes them.
        """
        self.is_running = True
        print(f"[{self.name}] Agent is online and listening...")
        
        while self.is_running:
            # Non-blocking wait for the next item in the queue
            task = await self.queue.get()
            
            try:
                # Execute the specific logic defined in the child class
                await self.process_task(task)
            except Exception as e:
                print(f"[{self.name}] Error processing task: {e}")
            finally:
                # Notify the queue that the task is complete
                self.queue.task_done()

    @abc.abstractmethod
    async def process_task(self, task_data: dict):
        """
        Must be implemented by the specific agent subclass.
        """
        pass
