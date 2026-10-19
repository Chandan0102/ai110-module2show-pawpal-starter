"""PawPal+ logic layer: class skeletons (no logic yet)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from typing import Optional


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    category: str = "general"  # walk, feeding, meds, enrichment, grooming
    preferred_time: Optional[str] = None  # e.g. "morning"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def priority_value(self) -> int:
        """Return a numeric priority (1-3) for sorting."""
        pass

    def __str__(self) -> str:
        """Human-readable description of the task."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: Optional[int] = None
    special_needs: Optional[str] = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        pass

    def edit_task(self, title: str, **changes) -> None:
        """Update fields of the task with the given title."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, name: str) -> None:
        """Remove the pet with the given name."""
        pass

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task across all pets, paired with its pet."""
        pass


@dataclass
class ScheduledItem:
    task: Task
    pet: Pet
    start: time
    end: time
    reason: str = ""


@dataclass
class SkippedTask:
    task: Task
    pet: Pet
    reason: str


@dataclass
class DailyPlan:
    plan_date: date = field(default_factory=date.today)
    entries: list[ScheduledItem] = field(default_factory=list)
    skipped: list[SkippedTask] = field(default_factory=list)
    total_minutes: int = 0

    def add_entry(self, item: ScheduledItem) -> None:
        """Append a scheduled item to the plan."""
        pass

    def add_skipped(self, task: Task, pet: Pet, reason: str) -> None:
        """Record a task that did not fit, with the reason."""
        pass

    def summary(self) -> str:
        """Short overview of the plan."""
        pass

    def explain(self) -> str:
        """Explain why tasks were included or skipped."""
        pass


class Scheduler:
    def __init__(self, owner: Owner, start_time: time = time(8, 0)) -> None:
        self.owner = owner
        self.start_time = start_time

    def generate_plan(self) -> DailyPlan:
        """Build the daily plan for the owner's pets."""
        pass

    def _sort_tasks(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order tasks by priority (then duration / preferred time)."""
        pass

    def _fit_to_time(
        self, tasks: list[tuple[Pet, Task]]
    ) -> tuple[list[tuple[Pet, Task]], list[SkippedTask]]:
        """Split tasks into those that fit the available time and those skipped."""
        pass

    def _assign_times(self, tasks: list[tuple[Pet, Task]]) -> list[ScheduledItem]:
        """Give each chosen task a start and end time."""
        pass

    def _explain(self, task: Task, reason: str) -> str:
        """Build the explanation text for one task decision."""
        pass
