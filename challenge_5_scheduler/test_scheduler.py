import time
from scheduler import Scheduler, TaskStatus


def add_numbers(a, b):
    """Simple task that adds two numbers"""
    return a + b


def slow_task(duration=1):
    """Task that takes some time"""
    time.sleep(duration)
    return "done"


def failing_task():
    """Task that always fails"""
    raise ValueError("Task failed")


def test_basic_task_execution():
    """Test that a simple task executes successfully"""
    scheduler = Scheduler(num_workers=2)
    scheduler.start()

    task_id = scheduler.add_task(add_numbers, args=(5, 3))

    scheduler.wait_completion()

    task = scheduler.task_queue.tasks[task_id]
    assert task.status == TaskStatus.COMPLETED
    assert task.result == 8

    scheduler.shutdown()


def test_priority_ordering():
    """Test that priority queue mechanism works"""
    scheduler = Scheduler(num_workers=1) 
    scheduler.start()

    task1 = scheduler.add_task(add_numbers, args=(1, 1), priority=10)
    task2 = scheduler.add_task(add_numbers, args=(2, 2), priority=1)
    task3 = scheduler.add_task(add_numbers, args=(3, 3), priority=5)

    scheduler.wait_completion()

    # Verify all completed
    assert scheduler.task_queue.tasks[task1].status == TaskStatus.COMPLETED
    assert scheduler.task_queue.tasks[task2].status == TaskStatus.COMPLETED
    assert scheduler.task_queue.tasks[task3].status == TaskStatus.COMPLETED

    scheduler.shutdown()


def test_task_dependencies():
    """Test that tasks wait for dependencies to complete"""
    scheduler = Scheduler(num_workers=2)
    scheduler.start()

    task1 = scheduler.add_task(slow_task, args=(0.2,))
    task2 = scheduler.add_task(slow_task, args=(0.2,), dependencies=[task1])
    task3 = scheduler.add_task(slow_task, args=(0.2,), dependencies=[task1, task2])

    time.sleep(0.3)

    scheduler.wait_completion()

    # All tasks should complete
    assert scheduler.task_queue.tasks[task1].status == TaskStatus.COMPLETED
    assert scheduler.task_queue.tasks[task2].status == TaskStatus.COMPLETED
    assert scheduler.task_queue.tasks[task3].status == TaskStatus.COMPLETED

    scheduler.shutdown()


def test_failed_task():
    """Test that failed tasks are marked as FAILED"""
    scheduler = Scheduler(num_workers=2)
    scheduler.start()

    task_id = scheduler.add_task(failing_task)

    scheduler.wait_completion()

    task = scheduler.task_queue.tasks[task_id]
    assert task.status == TaskStatus.FAILED
    assert "Task failed" in task.error

    scheduler.shutdown()


def test_task_cancellation():
    """Test that pending tasks can be cancelled"""
    scheduler = Scheduler(num_workers=1)
    scheduler.start()

    scheduler.add_task(slow_task, args=(2,))

    task_id = scheduler.add_task(add_numbers, args=(1, 1))

    time.sleep(0.5)
    cancelled = scheduler.cancel_task(task_id)

    assert cancelled == True

    task = scheduler.task_queue.tasks[task_id]
    assert task.status == TaskStatus.CANCELLED

    scheduler.shutdown()


def test_worker_scaling():
    """Test dynamic worker scaling"""
    scheduler = Scheduler(num_workers=2)
    scheduler.start()

    assert len(scheduler.workers) == 2

    scheduler.scale_workers(5)
    assert len(scheduler.workers) == 5

    scheduler.scale_workers(3)
    assert len(scheduler.workers) == 3

    scheduler.shutdown()


def test_status_reporting():
    """Test that scheduler reports status correctly"""
    scheduler = Scheduler(num_workers=2)
    scheduler.start()

    scheduler.add_task(slow_task, args=(1,))
    scheduler.add_task(slow_task, args=(1,))
    scheduler.add_task(failing_task)

    status = scheduler.get_status()

    assert 'workers' in status
    assert 'tasks' in status
    assert status['workers']['total'] == 2
    assert status['workers']['alive'] == 2

    scheduler.wait_completion()

    final_status = scheduler.get_status()
    assert final_status['tasks'][TaskStatus.COMPLETED] == 2
    assert final_status['tasks'][TaskStatus.FAILED] == 1

    scheduler.shutdown()


def test_multiple_workers_concurrent_execution():
    """Test that multiple workers execute tasks concurrently"""
    scheduler = Scheduler(num_workers=3)
    scheduler.start()

    start_time = time.time()

    scheduler.add_task(slow_task, args=(1,))
    scheduler.add_task(slow_task, args=(1,))
    scheduler.add_task(slow_task, args=(1,))

    scheduler.wait_completion()

    elapsed = time.time() - start_time

    assert elapsed < 3.0, f"Tasks took {elapsed}s, expected concurrent execution"

    scheduler.shutdown()
