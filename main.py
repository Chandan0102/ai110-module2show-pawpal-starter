"""Temporary terminal demo for the PawPal+ logic layer."""

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=4)
    luna = Pet(name="Luna", species="cat", age=2)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(
        Task("Morning walk", 30, Priority.HIGH, category="walk", preferred_time="morning")
    )
    mochi.add_task(
        Task("Training session", 20, Priority.MEDIUM, category="enrichment",
             preferred_time="afternoon")
    )
    mochi.add_task(
        Task("Grooming", 45, Priority.LOW, category="grooming", preferred_time="evening",
             frequency="weekly")
    )
    luna.add_task(
        Task("Breakfast", 10, Priority.HIGH, category="feeding", preferred_time="morning")
    )
    luna.add_task(
        Task("Evening medication", 5, Priority.HIGH, category="meds",
             preferred_time="evening")
    )
    luna.add_task(
        Task("Laser play", 15, Priority.MEDIUM, category="enrichment",
             preferred_time="afternoon")
    )

    plan = Scheduler(owner).generate_plan()

    print(f"=== Today's Schedule for {owner.name} "
          f"({owner.available_minutes} min available) ===")
    print(plan.summary())
    print("\n--- Why this plan ---")
    print(plan.explain())


if __name__ == "__main__":
    main()
