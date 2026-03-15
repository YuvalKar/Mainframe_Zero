import asyncio
import abc

# The Base Worker Architecture
class BaseWorker(abc.ABC):
    def __init__(self, name: str):
        self.name = name
        self.queue = asyncio.Queue()
        self.is_running = False

    async def add_task(self, task_data: dict) -> asyncio.Future:
        """
        Adds a new task to the agent's queue without blocking the main thread.
        Returns an asyncio.Future that the caller can await to get the result.
        """
        # Create a "beeper" (Future) for this specific task
        loop = asyncio.get_running_loop()
        task_future = loop.create_future()
        
        # Attach the beeper to the task data so the worker can ring it later
        task_data["_future"] = task_future
        
        await self.queue.put(task_data)
        print(f"[{self.name}] Task queued.")
        
        # Hand the beeper back to the caller
        return task_future

    async def start(self):
        """
        The continuous background loop. Waits for tasks and processes them.
        """
        self.is_running = True
        print(f"[{self.name}] Agent is online and listening...")
        
        while self.is_running:
            # Non-blocking wait for the next item in the queue
            task_data = await self.queue.get()
            
            # Extract the beeper from the task data
            task_future = task_data.pop("_future", None)
            
            try:
                # Execute the specific logic defined in the child class
                result = await self.process_task(task_data)
                
                # Ring the beeper with the result!
                if task_future and not task_future.done():
                    task_future.set_result(result)
                    
            except Exception as e:
                print(f"[{self.name}] Error processing task: {e}")
                # If something goes wrong, pass the error to the caller
                if task_future and not task_future.done():
                    task_future.set_exception(e)
            finally:
                # Notify the queue that the task is complete
                self.queue.task_done()

    @abc.abstractmethod
    async def process_task(self, task_data: dict):
        """
        Must be implemented by the specific agent subclass.
        """
        pass