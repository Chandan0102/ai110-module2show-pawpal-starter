# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan daily care for one or more pets. You add pets and care tasks (walks, feeding, meds, enrichment, grooming), tell the app how much time you have, and it builds a prioritised daily plan and explains its choices.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

## Features

- **Multiple pets, one plan.** An owner can have any number of pets, and the scheduler builds a single plan across all of them.
- **Priority-first daily plan.** Every task has a priority (low, medium or high). The plan is ordered by priority first (high before medium before low), then by fixed `HH:MM` time, then by time of day (morning, afternoon, evening), then shorter tasks first, and is placed back to back from 08:00. See [Priority-based scheduling](#-priority-based-scheduling).
- **Time budget.** The plan only includes tasks that fit in the owner's available minutes. Tasks that don't fit are listed as skipped, each with the reason.
- **Plan explanation.** Every included and skipped task comes with a plain-language reason.
- **Sorting by time.** The task list can be shown in chronological order using each task's fixed `HH:MM` time. Tasks with no fixed time go last.
- **Filtering.** Show tasks for one pet or all pets, and only pending, only completed, or all tasks.
- **Conflict warnings.** If two pending tasks share the same date and fixed time (same pet or different pets), the app shows a warning instead of failing, and lets you change one task's time.
- **Recurring tasks.** Completing a daily or weekly task automatically creates the next occurrence (due tomorrow, or in 7 days). One-off tasks do not repeat.
- **Input validation.** Bad durations, frequencies, priorities and times are rejected with a clear message.
- **Saved between runs.** Pets and tasks are stored in `data.json` and reloaded when the app starts (see [Data persistence](#-data-persistence)).
- **Easy to read output.** Colour-coded priority badges, emoji for task types, status indicators and formatted CLI tables (see [Display and formatting](#-display-and-formatting)).
- **Next available slot.** Ask for the earliest free gap of a given length around tasks that have fixed times (`Scheduler.find_next_slot()`), including the Streamlit "Find a free time slot" panel.
- **Tested.** 65 automated tests cover scheduling, sorting, filtering, recurrence, conflicts, validation, saving/loading and formatting.

## Implementation summary

The backend lives in `pawpal_system.py` and is built from a few small classes:

- **Task** (dataclass): one care activity with a title, duration, priority, category, preferred time of day, frequency, optional fixed time, due date and completion status. Each task has a unique `task_id`.
- **Pet** (dataclass): pet details plus its own list of tasks, with methods to add, edit, remove, complete and list them.
- **Owner** (dataclass): the owner's name and daily time budget, plus a list of pets. `get_all_tasks()` returns every pet's tasks together as `(pet, task)` pairs.
- **Scheduler**: the "brain". It reads tasks through `Owner.get_all_tasks()` (so every pet is covered), skips completed and not-yet-due tasks, sorts by priority, time of day and duration, keeps adding tasks until the owner's time budget runs out, and lays them out back to back from the start time. It also provides sorting, filtering and conflict detection.
- **DailyPlan**, **ScheduledItem** and **SkippedTask**: the result. A plan holds the scheduled items (task, pet, start, end, reason) and the skipped tasks with the reason each did not fit. `summary()` and `explain()` turn it into readable text.

How they fit together: `Owner` → `Pet` → `Task` hold the data, `Scheduler` reads from the `Owner` and produces a `DailyPlan`, and the UI only has to display that plan. The class diagram is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) (Mermaid source).

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
# Streamlit app
streamlit run app.py

# Terminal demo of the scheduling logic
python main.py
```

## 🖥️ Sample Output

The schedule section of `python main.py` (full output is in the demo walkthrough below):

```
=== Today's Schedule for Jordan (90 min available) ===
📅 Plan for 2026-10-18
╭─────────────┬───────┬─────────────────┬────────────┬───────╮
│ Time        │ Pet   │ Task            │ Priority   │   Min │
├─────────────┼───────┼─────────────────┼────────────┼───────┤
│ 08:00-08:30 │ Mochi │ 🐕 Morning walk │ 🔴 High    │    30 │
│ 08:30-08:35 │ Luna  │ 💊 Medication   │ 🔴 High    │     5 │
│ 08:35-09:05 │ Mochi │ 🐕 Evening walk │ 🟡 Medium  │    30 │
╰─────────────┴───────┴─────────────────┴────────────┴───────╯
⏱  65 min scheduled, 1 skipped
╭───────┬────────────────┬────────────┬────────────────────────────────────────────────────────────╮
│ Pet   │ Skipped task   │ Priority   │ Why                                                        │
├───────┼────────────────┼────────────┼────────────────────────────────────────────────────────────┤
│ Mochi │ 🛁 Grooming    │ 🟢 Low     │ needs 45 min but only 25 min of the 90 min budget remained │
╰───────┴────────────────┴────────────┴────────────────────────────────────────────────────────────╯

--- Why this plan ---
Included Mochi - Morning walk: high priority, fits within the available time
Included Luna - Medication: high priority, fits within the available time
Included Mochi - Evening walk: medium priority, fits within the available time
Skipped Mochi - Grooming: needs 45 min but only 25 min of the 90 min budget remained
```

## 🎯 Priority-based scheduling

Every `Task` has a `priority` of `Priority.LOW`, `Priority.MEDIUM` or `Priority.HIGH`. The scheduler sorts by priority first and by time second:

1. **Priority** (high, then medium, then low)
2. **Fixed time** (`HH:MM`, earliest first; tasks with no time last)
3. **Time of day** (morning, afternoon, evening)
4. **Duration** (shorter first)

The sort is `Scheduler.sort_by_priority()`, and `generate_plan()` uses it before fitting tasks into the owner's time budget. When time is short, the lowest-priority tasks are the ones dropped, even if they are earlier in the day.

The demo below (`python main.py`, second half) uses a 60-minute day with six tasks. Sorted by time alone, a low-priority grooming session at 09:00 would come before the 18:00 dinner. Sorted by priority first, the three high-priority tasks lead, and the plan drops the lowest priorities when time runs out:

```
=== Priority scheduling demo (60 min available) ===

--- By time only ---
╭────────┬───────┬─────────────────┬────────────┬───────┬───────────┬────────────┬────────────╮
│ Time   │ Pet   │ Task            │ Priority   │   Min │ Repeats   │ Due        │ Status     │
├────────┼───────┼─────────────────┼────────────┼───────┼───────────┼────────────┼────────────┤
│ 06:30  │ Luna  │ 🎾 Laser play   │ 🟡 Medium  │    15 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 07:00  │ Luna  │ 💊 Medication   │ 🔴 High    │     5 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 07:30  │ Mochi │ 🐕 Morning walk │ 🔴 High    │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 08:00  │ Luna  │ 🎾 Training     │ 🟡 Medium  │    20 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 09:00  │ Mochi │ 🛁 Grooming     │ 🟢 Low     │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 18:00  │ Mochi │ 🥣 Dinner       │ 🔴 High    │    10 │ daily     │ 2026-10-18 │ ⏳ Pending │
╰────────┴───────┴─────────────────┴────────────┴───────┴───────────┴────────────┴────────────╯

--- Priority first, then time ---
╭────────┬───────┬─────────────────┬────────────┬───────┬───────────┬────────────┬────────────╮
│ Time   │ Pet   │ Task            │ Priority   │   Min │ Repeats   │ Due        │ Status     │
├────────┼───────┼─────────────────┼────────────┼───────┼───────────┼────────────┼────────────┤
│ 07:00  │ Luna  │ 💊 Medication   │ 🔴 High    │     5 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 07:30  │ Mochi │ 🐕 Morning walk │ 🔴 High    │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 18:00  │ Mochi │ 🥣 Dinner       │ 🔴 High    │    10 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 06:30  │ Luna  │ 🎾 Laser play   │ 🟡 Medium  │    15 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 08:00  │ Luna  │ 🎾 Training     │ 🟡 Medium  │    20 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 09:00  │ Mochi │ 🛁 Grooming     │ 🟢 Low     │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
╰────────┴───────┴─────────────────┴────────────┴───────┴───────────┴────────────┴────────────╯

📅 Plan for 2026-10-18
╭─────────────┬───────┬─────────────────┬────────────┬───────╮
│ Time        │ Pet   │ Task            │ Priority   │   Min │
├─────────────┼───────┼─────────────────┼────────────┼───────┤
│ 08:00-08:05 │ Luna  │ 💊 Medication   │ 🔴 High    │     5 │
│ 08:05-08:35 │ Mochi │ 🐕 Morning walk │ 🔴 High    │    30 │
│ 08:35-08:45 │ Mochi │ 🥣 Dinner       │ 🔴 High    │    10 │
│ 08:45-09:00 │ Luna  │ 🎾 Laser play   │ 🟡 Medium  │    15 │
╰─────────────┴───────┴─────────────────┴────────────┴───────╯
⏱  60 min scheduled, 2 skipped
╭───────┬────────────────┬────────────┬───────────────────────────────────────────────────────────╮
│ Pet   │ Skipped task   │ Priority   │ Why                                                       │
├───────┼────────────────┼────────────┼───────────────────────────────────────────────────────────┤
│ Luna  │ 🎾 Training    │ 🟡 Medium  │ needs 20 min but only 0 min of the 60 min budget remained │
│ Mochi │ 🛁 Grooming    │ 🟢 Low     │ needs 30 min but only 0 min of the 60 min budget remained │
╰───────┴────────────────┴────────────┴───────────────────────────────────────────────────────────╯

--- Why this plan ---
Included Luna - Medication: high priority, fits within the available time
Included Mochi - Morning walk: high priority, fits within the available time
Included Mochi - Dinner: high priority, fits within the available time
Included Luna - Laser play: medium priority, fits within the available time
Skipped Luna - Training: needs 20 min but only 0 min of the 60 min budget remained
Skipped Mochi - Grooming: needs 30 min but only 0 min of the 60 min budget remained
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage (requires pytest-cov):
python -m pytest --cov
```

Sample test output:

```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\sinha\Desktop\AI110\ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
collected 65 items

tests\test_format.py ........                                           [ 14%]
tests\test_pawpal.py ................................................... [ 90%]
......                                                                   [100%]

============================= 65 passed in 0.30s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | `sort_by_time` orders tasks by their `"HH:MM"` `start_time`; tasks with no time go last. `sort_by_priority` orders by priority first, then `start_time`, then time of day, then duration, and is what the daily plan uses. |
| Filtering | `Scheduler.filter_tasks()` | Filter by `pet_name`, by `completed` status, or both. |
| Conflict handling | `Scheduler.detect_conflicts()` | Warns when pending tasks share the same date and `start_time`, for the same pet or different pets. |
| Recurring tasks | `Task.next_occurrence()`, `Pet.complete_task()` | Completing a daily or weekly task adds a copy due today + 1 or + 7 days. |
| Next available slot | `Scheduler.find_next_slot()` | Finds the earliest start time with a free gap of the requested length, around pending fixed-time tasks. |

**Sorting.** `sort_by_time()` uses `sorted()` with a lambda key on `start_time`. `Task` normalises times to zero-padded `HH:MM` (so `"8:00"` becomes `"08:00"`), which makes plain string comparison match clock order. Tasks without a time sort last using a `"99:99"` sentinel.

**Filtering.** `filter_tasks(pet_name=..., completed=...)` works on the `(pet, task)` pairs from `Owner.get_all_tasks()`. Leave an argument as `None` to ignore that filter.

**Conflict detection.** `detect_conflicts()` groups pending tasks by `(due_date, start_time)` in one pass and returns a list of warning strings. It never raises. It only catches exact start-time matches, not overlapping durations (see the tradeoff in `reflection.md`).

**Recurring tasks.** Call `pet.complete_task(task_id)` instead of `task.mark_complete()` when you want recurrence. It marks the task done and, for `daily` or `weekly` tasks, adds a new `Task` with a fresh id and a due date computed with `timedelta`. One-off (`once`) tasks return `None`, and completing an already-completed task does nothing. The daily plan only includes tasks that are due today or earlier, so the new copy waits until its day.

**Next available slot.** `find_next_slot(duration_minutes, day_start=08:00, day_end=22:00, on=today)` answers "when could I fit a 45-minute vet visit?". Pending tasks that have a fixed `HH:MM` time block their time range (start to start + duration). Tasks without a fixed time are flexible and block nothing. The method sorts those blocked ranges by start time and sweeps through the day once with a cursor: if the gap before the next range is big enough it returns the cursor, otherwise it moves the cursor past that range. It returns `None` if nothing fits before `day_end`. It works in whole minutes, so overlapping and unsorted tasks are handled and nothing wraps past midnight. Unlike `detect_conflicts()`, which only matches identical start times, this method does take durations into account. Output from `python main.py` (the third demo), with fixed tasks at 08:00 for 30 min, 09:00 for 60 min and 11:00 for 45 min:

```
=== Next available slot demo (day runs 08:00-22:00) ===
╭────────┬───────┬─────────────────┬────────────┬───────┬───────────┬────────────┬────────────╮
│ Time   │ Pet   │ Task            │ Priority   │   Min │ Repeats   │ Due        │ Status     │
├────────┼───────┼─────────────────┼────────────┼───────┼───────────┼────────────┼────────────┤
│ 08:00  │ Mochi │ 🐕 Morning walk │ 🔴 High    │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 09:00  │ Mochi │ 🐾 Vet visit    │ 🔴 High    │    60 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 11:00  │ Mochi │ 🛁 Grooming     │ 🟢 Low     │    45 │ daily     │ 2026-10-18 │ ⏳ Pending │
╰────────┴───────┴─────────────────┴────────────┴───────┴───────────┴────────────┴────────────╯
🕒 Next free  30-minute slot: 08:30
🕒 Next free  45-minute slot: 10:00
🕒 Next free  90-minute slot: 11:45
🕒 Next free 600-minute slot: 11:45
🕒 Next free 720-minute slot: no room today
```

In the Streamlit app, open **Find a free time slot** in the Tasks section, enter the minutes needed and press **Find slot**.

**Known limitation.** The daily plan packs tasks back to back from the start time and does not yet place tasks at their fixed `start_time`. Fixed times are used for sorting and conflict warnings only.

## 🎨 Display and formatting

PawPal+ uses the same visual language in the terminal and in the Streamlit app, defined once in `pawpal_format.py`.

| Feature | Where | How it is built |
|---------|-------|-----------------|
| **Colour-coded priority badges** 🔴 High, 🟡 Medium, 🟢 Low | CLI tables and Streamlit tables | `priority_badge()` maps each `Priority` to a coloured emoji and label |
| **Emoji for task types** 🐕 walk, 🥣 feeding, 💊 meds, 🎾 enrichment, 🛁 grooming, 🐾 other | CLI tables, Streamlit tables, and the "Type" dropdown when adding a task | `category_emoji()` and `task_label()` (unknown types fall back to 🐾) |
| **Status indicators** ✅ Done, ⏳ Pending | Task tables | `status_badge()` |
| **Structured CLI tables** with rounded borders | `python main.py` | `tasks_table()` and `plan_table()`, built with the [`tabulate`](https://pypi.org/project/tabulate/) library (`rounded_outline` style) |
| **Skipped-task table** with the reason each task did not fit | `python main.py` | `plan_table()` |
| **Conflict alerts** 🚨, or ✅ when there are none | `python main.py`; the app shows `st.warning` boxes | `conflicts_text()` |

**Libraries.** [`tabulate`](https://pypi.org/project/tabulate/) draws the tables, and [`wcwidth`](https://pypi.org/project/wcwidth/) lets it measure emoji widths so columns stay aligned. Both are listed in `requirements.txt` (`pip install -r requirements.txt`). The Streamlit app uses `st.table`, `st.metric`, `st.success`, `st.warning` and `st.error`, with the same badge functions.

**Windows note.** The default Windows console encoding can't print emoji, so `main.py` switches its output to UTF-8 with `sys.stdout.reconfigure(encoding="utf-8")`. If you run `python main.py` and the characters look wrong, use Windows Terminal or set `PYTHONUTF8=1`.

**Files for this feature:** `pawpal_format.py` (new), `main.py`, `app.py`, `requirements.txt`, `tests/test_format.py` (new, 8 tests) and this README.

## 💾 Data persistence

PawPal+ remembers your pets and tasks between runs by saving them to `data.json` in the project folder.

**Workflow**

1. **Start-up.** When `app.py` starts a new session it calls `Owner.load_from_json("data.json")`.
   - If the file doesn't exist yet (first run), it starts with an empty default owner.
   - If the file is corrupt or malformed, it is renamed to `data.json.corrupt` (so nothing is lost), the app starts fresh, and a warning explains what happened.
2. **While you use the app.** Changes (owner name and minutes, new pets, new tasks, completing a task, changing a task's time) live in the in-memory `Owner` held in `st.session_state`.
3. **Saving.** At the end of every run of the script, and just before the app refreshes itself after completing a task or changing a time, `app.py` calls `owner.save_to_json("data.json")`.
4. **Next start.** The saved data is loaded again, including each task's id, due date, completion status and recurrence, so a recurring task completed yesterday still has its next occurrence waiting.

**How objects become JSON.** Instead of a serialisation library such as marshmallow, the project uses small custom conversion methods, which keeps it dependency-free and easy to read:

| Method | What it does |
|--------|--------------|
| `Task.to_dict()` / `Task.from_dict()` | The priority enum is stored by name (`"HIGH"`) and the due date as an ISO string (`"2026-10-18"`). Loading goes through the normal constructor, so validation runs again. |
| `Pet.to_dict()` / `Pet.from_dict()` | Stores the pet's details and its tasks as a nested list. |
| `Owner.to_dict()` / `Owner.from_dict()` | Stores the owner and all pets (and therefore every task). |
| `Owner.save_to_json(path)` | Writes the dict with `json.dump`. It writes to a temporary file and then swaps it in with `os.replace`, so a crash mid-save can't leave a half-written `data.json`. |
| `Owner.load_from_json(path)` | Reads and rebuilds the `Owner`. Raises `FileNotFoundError` if there is no file and `ValueError` if the JSON is invalid, a key is missing, or a value fails validation. |

**Files modified for persistence**

- `pawpal_system.py`: added the `to_dict`/`from_dict` methods on `Task`, `Pet` and `Owner`, plus `save_to_json` and `load_from_json` on `Owner`.
- `app.py`: loads `data.json` at start-up and saves after changes.
- `tests/test_pawpal.py`: 10 new tests covering the round trip, the JSON contents, a missing file, corrupt or malformed files, invalid task values, and that loaded data keeps working.
- `README.md`: this section.
- `data.json` (created at runtime, not part of the source). You may want to leave it out of version control, since it holds your personal pet data. To start over, delete the file.

## 📸 Demo Walkthrough

### The app at a glance

Run `streamlit run app.py`. The page has four sections, top to bottom:

1. **Owner.** Set your name and how many minutes you have available today.
2. **Pets.** Add a pet with a name and species. Duplicate or empty names are rejected.
3. **Tasks.** Add a task for a pet (title, duration, priority, time of day, frequency and an optional fixed `HH:MM` time). Below the form you can:
   - filter the list by pet and by status (pending, completed, all),
   - read the table, which is sorted by time,
   - open **Mark a task complete** to finish a task (recurring tasks create their next occurrence),
   - open **Change a task's time** to fix a clash.
4. **Today's Schedule.** Press **Generate schedule** to see the plan, summary numbers (scheduled, minutes used, skipped), any skipped tasks with reasons, and a **Why this plan?** explanation.

### Example workflow

1. Set the owner to "Jordan" with 90 minutes available.
2. Add two pets: Mochi (dog) and Luna (cat).
3. Add tasks out of order, for example Mochi's "Evening walk" at 18:00, Mochi's "Morning walk" at 07:30, and Luna's "Medication" at 18:00. The table shows them sorted by time.
4. Because the evening walk and the medication share 18:00, a **Time clash** warning appears above the task list. Open **Change a task's time**, move the medication to 19:00, and the warning disappears.
5. Filter to "Luna" and "Pending" to see only her open tasks.
6. Mark Luna's daily "Breakfast" complete. The app confirms the next one is due tomorrow, and the original moves to the Completed filter.
7. Press **Generate schedule** to see today's plan, which tasks were skipped for lack of time, and why.

### Scheduler behaviors shown

- **Sorting:** tasks added out of order come back in chronological order, untimed tasks last.
- **Filtering:** by pet name and by completed or pending status.
- **Conflict warnings:** two tasks at the same time produce a readable warning, not an error.
- **Recurrence:** completing a daily task creates a copy due the next day; a one-off task creates nothing.
- **Time budget:** lower-priority tasks that no longer fit are skipped with a reason.

### Sample CLI output

This is the output of `python main.py`, which adds six tasks out of order and exercises each behavior above:

```
All tasks, as added
╭────────┬───────┬─────────────────┬────────────┬───────┬───────────┬────────────┬────────────╮
│ Time   │ Pet   │ Task            │ Priority   │   Min │ Repeats   │ Due        │ Status     │
├────────┼───────┼─────────────────┼────────────┼───────┼───────────┼────────────┼────────────┤
│ 18:00  │ Mochi │ 🐕 Evening walk │ 🟡 Medium  │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 07:30  │ Mochi │ 🐕 Morning walk │ 🔴 High    │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ -      │ Mochi │ 🛁 Grooming     │ 🟢 Low     │    45 │ weekly    │ 2026-10-18 │ ⏳ Pending │
│ 08:00  │ Luna  │ 🥣 Breakfast    │ 🔴 High    │    10 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 18:00  │ Luna  │ 💊 Medication   │ 🔴 High    │     5 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 12:15  │ Luna  │ 🎾 Laser play   │ 🟡 Medium  │    15 │ once      │ 2026-10-18 │ ⏳ Pending │
╰────────┴───────┴─────────────────┴────────────┴───────┴───────────┴────────────┴────────────╯

Sorted by time
╭────────┬───────┬─────────────────┬────────────┬───────┬───────────┬────────────┬────────────╮
│ Time   │ Pet   │ Task            │ Priority   │   Min │ Repeats   │ Due        │ Status     │
├────────┼───────┼─────────────────┼────────────┼───────┼───────────┼────────────┼────────────┤
│ 07:30  │ Mochi │ 🐕 Morning walk │ 🔴 High    │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 08:00  │ Luna  │ 🥣 Breakfast    │ 🔴 High    │    10 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 12:15  │ Luna  │ 🎾 Laser play   │ 🟡 Medium  │    15 │ once      │ 2026-10-18 │ ⏳ Pending │
│ 18:00  │ Mochi │ 🐕 Evening walk │ 🟡 Medium  │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 18:00  │ Luna  │ 💊 Medication   │ 🔴 High    │     5 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ -      │ Mochi │ 🛁 Grooming     │ 🟢 Low     │    45 │ weekly    │ 2026-10-18 │ ⏳ Pending │
╰────────┴───────┴─────────────────┴────────────┴───────┴───────────┴────────────┴────────────╯

Only Luna's tasks
╭────────┬───────┬───────────────┬────────────┬───────┬───────────┬────────────┬────────────╮
│ Time   │ Pet   │ Task          │ Priority   │   Min │ Repeats   │ Due        │ Status     │
├────────┼───────┼───────────────┼────────────┼───────┼───────────┼────────────┼────────────┤
│ 08:00  │ Luna  │ 🥣 Breakfast  │ 🔴 High    │    10 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 18:00  │ Luna  │ 💊 Medication │ 🔴 High    │     5 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 12:15  │ Luna  │ 🎾 Laser play │ 🟡 Medium  │    15 │ once      │ 2026-10-18 │ ⏳ Pending │
╰────────┴───────┴───────────────┴────────────┴───────┴───────────┴────────────┴────────────╯

✅ Completed 'Breakfast' -> next occurrence due 2026-10-19
✅ Completed one-off 'Laser play' -> next: None

Pending tasks
╭────────┬───────┬─────────────────┬────────────┬───────┬───────────┬────────────┬────────────╮
│ Time   │ Pet   │ Task            │ Priority   │   Min │ Repeats   │ Due        │ Status     │
├────────┼───────┼─────────────────┼────────────┼───────┼───────────┼────────────┼────────────┤
│ 18:00  │ Mochi │ 🐕 Evening walk │ 🟡 Medium  │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 07:30  │ Mochi │ 🐕 Morning walk │ 🔴 High    │    30 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ -      │ Mochi │ 🛁 Grooming     │ 🟢 Low     │    45 │ weekly    │ 2026-10-18 │ ⏳ Pending │
│ 18:00  │ Luna  │ 💊 Medication   │ 🔴 High    │     5 │ daily     │ 2026-10-18 │ ⏳ Pending │
│ 08:00  │ Luna  │ 🥣 Breakfast    │ 🔴 High    │    10 │ daily     │ 2026-10-19 │ ⏳ Pending │
╰────────┴───────┴─────────────────┴────────────┴───────┴───────────┴────────────┴────────────╯

Completed tasks
╭────────┬───────┬───────────────┬────────────┬───────┬───────────┬────────────┬──────────╮
│ Time   │ Pet   │ Task          │ Priority   │   Min │ Repeats   │ Due        │ Status   │
├────────┼───────┼───────────────┼────────────┼───────┼───────────┼────────────┼──────────┤
│ 08:00  │ Luna  │ 🥣 Breakfast  │ 🔴 High    │    10 │ daily     │ 2026-10-18 │ ✅ Done  │
│ 12:15  │ Luna  │ 🎾 Laser play │ 🟡 Medium  │    15 │ once      │ 2026-10-18 │ ✅ Done  │
╰────────┴───────┴───────────────┴────────────┴───────┴───────────┴────────────┴──────────╯

Conflict check
🚨 Conflict on 2026-10-18 at 18:00 (different pets): Mochi: Evening walk, Luna: Medication

=== Today's Schedule for Jordan (90 min available) ===
📅 Plan for 2026-10-18
╭─────────────┬───────┬─────────────────┬────────────┬───────╮
│ Time        │ Pet   │ Task            │ Priority   │   Min │
├─────────────┼───────┼─────────────────┼────────────┼───────┤
│ 08:00-08:30 │ Mochi │ 🐕 Morning walk │ 🔴 High    │    30 │
│ 08:30-08:35 │ Luna  │ 💊 Medication   │ 🔴 High    │     5 │
│ 08:35-09:05 │ Mochi │ 🐕 Evening walk │ 🟡 Medium  │    30 │
╰─────────────┴───────┴─────────────────┴────────────┴───────╯
⏱  65 min scheduled, 1 skipped
╭───────┬────────────────┬────────────┬────────────────────────────────────────────────────────────╮
│ Pet   │ Skipped task   │ Priority   │ Why                                                        │
├───────┼────────────────┼────────────┼────────────────────────────────────────────────────────────┤
│ Mochi │ 🛁 Grooming    │ 🟢 Low     │ needs 45 min but only 25 min of the 90 min budget remained │
╰───────┴────────────────┴────────────┴────────────────────────────────────────────────────────────╯

--- Why this plan ---
Included Mochi - Morning walk: high priority, fits within the available time
Included Luna - Medication: high priority, fits within the available time
Included Mochi - Evening walk: medium priority, fits within the available time
Skipped Mochi - Grooming: needs 45 min but only 25 min of the 90 min budget remained
```

Notice that the plan places the 18:00 medication at 08:30 and the 18:00 evening walk at 08:35. That is the known limitation above: the plan fills time by priority and does not yet pin tasks to their fixed times.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
