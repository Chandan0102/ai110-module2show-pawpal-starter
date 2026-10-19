from datetime import date, time, timedelta

import pytest

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


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


# --- Edge cases: plan generation ------------------------------------------------


def test_empty_owner_and_pet_without_tasks_give_empty_plan():
    owner = Owner("Jordan", 60)
    assert Scheduler(owner).generate_plan().entries == []

    owner.add_pet(Pet("Mochi", "dog"))
    plan = Scheduler(owner).generate_plan()
    assert plan.entries == [] and plan.skipped == []


def test_zero_minute_budget_skips_everything_with_a_reason():
    owner, mochi, _ = _owner_with_two_pets()
    owner.available_minutes = 0
    mochi.add_task(Task("Walk", 10))

    plan = Scheduler(owner).generate_plan()

    assert plan.entries == []
    assert len(plan.skipped) == 1 and "budget" in plan.skipped[0].reason


def test_task_exactly_equal_to_remaining_time_fits_and_longer_one_is_skipped():
    owner, mochi, _ = _owner_with_two_pets()
    owner.available_minutes = 30
    mochi.add_task(Task("Exact", 30, Priority.HIGH))
    mochi.add_task(Task("Too long", 31, Priority.LOW))

    plan = Scheduler(owner).generate_plan()

    assert [i.task.title for i in plan.entries] == ["Exact"]
    assert [s.task.title for s in plan.skipped] == ["Too long"]
    assert plan.total_minutes == 30


def test_plan_orders_by_priority_and_runs_back_to_back_from_start_time():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Low", 10, Priority.LOW))
    luna.add_task(Task("High", 20, Priority.HIGH))

    entries = Scheduler(owner, start_time=time(9, 0)).generate_plan().entries

    assert [i.task.title for i in entries] == ["High", "Low"]
    assert (entries[0].start, entries[0].end) == (time(9, 0), time(9, 20))
    assert entries[1].start == time(9, 20)


def test_equal_priority_tasks_keep_a_stable_order():
    owner, mochi, _ = _owner_with_two_pets()
    for name in ["A", "B", "C"]:
        mochi.add_task(Task(name, 10, Priority.MEDIUM))

    entries = Scheduler(owner).generate_plan().entries

    assert [i.task.title for i in entries] == ["A", "B", "C"]


def test_completed_tasks_are_excluded_and_overdue_tasks_are_included():
    owner, mochi, _ = _owner_with_two_pets()
    done = Task("Done", 10)
    done.mark_complete()
    mochi.add_task(done)
    mochi.add_task(Task("Overdue", 10, due_date=date.today() - timedelta(days=2)))

    entries = Scheduler(owner).generate_plan().entries

    assert [i.task.title for i in entries] == ["Overdue"]


# --- Edge cases: sorting, filtering, conflicts -----------------------------------


def test_sort_by_time_keeps_original_order_for_equal_times_and_handles_empty():
    owner, mochi, luna = _owner_with_two_pets()
    assert Scheduler(owner).sort_by_time() == []

    mochi.add_task(Task("First", 10, start_time="10:00"))
    luna.add_task(Task("Second", 10, start_time="10:00"))

    assert [t.title for _, t in Scheduler(owner).sort_by_time()] == ["First", "Second"]


def test_filter_unknown_pet_returns_empty_and_filters_can_combine():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 10))
    mochi.add_task(Task("Groom", 10))
    mochi.tasks[0].mark_complete()
    scheduler = Scheduler(owner)

    assert scheduler.filter_tasks(pet_name="Ghost") == []
    both = scheduler.filter_tasks(pet_name="Mochi", completed=False)
    assert [t.title for _, t in both] == ["Groom"]


