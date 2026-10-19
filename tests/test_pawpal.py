from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", 30)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Breakfast", 10))

    assert len(pet.get_tasks()) == 1


def _owner_with_two_pets():
    owner = Owner("Jordan", 90)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna


def test_sort_by_time_orders_hhmm_and_puts_untimed_last():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Evening", 10, start_time="18:00"))
    mochi.add_task(Task("Untimed", 10))
    luna.add_task(Task("Early", 10, start_time="8:00"))  # normalised to 08:00

    ordered = [t.title for _, t in Scheduler(owner).sort_by_time()]

    assert ordered == ["Early", "Evening", "Untimed"]


def test_filter_by_pet_and_completion_status():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 10, frequency="once"))
    luna.add_task(Task("Feed", 10, frequency="once"))
    mochi.tasks[0].mark_complete()
    scheduler = Scheduler(owner)

    assert [t.title for _, t in scheduler.filter_tasks(pet_name="Luna")] == ["Feed"]
    assert [t.title for _, t in scheduler.filter_tasks(completed=True)] == ["Walk"]
    assert [t.title for _, t in scheduler.filter_tasks(completed=False)] == ["Feed"]


def test_completing_daily_task_creates_next_day_occurrence():
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30, frequency="daily")
    pet.add_task(task)

    new_task = pet.complete_task(task.task_id)

    assert task.completed is True
    assert new_task.completed is False
    assert new_task.due_date == date.today() + timedelta(days=1)
    assert new_task.task_id != task.task_id
    assert len(pet.get_tasks()) == 2


def test_completing_weekly_task_is_due_in_seven_days_and_once_task_does_not_recur():
    pet = Pet("Mochi", "dog")
    weekly = Task("Groom", 30, frequency="weekly")
    once = Task("Vet", 30, frequency="once")
    pet.add_task(weekly)
    pet.add_task(once)

    assert pet.complete_task(weekly.task_id).due_date == date.today() + timedelta(days=7)
    assert pet.complete_task(once.task_id) is None


def test_detect_conflicts_warns_on_same_start_time_across_pets():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30, start_time="18:00"))
    luna.add_task(Task("Meds", 5, start_time="18:00"))
    luna.add_task(Task("Feed", 10, start_time="09:00"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "18:00" in warnings[0] and "different pets" in warnings[0]


def test_detect_conflicts_returns_empty_list_when_no_clash():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30, start_time="07:00"))

    assert Scheduler(owner).detect_conflicts() == []


def test_invalid_start_time_raises_value_error():
    with pytest.raises(ValueError):
        Task("Walk", 30, start_time="25:99")


def test_plan_skips_tasks_not_yet_due():
    owner, mochi, _ = _owner_with_two_pets()
    walk = Task("Walk", 30)
    mochi.add_task(walk)
    mochi.complete_task(walk.task_id)  # creates a copy due tomorrow

    plan = Scheduler(owner).generate_plan()

    assert plan.entries == []
