import multiprocessing
import queue
import time
import uuid
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"          
    RUNNING = "running"          
    COMPLETED = "completed"      
    FAILED = "failed"            # Task failed during execution
    CANCELLED = "cancelled"      # Task was cancelled before completion
    TIMEOUT = "timeout"          


class Task:
    """
    Represents a single task to be executed by the scheduler.
    """
    def __init__(self, func=None, args=(), kwargs=None, priority=5,
                 dependencies=None, timeout=None):
        self.func = func

        self.args = args
        self.kwargs = kwargs if kwargs is not None else {}

        self.priority = priority

        self.dependencies = dependencies if dependencies is not None else []

        self.timeout = timeout

        self.task_id = str(uuid.uuid4())

        self.status = TaskStatus.PENDING

        self.result = None
        self.error = None

    def __lt__(self, other):
        return self.priority < other.priority


class TaskQueue:
    """
    Priority queue for managing tasks across multiple processes.
    """

    def __init__(self):
        self.queue = multiprocessing.Queue()

        manager = multiprocessing.Manager()
        self.tasks = manager.dict()

        self.completed_tasks = manager.list()

        self.cancelled_tasks = manager.list()

        self.queued_tasks = manager.list()

    def add_task(self, task):
        """
        Add a task to the queue. Tasks with dependencies are held back
        until their dependencies complete.
        """
        self.tasks[task.task_id] = task

        task.status = TaskStatus.PENDING

        # Check if all dependencies are satisfied
        if self._dependencies_satisfied(task):
            self.queue.put(task)
            self.queued_tasks.append(task.task_id)

    def _dependencies_satisfied(self, task):
        """
        Check if all task dependencies have completed.
        """
        if not task.dependencies:
            return True

        # Check if all dependency IDs are in completed list
        return all(dep_id in self.completed_tasks for dep_id in task.dependencies)

    def get_task(self, timeout=1):
        """
        Get next task from queue. Blocks for up to 'timeout' seconds.
        """
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def mark_completed(self, task_id):
        """
        Mark a task as completed and check if any pending tasks
        """
        # Add to completed list
        self.completed_tasks.append(task_id)

        # Check all pending tasks to see if they can now be queued
        self._check_pending_tasks()

    def _check_pending_tasks(self):
        """
        Iterate through all pending tasks and queue any whose
        """
        for task_id, task in list(self.tasks.items()):
            # Check if task is pending AND not already queued
            if task.status == TaskStatus.PENDING and task_id not in self.queued_tasks:
                if self._dependencies_satisfied(task):
                    # Task stays PENDING but now enters queue
                    self.queue.put(task)
                    self.queued_tasks.append(task_id)

    def cancel_task(self, task_id):
        """
        Cancel a task. Only works if task is still pending.
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                self.tasks[task_id] = task  # Update in shared dict
                self.cancelled_tasks.append(task_id)
                return True
        return False

    def get_status(self):
        """
        Get current status of all tasks grouped by status.
        """
        status_counts = {status: 0 for status in TaskStatus}
        for task in self.tasks.values():
            status_counts[task.status] += 1
        return status_counts


def worker_process(task_queue, worker_id):
    """
    Worker function that runs in a separate process.
    """
    print(f"Worker {worker_id} started")

    while True:
        # Get next task from queue (blocks for 1 second)
        task = task_queue.get_task(timeout=1)

        if task is None:
            # No task available, continue waiting
            continue

        # Check if task was cancelled while in queue
        if task.task_id in task_queue.cancelled_tasks:
            print(f"Worker {worker_id}: Task {task.task_id} was cancelled")
            continue

        # Mark task as running - update in shared dict
        task.status = TaskStatus.RUNNING
        task_queue.tasks[task.task_id] = task
        print(f"Worker {worker_id}: Executing task {task.task_id} (priority {task.priority})")

        try:
            if task.timeout:
                start_time = time.time()
                result = task.func(*task.args, **task.kwargs)
                elapsed = time.time() - start_time

                if elapsed > task.timeout:
                    raise TimeoutError(f"Task exceeded timeout of {task.timeout}s")
            else:
                result = task.func(*task.args, **task.kwargs)

            task.result = result
            task.status = TaskStatus.COMPLETED
            task_queue.tasks[task.task_id] = task
            task_queue.mark_completed(task.task_id)
            print(f"Worker {worker_id}: Task {task.task_id} completed successfully")

        except TimeoutError as e:
            task.error = str(e)
            task.status = TaskStatus.TIMEOUT
            task_queue.tasks[task.task_id] = task
            print(f"Worker {worker_id}: Task {task.task_id} timed out")

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            task_queue.tasks[task.task_id] = task
            print(f"Worker {worker_id}: Task {task.task_id} failed: {e}")


class Scheduler:
    def __init__(self, num_workers=4):
        """
        Initialize scheduler with specified number of worker processes.
        """
        self.task_queue = TaskQueue()

        self.workers = []

        self.target_num_workers = num_workers

        self.running = False

    def start(self):
        """
        Start the scheduler and spawn worker processes.
        """
        self.running = True

        for i in range(self.target_num_workers):
            self._spawn_worker(i)

        print(f"Scheduler started with {self.target_num_workers} workers")

    def _spawn_worker(self, worker_id):
        worker = multiprocessing.Process(
            target=worker_process,
            args=(self.task_queue, worker_id),
            daemon=True 
        )
        worker.start()
        self.workers.append(worker)

    def add_task(self, func, args=(), kwargs=None, priority=5, dependencies=None, timeout=None):
        """
        Add a new task to the scheduler.
        """
        kwargs = kwargs or {}
        dependencies = dependencies or []

        task = Task(
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            dependencies=dependencies,
            timeout=timeout
        )

        self.task_queue.add_task(task)

        return task.task_id

    def cancel_task(self, task_id):
        return self.task_queue.cancel_task(task_id)

    def scale_workers(self, num_workers):
        """
        Dynamically scale the number of workers up or down.
        """
        current_workers = len(self.workers)

        if num_workers > current_workers:
            # Scale up - spawn additional workers
            for i in range(current_workers, num_workers):
                self._spawn_worker(i)
            print(f"Scaled up to {num_workers} workers")

        elif num_workers < current_workers:
            # Scale down - terminate excess workers
            workers_to_remove = current_workers - num_workers
            for _ in range(workers_to_remove):
                worker = self.workers.pop()
                worker.terminate()
                worker.join()
            print(f"Scaled down to {num_workers} workers")

        self.target_num_workers = num_workers

    def monitor_workers(self):
        """
        Check worker health and restart any that have died.
        Should be called periodically by the main process.
        """
        for i, worker in enumerate(self.workers):
            if not worker.is_alive():
                # Worker died - restart it
                print(f"Worker {i} died, restarting...")
                worker.join()  # Clean up dead process
                self.workers[i] = multiprocessing.Process(
                    target=worker_process,
                    args=(self.task_queue, i),
                    daemon=True
                )
                self.workers[i].start()

    def get_status(self):
        """
        Get current status of scheduler including task counts and worker status.
        """
        task_status = self.task_queue.get_status()

        return {
            'workers': {
                'total': len(self.workers),
                'alive': sum(1 for w in self.workers if w.is_alive())
            },
            'tasks': task_status
        }

    def wait_completion(self, check_interval=1):
        """
        Block until all tasks are completed.
        Continuously monitors workers and checks task status.
        """
        while True:
            self.monitor_workers()

            status = self.task_queue.get_status()
            pending = status[TaskStatus.PENDING]
            running = status[TaskStatus.RUNNING]

            if pending == 0 and running == 0:
                # All tasks completed
                break

            # Sleep before next check
            time.sleep(check_interval)

    def shutdown(self):
        """
        Shutdown scheduler and terminate all workers.
        """
        print("Shutting down scheduler...")
        self.running = False

        # Terminate all workers
        for worker in self.workers:
            worker.terminate()
            worker.join()

        print("Scheduler shutdown complete")


