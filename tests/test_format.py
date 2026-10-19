from datetime import date

from pawpal_format import (
    category_emoji,
    conflicts_text,
    plan_table,
    priority_badge,
    status_badge,
    task_label,
    tasks_table,
)
from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def test_priority_badges_are_colour_coded():
    assert priority_badge(Priority.HIGH).startswith("🔴")
    assert priority_badge(Priority.MEDIUM).startswith("🟡")
    assert priority_badge(Priority.LOW).startswith("🟢")


def test_category_emoji_known_unknown_and_case_insensitive():
    assert category_emoji("meds") == "💊"
    assert category_emoji("WALK") == "🐕"
    assert category_emoji("skydiving") == "🐾"


def test_status_badge_and_task_label():
    task = Task("Walk", 10, category="walk")
    assert status_badge(task) == "⏳ Pending"
    task.mark_complete()
    assert status_badge(task) == "✅ Done"
    assert task_label(task) == "🐕 Walk"


def test_tasks_table_has_headers_rows_and_emoji():
    pet = Pet("Mochi", "dog")
    task = Task("Morning walk", 30, Priority.HIGH, category="walk", start_time="07:30")

    table = tasks_table([(pet, task)])

    for expected in ["Time", "Priority", "Status", "07:30", "Mochi", "🐕 Morning walk", "🔴 High"]:
        assert expected in table


def test_tasks_table_handles_empty_list():
    assert tasks_table([]) == "No tasks to show."


def test_plan_table_shows_scheduled_and_skipped_tasks():
    owner = Owner("Jordan", 30)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, Priority.HIGH, category="walk"))
    pet.add_task(Task("Groom", 45, Priority.LOW, category="grooming"))

    text = plan_table(Scheduler(owner).generate_plan())

    assert date.today().isoformat() in text
    assert "🐕 Walk" in text and "08:00-08:30" in text
    assert "Skipped task" in text and "🛁 Groom" in text


def test_plan_table_empty_plan():
    text = plan_table(Scheduler(Owner("Jordan", 30)).generate_plan())
    assert "Nothing scheduled." in text and "0 min scheduled" in text


def test_conflicts_text_for_warnings_and_all_clear():
    assert conflicts_text([]) == "✅ No time conflicts."
    assert conflicts_text(["clash A", "clash B"]) == "🚨 clash A\n🚨 clash B"