def test_three_tasks_at_same_time_give_one_warning_naming_all_three():
    owner, mochi, luna = _owner_with_two_pets()
    mochi.add_task(Task("A", 10, start_time="09:00"))
    mochi.add_task(Task("B", 10, start_time="09:00"))
    luna.add_task(Task("C", 10, start_time="09:00"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert all(name in warnings[0] for name in ["A", "B", "C"])


def test_same_pet_conflict_is_labelled_same_pet():
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("A", 10, start_time="09:00"))
    mochi.add_task(Task("B", 10, start_time="09:00"))

    assert "same pet" in Scheduler(owner).detect_conflicts()[0]


def test_conflicts_ignore_completed_tasks_other_dates_and_untimed_tasks():
    owner, mochi, luna = _owner_with_two_pets()
    done = Task("Done", 10, start_time="09:00")
    done.mark_complete()
    mochi.add_task(done)
    mochi.add_task(Task("Today", 10, start_time="09:00"))
    tomorrow = date.today() + timedelta(days=1)
    luna.add_task(Task("Tomorrow", 10, start_time="09:00", due_date=tomorrow))
    luna.add_task(Task("Untimed 1", 10))
    luna.add_task(Task("Untimed 2", 10))

    assert Scheduler(owner).detect_conflicts() == []


def test_overlapping_but_not_identical_start_times_are_not_flagged():
    # Documents the tradeoff in reflection.md: only exact matches are detected.
    owner, mochi, _ = _owner_with_two_pets()
    mochi.add_task(Task("Walk", 30, start_time="18:00"))
    mochi.add_task(Task("Meds", 5, start_time="18:15"))

    assert Scheduler(owner).detect_conflicts() == []


# --- Edge cases: recurrence and validation ---------------------------------------


def test_completing_the_same_task_twice_does_not_create_two_copies():
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30)
    pet.add_task(task)

    pet.complete_task(task.task_id)
    assert pet.complete_task(task.task_id) is None

    assert len(pet.get_tasks()) == 2


def test_next_occurrence_keeps_task_details():
    task = Task("Meds", 5, Priority.HIGH, category="meds", start_time="08:00")

    nxt = task.next_occurrence()

    assert (nxt.title, nxt.priority, nxt.category, nxt.start_time) == (
        "Meds", Priority.HIGH, "meds", "08:00",
    )


@pytest.mark.parametrize("text, expected", [("HIGH", Priority.HIGH), (" low ", Priority.LOW)])
def test_priority_from_str_ignores_case_and_whitespace(text, expected):
    assert Priority.from_str(text) is expected


def test_priority_from_str_rejects_unknown_value():
    with pytest.raises(ValueError):
        Priority.from_str("urgent")


@pytest.mark.parametrize(
    "bad", [{"duration_minutes": 0}, {"duration_minutes": -5}, {"frequency": "hourly"}]
)
def test_task_rejects_invalid_values(bad):
    base = {"title": "Walk", "duration_minutes": 10}
    with pytest.raises(ValueError):
        Task(**{**base, **bad})


def test_edit_task_updates_fields_and_keeps_id():
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30)
    original_id = task.task_id
    pet.add_task(task)

    pet.edit_task(task.task_id, duration_minutes=45, title="Long walk")

    assert (task.duration_minutes, task.title) == (45, "Long walk")
    assert task.task_id == original_id


def test_failed_edit_leaves_task_unchanged():
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30)
    pet.add_task(task)

    with pytest.raises(ValueError):
        pet.edit_task(task.task_id, duration_minutes=0)

    assert task.duration_minutes == 30


def test_unknown_task_id_or_field_raises():
    pet = Pet("Mochi", "dog")
    task = Task("Walk", 30)
    pet.add_task(task)

    with pytest.raises(KeyError):
        pet.remove_task("missing")
    with pytest.raises(KeyError):
        pet.edit_task("missing", title="x")
    with pytest.raises(AttributeError):
        pet.edit_task(task.task_id, colour="red")


def test_remove_task_and_remove_pet():
    owner, mochi, _ = _owner_with_two_pets()
    task = Task("Walk", 30)
    mochi.add_task(task)

    mochi.remove_task(task.task_id)
    owner.remove_pet("Luna")

    assert mochi.get_tasks() == []
    assert [p.name for p in owner.pets] == ["Mochi"]
    with pytest.raises(KeyError):
        owner.remove_pet("Ghost")
