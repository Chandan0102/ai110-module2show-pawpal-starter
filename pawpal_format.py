"""Display helpers for PawPal+: emoji, colour-coded badges and tabulate tables."""

from __future__ import annotations

from tabulate import tabulate

from pawpal_system import DailyPlan, Pet, Priority, Task

PRIORITY_BADGES = {
    Priority.HIGH: "🔴 High",
    Priority.MEDIUM: "🟡 Medium",
    Priority.LOW: "🟢 Low",
}

CATEGORY_EMOJI = {
    "walk": "🐕",
    "feeding": "🥣",
    "meds": "💊",
    "enrichment": "🎾",
    "grooming": "🛁",
    "general": "🐾",
}

TABLE_STYLE = "rounded_outline"


def priority_badge(priority: Priority) -> str:
    """Return a colour-coded label: red high, yellow medium, green low."""
    return PRIORITY_BADGES[priority]


def category_emoji(category: str) -> str:
    """Return the emoji for a task category, or a paw print if unknown."""
    return CATEGORY_EMOJI.get(category.lower(), CATEGORY_EMOJI["general"])


def status_badge(task: Task) -> str:
    """Return a done/pending indicator for a task."""
    return "✅ Done" if task.completed else "⏳ Pending"


def task_label(task: Task) -> str:
    """Return the task title prefixed with its category emoji."""
    return f"{category_emoji(task.category)} {task.title}"


def tasks_table(pairs: list[tuple[Pet, Task]]) -> str:
    """Format (pet, task) pairs as a CLI table with badges and emoji."""
    if not pairs:
        return "No tasks to show."
    rows = [
        [
            task.start_time or "-",
            pet.name,
            task_label(task),
            priority_badge(task.priority),
            task.duration_minutes,
            task.frequency,
            task.due_date.isoformat(),
            status_badge(task),
        ]
        for pet, task in pairs
    ]
    headers = ["Time", "Pet", "Task", "Priority", "Min", "Repeats", "Due", "Status"]
    return tabulate(rows, headers=headers, tablefmt=TABLE_STYLE)


def plan_table(plan: DailyPlan) -> str:
    """Format a DailyPlan's scheduled entries and skipped tasks as CLI tables."""
    if plan.entries:
        scheduled = tabulate(
            [
                [
                    f"{i.start:%H:%M}-{i.end:%H:%M}",
                    i.pet.name,
                    task_label(i.task),
                    priority_badge(i.task.priority),
                    i.task.duration_minutes,
                ]
                for i in plan.entries
            ],
            headers=["Time", "Pet", "Task", "Priority", "Min"],
            tablefmt=TABLE_STYLE,
        )
    else:
        scheduled = "Nothing scheduled."

    parts = [
        f"📅 Plan for {plan.plan_date:%Y-%m-%d}",
        scheduled,
        f"⏱  {plan.total_minutes} min scheduled, {len(plan.skipped)} skipped",
    ]
    if plan.skipped:
        parts.append(
            tabulate(
                [
                    [s.pet.name, task_label(s.task), priority_badge(s.task.priority), s.reason]
                    for s in plan.skipped
                ],
                headers=["Pet", "Skipped task", "Priority", "Why"],
                tablefmt=TABLE_STYLE,
            )
        )
    return "\n".join(parts)


def conflicts_text(warnings: list[str]) -> str:
    """Format conflict warnings, or a green all-clear when there are none."""
    if not warnings:
        return "✅ No time conflicts."
    return "\n".join(f"🚨 {w}" for w in warnings)
