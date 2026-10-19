# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Implementation summary

The backend lives in `pawpal_system.py` and is built from a few small classes:

- **Task** (dataclass): one care activity with a title, duration, priority, category, preferred time of day, frequency and completion status. Each task has a unique `task_id`.
- **Pet** (dataclass): pet details plus its own list of tasks, with methods to add, edit, remove and list them.
- **Owner** (dataclass): the owner's name and daily time budget, plus a list of pets. `get_all_tasks()` returns every pet's tasks together as `(pet, task)` pairs.
- **Scheduler**: the "brain". It reads tasks through `Owner.get_all_tasks()` (so every pet is covered), skips completed tasks, sorts by priority, time of day and duration, keeps adding tasks until the owner's time budget runs out, and lays them out back to back from the start time.
- **DailyPlan**, **ScheduledItem** and **SkippedTask**: the result. A plan holds the scheduled items (task, pet, start, end, reason) and the skipped tasks with the reason each did not fit. `summary()` and `explain()` turn it into readable text.

How they fit together: `Owner` → `Pet` → `Task` hold the data, `Scheduler` reads from the `Owner` and produces a `DailyPlan`, and the UI only has to display that plan.

Try it in the terminal with `python main.py`, and run the tests with `pytest`. The Streamlit UI in `app.py` is not connected to this logic yet.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```
(.venv) PS C:\Users\sinha\Desktop\AI110\ai110-module2show-pawpal-starter> python main.py
=== Today's Schedule for Jordan (90 min available) ===
Plan for 2026-10-18
  08:00-08:10  Luna: Breakfast (10 min) [high]
  08:10-08:40  Mochi: Morning walk (30 min) [high]
  08:40-08:45  Luna: Evening medication (5 min) [high]
  08:45-09:00  Luna: Laser play (15 min) [medium]
  09:00-09:20  Mochi: Training session (20 min) [medium]
Total: 80 min, 1 skipped

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
