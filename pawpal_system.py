"""PawPal+ logic layer: Task, Pet, Owner, Scheduler and supporting classes."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields, replace
from datetime import date, datetime, time, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Union
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
    start_time: Optional[str] = None  # fixed time of day as "HH:MM"
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    task_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        """Validate duration and frequency."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {FREQUENCIES}")
        if self.start_time is not None:
            # Normalise to zero-padded "HH:MM" so plain string sorting is correct.
            try:
                parsed = datetime.strptime(self.start_time, "%H:%M")
            except ValueError:
                raise ValueError("start_time must look like 'HH:MM'") from None
            self.start_time = parsed.strftime("%H:%M")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> Optional[Task]:
        """Return a fresh copy due on the next occurrence, or None if one-off."""
        days = {"daily": 1, "weekly": 7}.get(self.frequency)
        if days is None:
            return None
        return replace(
            self,
            completed=False,
            due_date=date.today() + timedelta(days=days),
            task_id=uuid4().hex,
        )

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict (enum by name, date as ISO string)."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.name,
            "category": self.category,
            "preferred_time": self.preferred_time,
            "frequency": self.frequency,
            "start_time": self.start_time,
            "due_date": self.due_date.isoformat(),
            "completed": self.completed,
            "task_id": self.task_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Rebuild a Task from to_dict() output, re-running validation."""
        return cls(
            title=data["title"],
            duration_minutes=data["duration_minutes"],
            priority=Priority[data["priority"]],
            category=data.get("category", "general"),
            preferred_time=data.get("preferred_time"),
            frequency=data.get("frequency", "daily"),
            start_time=data.get("start_time"),
            due_date=date.fromisoformat(data["due_date"]),
            completed=data.get("completed", False),
            task_id=data["task_id"],
        )

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
        for name in changes:
            if name not in valid:
                raise AttributeError(f"Task has no editable field {name!r}")
        # Build a validated copy first so a bad value leaves the task untouched.
        candidate = replace(task, **changes)
        for f in fields(Task):
            setattr(task, f.name, getattr(candidate, f.name))

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id."""
        self.tasks.remove(self._find_task(task_id))

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task done; if it recurs, add and return its next occurrence (None if already done)."""
        task = self._find_task(task_id)
        if task.completed:
            return None  # already done: don't spawn a duplicate occurrence
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's tasks."""
        return list(self.tasks)

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict including this pet's tasks."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "special_needs": self.special_needs,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Pet:
        """Rebuild a Pet (and its tasks) from to_dict() output."""
        return cls(
            name=data["name"],
            species=data["species"],
            age=data.get("age"),
            special_needs=data.get("special_needs"),
            tasks=[Task.from_dict(t) for t in data.get("tasks", [])],
        )

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

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict of the whole owner, pets and tasks."""
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "preferences": self.preferences,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Owner:
        """Rebuild an Owner (with pets and tasks) from to_dict() output."""
        return cls(
            name=data["name"],
            available_minutes=data["available_minutes"],
            preferences=data.get("preferences", {}),
            pets=[Pet.from_dict(p) for p in data.get("pets", [])],
        )

    def save_to_json(self, path: Union[str, Path] = "data.json") -> None:
        """Write this owner, their pets and tasks to a JSON file (atomic replace)."""
        path = Path(path)
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        os.replace(tmp, path)  # never leaves a half-written data file behind

    @classmethod
    def load_from_json(cls, path: Union[str, Path] = "data.json") -> Owner:
        """Load an Owner from a JSON file; raises FileNotFoundError or ValueError."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)  # invalid JSON raises JSONDecodeError (a ValueError)
        try:
            return cls.from_dict(data)
        except (KeyError, TypeError, AttributeError) as err:
            raise ValueError(f"Malformed data file {str(path)!r}: {err!r}") from err


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
        today = date.today()
        pending = [
            (p, t)
            for p, t in self.owner.get_all_tasks()
            if not t.completed and t.due_date <= today
        ]
        ordered = self.sort_by_priority(pending)
        fitted, skipped = self._fit_to_time(ordered)

        plan = DailyPlan()
        for item in self._assign_times(fitted):
            plan.add_entry(item)
        for entry in skipped:
            plan.skipped.append(entry)
        return plan

    def sort_by_time(
        self, tasks: Optional[list[tuple[Pet, Task]]] = None
    ) -> list[tuple[Pet, Task]]:
        """Sort (pet, task) pairs by their "HH:MM" start_time; untimed tasks go last."""
        pairs = self.owner.get_all_tasks() if tasks is None else tasks
        return sorted(pairs, key=lambda pair: pair[1].start_time or "99:99")

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        tasks: Optional[list[tuple[Pet, Task]]] = None,
    ) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs matching the given pet name and/or completion status."""
        pairs = self.owner.get_all_tasks() if tasks is None else tasks
        return [
            (pet, task)
            for pet, task in pairs
            if (pet_name is None or pet.name == pet_name)
            and (completed is None or task.completed == completed)
        ]

    def detect_conflicts(self) -> list[str]:
        """Return warnings for pending tasks sharing the same date and start_time."""
        slots: dict[tuple[date, str], list[tuple[Pet, Task]]] = {}
        for pet, task in self.owner.get_all_tasks():
            if task.start_time is not None and not task.completed:
                slots.setdefault((task.due_date, task.start_time), []).append((pet, task))

        warnings = []
        for (day, at), group in slots.items():
            if len(group) > 1:
                scope = "same pet" if len({p.name for p, _ in group}) == 1 else "different pets"
                names = ", ".join(f"{p.name}: {t.title}" for p, t in group)
                warnings.append(f"Conflict on {day:%Y-%m-%d} at {at} ({scope}): {names}")
        return warnings

    def sort_by_priority(
        self, tasks: Optional[list[tuple[Pet, Task]]] = None
    ) -> list[tuple[Pet, Task]]:
        """Order by priority (high first), then fixed time, time of day, shorter first."""
        pairs = self.owner.get_all_tasks() if tasks is None else tasks

        def key(pair: tuple[Pet, Task]):
            """Sort key: priority desc, "HH:MM" time, time of day, duration asc."""
            _, task = pair
            tod = TIME_OF_DAY_ORDER.get(task.preferred_time or "", len(TIME_OF_DAY_ORDER))
            return (-task.priority_value(), task.start_time or "99:99", tod, task.duration_minutes)

        return sorted(pairs, key=key)

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
