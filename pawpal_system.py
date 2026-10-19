"""PawPal+ logic layer: Task, Pet, Owner, Scheduler and supporting classes."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4

TIME_OF_DAY_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}
FREQUENCIES = ("once", "daily", "weekly")


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @classmethod
    def from_str(cls, value: str) -> Priority:
        """Convert a UI string like 'high' into a Priority."""
        try:
            return cls[value.strip().upper()]
        except KeyError:
            raise ValueError(f"Unknown priority: {value!r}") from None


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    category: str = "general"  # walk, feeding, meds, enrichment, grooming
    preferred_time: Optional[str] = None  # "morning", "afternoon" or "evening"
    frequency: str = "daily"  # "once", "daily" or "weekly"
    completed: bool = False
    task_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        """Validate duration and frequency."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {FREQUENCIES}")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def priority_value(self) -> int:
        """Return a numeric priority (1-3) for sorting."""
        return self.priority.value

    def __str__(self) -> str:
        """Return a one-line description of the task."""
        status = "done" if self.completed else "pending"
        return (
            f"{self.title} ({self.duration_minutes} min, "
            f"{self.priority.name.lower()} priority, {self.frequency}, {status})"
        )


@dataclass
class Pet:
    name: str
    species: str
    age: Optional[int] = None
    special_needs: Optional[str] = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def edit_task(self, task_id: str, **changes) -> None:
        """Update fields of the task with the given id."""
        task = self._find_task(task_id)
        valid = {f.name for f in fields(Task)} - {"task_id"}
        for name, value in changes.items():
            if name not in valid:
                raise AttributeError(f"Task has no editable field {name!r}")
            setattr(task, name, value)
        task.__post_init__()  # re-validate

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id."""
        self.tasks.remove(self._find_task(task_id))

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's tasks."""
        return list(self.tasks)

    def _find_task(self, task_id: str) -> Task:
        """Return the task with the given id or raise KeyError."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"No task with id {task_id!r} for pet {self.name!r}")


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove the pet with the given name."""
        for pet in self.pets:
            if pet.name == name:
                self.pets.remove(pet)
                return
        raise KeyError(f"No pet named {name!r}")

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task across all pets, paired with its pet."""
        return [(pet, task) for pet in self.pets for task in pet.get_tasks()]


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

    @property
    def total_minutes(self) -> int:
        """Total scheduled minutes, derived from entries."""
        return sum(item.task.duration_minutes for item in self.entries)

    def add_entry(self, item: ScheduledItem) -> None:
        """Append a scheduled item to the plan."""
        self.entries.append(item)

    def add_skipped(self, task: Task, pet: Pet, reason: str) -> None:
        """Record a task that did not fit, with the reason."""
        self.skipped.append(SkippedTask(task, pet, reason))

    def summary(self) -> str:
        """Short overview of the plan."""
        lines = [f"Plan for {self.plan_date:%Y-%m-%d}"]
        for item in self.entries:
            lines.append(
                f"  {item.start:%H:%M}-{item.end:%H:%M}  {item.pet.name}: "
                f"{item.task.title} ({item.task.duration_minutes} min) "
                f"[{item.task.priority.name.lower()}]"
            )
        if not self.entries:
            lines.append("  Nothing scheduled.")
        lines.append(f"Total: {self.total_minutes} min, {len(self.skipped)} skipped")
        return "\n".join(lines)

    def explain(self) -> str:
        """Explain why tasks were included or skipped."""
        lines = []
        for item in self.entries:
            lines.append(f"Included {item.pet.name} - {item.task.title}: {item.reason}")
        for skipped in self.skipped:
            lines.append(
                f"Skipped {skipped.pet.name} - {skipped.task.title}: {skipped.reason}"
            )
        return "\n".join(lines) if lines else "No tasks to explain."


class Scheduler:
    def __init__(self, owner: Owner, start_time: time = time(8, 0)) -> None:
        """Create a scheduler for an owner, starting the day at start_time."""
        self.owner = owner
        self.start_time = start_time

    def generate_plan(self) -> DailyPlan:
        """Build the daily plan from all of the owner's pets' tasks."""
        # Read through the Owner so every pet is covered, not just one.
        pending = [(p, t) for p, t in self.owner.get_all_tasks() if not t.completed]
        ordered = self._sort_tasks(pending)
        fitted, skipped = self._fit_to_time(ordered)

        plan = DailyPlan()
        for item in self._assign_times(fitted):
            plan.add_entry(item)
        for entry in skipped:
            plan.skipped.append(entry)
        return plan

    def _sort_tasks(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order by priority (high first), then time of day, then shorter first."""

        def key(pair: tuple[Pet, Task]):
            """Sort key: priority desc, time of day, duration asc."""
            _, task = pair
            tod = TIME_OF_DAY_ORDER.get(task.preferred_time or "", len(TIME_OF_DAY_ORDER))
            return (-task.priority_value(), tod, task.duration_minutes)

        return sorted(tasks, key=key)

    def _fit_to_time(
        self, tasks: list[tuple[Pet, Task]]
    ) -> tuple[list[tuple[Pet, Task]], list[SkippedTask]]:
        """Split tasks into those that fit the available time and those skipped."""
        remaining = self.owner.available_minutes
        fitted: list[tuple[Pet, Task]] = []
        skipped: list[SkippedTask] = []
        for pet, task in tasks:
            if task.duration_minutes <= remaining:
                fitted.append((pet, task))
                remaining -= task.duration_minutes
            else:
                reason = (
                    f"needs {task.duration_minutes} min but only {remaining} min "
                    f"of the {self.owner.available_minutes} min budget remained"
                )
                skipped.append(SkippedTask(task, pet, reason))
        return fitted, skipped

    def _assign_times(self, tasks: list[tuple[Pet, Task]]) -> list[ScheduledItem]:
        """Give each chosen task a back-to-back start and end time."""
        cursor = datetime.combine(date.today(), self.start_time)
        items: list[ScheduledItem] = []
        for pet, task in tasks:
            end = cursor + timedelta(minutes=task.duration_minutes)
            items.append(
                ScheduledItem(
                    task=task,
                    pet=pet,
                    start=cursor.time(),
                    end=end.time(),
                    reason=self._explain(task, "fits within the available time"),
                )
            )
            cursor = end
        return items

    def _explain(self, task: Task, reason: str) -> str:
        """Build the explanation text for one task decision."""
        return f"{task.priority.name.lower()} priority, {reason}"
