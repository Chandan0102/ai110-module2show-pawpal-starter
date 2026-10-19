"""Temporary terminal demo for the PawPal+ logic layer."""

import sys

from pawpal_format import conflicts_text, plan_table, tasks_table
from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def heading(text: str) -> None:
    print(f"\n{text}")


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)
    mochi = Pet(name="Mochi", species="dog", age=4)
    luna = Pet(name="Luna", species="cat", age=2)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks are deliberately added out of time order.
    mochi.add_task(Task("Evening walk", 30, Priority.MEDIUM, category="walk", start_time="18:00"))
    mochi.add_task(Task("Morning walk", 30, Priority.HIGH, category="walk", start_time="07:30"))
    mochi.add_task(Task("Grooming", 45, Priority.LOW, category="grooming", frequency="weekly"))
    luna.add_task(Task("Breakfast", 10, Priority.HIGH, category="feeding", start_time="8:00"))
    luna.add_task(Task("Medication", 5, Priority.HIGH, category="meds", start_time="18:00"))  # clashes
    luna.add_task(Task("Laser play", 15, Priority.MEDIUM, category="enrichment",
                       start_time="12:15", frequency="once"))

    scheduler = Scheduler(owner)

    heading("All tasks, as added")
    print(tasks_table(owner.get_all_tasks()))
    heading("Sorted by time")
    print(tasks_table(scheduler.sort_by_time()))
    heading("Only Luna's tasks")
    print(tasks_table(scheduler.filter_tasks(pet_name="Luna")))

    # Completing a recurring task creates the next occurrence automatically.
    breakfast = next(t for t in luna.tasks if t.title == "Breakfast")
    nxt = luna.complete_task(breakfast.task_id)
    heading(f"✅ Completed '{breakfast.title}' -> next occurrence due {nxt.due_date}")
    laser = next(t for t in luna.tasks if t.title == "Laser play")
    print(f"✅ Completed one-off '{laser.title}' -> next: {luna.complete_task(laser.task_id)}")

    heading("Pending tasks")
    print(tasks_table(scheduler.filter_tasks(completed=False)))
    heading("Completed tasks")
    print(tasks_table(scheduler.filter_tasks(completed=True)))

    heading("Conflict check")
    print(conflicts_text(scheduler.detect_conflicts()))

    heading(f"=== Today's Schedule for {owner.name} ({owner.available_minutes} min available) ===")
    plan = scheduler.generate_plan()
    print(plan_table(plan))
    heading("--- Why this plan ---")
    print(plan.explain())


def priority_demo() -> None:
    """Show priority-first ordering (then time) on a day that is too full."""
    owner = Owner(name="Jordan", available_minutes=60)
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Grooming", 30, Priority.LOW, category="grooming", start_time="09:00"))
    mochi.add_task(Task("Morning walk", 30, Priority.HIGH, category="walk", start_time="07:30"))
    mochi.add_task(Task("Dinner", 10, Priority.HIGH, category="feeding", start_time="18:00"))
    luna.add_task(Task("Medication", 5, Priority.HIGH, category="meds", start_time="07:00"))
    luna.add_task(Task("Training", 20, Priority.MEDIUM, category="enrichment", start_time="08:00"))
    luna.add_task(Task("Laser play", 15, Priority.MEDIUM, category="enrichment", start_time="06:30"))

    scheduler = Scheduler(owner)

    print("\n\n=== Priority scheduling demo (60 min available) ===")
    heading("--- By time only ---")
    print(tasks_table(scheduler.sort_by_time()))
    heading("--- Priority first, then time ---")
    print(tasks_table(scheduler.sort_by_priority()))

    plan = scheduler.generate_plan()
    print()
    print(plan_table(plan))
    heading("--- Why this plan ---")
    print(plan.explain())


def slot_demo() -> None:
    """Show find_next_slot() looking for free gaps around fixed-time tasks."""
    owner = Owner(name="Jordan", available_minutes=240)
    mochi = Pet(name="Mochi", species="dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Morning walk", 30, Priority.HIGH, category="walk", start_time="08:00"))
    mochi.add_task(Task("Vet visit", 60, Priority.HIGH, category="general", start_time="09:00"))
    mochi.add_task(Task("Grooming", 45, Priority.LOW, category="grooming", start_time="11:00"))

    scheduler = Scheduler(owner)

    print("\n\n=== Next available slot demo (day runs 08:00-22:00) ===")
    print(tasks_table(scheduler.sort_by_time()))
    for minutes in (30, 45, 90, 600, 720):
        slot = scheduler.find_next_slot(minutes)
        answer = f"{slot:%H:%M}" if slot else "no room today"
        print(f"🕒 Next free {minutes:>3}-minute slot: {answer}")


if __name__ == "__main__":
    # Emoji need UTF-8; the default Windows console encoding can't print them.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
    priority_demo()
    slot_demo()
