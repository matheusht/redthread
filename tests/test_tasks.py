"""Tests for the Task state machine."""

from __future__ import annotations

import pytest

from redthread.tasks.base import Task, TaskStatus, TaskType, generate_task_id


def test_generate_task_id_format() -> None:
    task_id = generate_task_id(TaskType.ATTACK_RUN)
    assert task_id.startswith("attack_run-")
    assert len(task_id) == len("attack_run-") + 6


def test_generate_task_id_uniqueness() -> None:
    ids = {generate_task_id(TaskType.CAMPAIGN) for _ in range(100)}
    assert len(ids) == 100  # All unique


def test_task_initial_state() -> None:
    task = Task.create(TaskType.CAMPAIGN)
    assert task.status == TaskStatus.PENDING
    assert task.type == TaskType.CAMPAIGN
    assert task.result is None
    assert task.error is None
    assert not task.is_terminal


def test_task_start_transition() -> None:
    task = Task.create(TaskType.ATTACK_RUN)
    task.start()
    assert task.status == TaskStatus.RUNNING
    assert task._start_time is not None


def test_task_complete_transition() -> None:
    task = Task.create(TaskType.JUDGE_EVAL)
    task.start()
    task.complete(result={"score": 4.2})
    assert task.status == TaskStatus.COMPLETED
    assert task.result == {"score": 4.2}
    assert task.is_terminal


def test_task_fail_transition() -> None:
    task = Task.create(TaskType.ATTACK_RUN)
    task.start()
    task.fail("Connection timeout")
    assert task.status == TaskStatus.FAILED
    assert task.error == "Connection timeout"
    assert task.is_terminal


def test_task_kill_from_pending() -> None:
    task = Task.create(TaskType.CAMPAIGN)
    task.kill()
    assert task.status == TaskStatus.KILLED
    assert task.is_terminal


def test_invalid_transition_completed_to_running() -> None:
    task = Task.create(TaskType.ATTACK_RUN)
    task.start()
    task.complete()
    with pytest.raises(ValueError, match="Invalid transition"):
        task.start()  # Cannot restart a completed task


def test_invalid_transition_pending_to_completed() -> None:
    task = Task.create(TaskType.ATTACK_RUN)
    with pytest.raises(ValueError, match="Invalid transition"):
        task.complete()  # Must go through RUNNING first


def test_task_duration() -> None:
    import time

    task = Task.create(TaskType.DREAM)
    assert task.duration_seconds is None  # Not started

    task.start()
    time.sleep(0.05)
    task.complete()

    assert task.duration_seconds is not None
    assert task.duration_seconds >= 0.05
