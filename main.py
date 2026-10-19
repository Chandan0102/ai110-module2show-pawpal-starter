"""Temporary terminal demo for the PawPal+ logic layer."""

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def show(title: str, pairs) -> None:
    print(f"\n--- {title} ---")
    for pet, task in pairs:
        print(f"  {task.start_time or '--:--'}  {pet.name:<6} {task.title} "
              f"[{'done' if task.completed else 'pending'}, due {task.due_date}]")


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)
    mochi = Pet(name="Mochi", species="dog", age=4)
    luna = Pet(name="Luna", species="cat", age=2)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks are deliberately added out of time order.
    mochi.add_task(Task("Evening walk", 30, Priority.MEDIUM, start_time="18:00"))
    mochi.add_task(Task("Morning walk", 30, Priority.HIGH, start_time="07:30"))
    mochi.add_task(Task("Grooming", 45, Priority.LOW, frequency="weekly"))
    luna.add_task(Task("Breakfast", 10, Priority.HIGH, start_time="8:00"))
    luna.add_task(Task("Medication", 5, Priority.HIGH, start_time="18:00"))  # clashes with Evening walk
    luna.add_task(Task("Laser play", 15, Priority.MEDIUM, start_time="12:15", frequency="once"))

    scheduler = Scheduler(owner)

    show("All tasks, as added", owner.get_all_tasks())
    show("Sorted by time", scheduler.sort_by_time())
    show("Only Luna's tasks", scheduler.filter_tasks(pet_name="Luna"))

    # Completing a recurring task creates the next occurrence automatically.
    breakfast = next(t for t in luna.tasks if t.title == "Breakfast")
    nxt = luna.complete_task(breakfast.task_id)
    print(f"\nCompleted '{breakfast.title}' -> next occurrence due {nxt.due_date}")
    laser = next(t for t in luna.tasks if t.title == "Laser play")
    print(f"Completed one-off '{laser.title}' -> next: {luna.complete_task(laser.task_id)}")

    show("Pending tasks", scheduler.filter_tasks(completed=False))
    show("Completed tasks", scheduler.filter_tasks(completed=True))

    print("\n--- Conflict check ---")
    warnings = scheduler.detect_conflicts()
    print("\n".join(f"  WARNING: {w}" for w in warnings) or "  No conflicts.")

    plan = Scheduler(owner).generate_plan()
    print(f"\n=== Today's Schedule for {owner.name} "
          f"({owner.available_minutes} min available) ===")
    print(plan.summary())
    print("\n--- Why this plan ---")
    print(plan.explain())


if __name__ == "__main__":
    main()
