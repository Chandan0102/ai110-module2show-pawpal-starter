# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design is built around the three core actions a user performs: entering owner and pet info, adding and editing care tasks, and generating a daily plan. I wanted each action to map to one clear class, and I kept scheduling logic out of the data classes so it could be tested on its own.

I included five classes:

- **Owner**: holds the owner's name, the time available per day, and their preferences. It owns a list of pets and is the single entry point for reaching all of their tasks.
- **Pet**: holds the pet's name and species, and the list of care tasks for that pet. It is responsible for adding, editing and removing its own tasks.
- **Task**: represents one care activity (walk, feeding, meds, enrichment, grooming). It stores a title, duration in minutes, and priority (low, medium or high). It is a plain data object with no scheduling logic.
- **Scheduler**: takes an Owner and builds the daily plan. It collects tasks across pets, orders them by priority, fits them into the owner's available time, and records the reason each task was included or left out. This is where all the planning logic lives.
- **DailyPlan**: the result the Scheduler returns. It holds the ordered, time-slotted entries, the tasks that were skipped, and the explanation text. 

The main relationships are: an Owner has many Pets, a Pet has many Tasks, the Scheduler uses an Owner to produce a DailyPlan, and a DailyPlan refers to the Tasks it scheduled.

**b. Design changes**

After drafting the class skeleton in `pawpal_system.py`, I asked an AI assistant to review it for missing relationships and logic bottlenecks. I made three changes based on that feedback:

- **Tasks are identified by `task_id`, not title.** `edit_task` and `remove_task` originally looked tasks up by title, which breaks as soon as a pet has two tasks with the same name (for example two "Feeding" entries). Each Task now gets a unique id, and those methods take it.
- **`total_minutes` is computed, not stored.** On `DailyPlan` it was a separate field that could drift out of sync with `entries`. It is now a property derived from the entries.
- **Added `Priority.from_str`.** The Streamlit UI sends priority as a string ("low", "medium", "high"), but the model uses an enum, so I added a conversion at that boundary.

The review also raised points I chose not to act on yet, and will revisit during implementation:

- Recurring tasks: I added a `frequency` field, but nothing uses it yet, so a completed task can't reset for the next day.
- `preferred_time` is a free-form string, which will be hard for the scheduler to use.
- The greedy "fit to time" step can skip a long high-priority task and then fill the day with short low-priority ones. I will treat this as a deliberate tradeoff and describe it in section 2.
- `start_time` as a plain `time` can't represent a plan that runs past midnight.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers these constraints, roughly in order of importance:

1. **The owner's available time.** This is a hard limit. `_fit_to_time()` never schedules more minutes than the owner has, and anything that doesn't fit is skipped with a reason.
2. **Task priority.** High-priority tasks (meds, feeding) are placed first, so they are the last to be dropped when time is short.
3. **Preferred time of day, then duration.** These only break ties between tasks of the same priority: morning before afternoon before evening, and shorter tasks before longer ones.
4. **Whether a task is still pending and due.** Completed tasks and tasks due on a future day (such as tomorrow's copy of a daily task) are left out.

Fixed `HH:MM` times are used for sorting the task list and for conflict warnings, but not yet to place tasks in the plan. Owner preferences exist as a field but are not used by the scheduler.

I ranked time and priority first because they decide whether a plan is even possible and whether the important tasks survive. A missed walk is a nuisance, but missed medication is a real problem, so priority has to beat convenience. Time of day and duration are comfort details, so they only decide ties.

**b. Tradeoffs**

**Conflict detection only checks for exact start-time matches, not overlapping durations.** `Scheduler.detect_conflicts()` groups pending tasks by `(due_date, start_time)`. Two tasks at 18:00 raise a warning, but a 30-minute walk at 18:00 and a medication at 18:15 do not, even though they overlap.

This is reasonable for a first version. The check is a single pass with a dictionary, it is easy to read and test, and it never crashes the app because it returns warning strings. It also fits how pet owners think about care tasks, which are usually "18:00 walk" and "18:00 meds" rather than precise time ranges. Catching overlaps would mean comparing every pair of tasks and handling tasks that run past midnight, and I judged that too much complexity for the benefit. The cost is missed warnings for near-misses, so with more time I would compare `start_time` plus `duration_minutes` ranges.

A related simplification is that the daily plan still packs tasks back to back from the start time and does not place tasks at their fixed `start_time`. Fixed times currently drive sorting and conflict warnings only.

---

## 3. AI Collaboration

**a. How you used AI**

I used an AI assistant at every stage, not only for writing code:

- **Design brainstorming:** I asked it to list the building blocks of the system with their attributes and methods, then turned that into a Mermaid class diagram.
- **Scaffolding:** I had it generate the class skeleton in `pawpal_system.py` from the UML, using dataclasses for Task, Pet and Owner.
- **Design review:** I asked it to review the skeleton for missing relationships and logic bottlenecks.
- **Implementation and tests:** It filled in the class logic, wrote a `main.py` terminal demo, drafted the pytest tests, and added docstrings.
- **Algorithms, UI and docs:** It implemented sorting, filtering, recurrence and conflict detection, connected them to the Streamlit UI, redrew the UML to match the final code, and drafted the README.

The most helpful prompts were specific and tied to the code that already existed, such as "review my skeleton for missing relationships and bottlenecks" and "make the Scheduler read from an Owner method rather than a single pet". Broad prompts gave generic answers. Prompts that named a concrete constraint gave answers I could act on.

**b. Judgment and verification**

I did not accept the AI's design review wholesale. It raised seven points: identifying tasks by id, a derived `total_minutes`, a priority string-to-enum conversion, recurring tasks, a free-form `preferred_time`, the greedy fit-to-time behavior, and the midnight limitation of `start_time`. I accepted the first three because each fixed a concrete problem: duplicate titles breaking edit and remove, a stored total that could drift from the entries, and the UI sending strings where the model uses an enum. I rejected the rest for now. They would have made the first version much bigger, and the greedy behavior is a tradeoff I want to describe myself in section 2. I recorded them in section 1b so they are not lost.

I verified the result instead of trusting it:

- I ran `main.py` with two pets and six tasks and read the schedule and the reasons. This showed the multi-pet logic works, and it also exposed a weakness: a high-priority evening medication was scheduled at 08:40, because `preferred_time` only affects ordering and does not pin a time slot.
- I wrote pytest tests and ran them in the project's virtual environment. Asking for a test plan of edge cases found two real bugs in code the AI had already written and that looked fine: completing the same recurring task twice created duplicate copies, and a failed `edit_task` raised an error but still left the task changed. I fixed both and added tests so they stay fixed.

**c. AI strategy and being the lead architect**

- **Most effective features:** Scaffolding the class skeleton from the UML, asking for a review of existing code, and having the AI edit several files in one pass (logic, `main.py`, tests, UI and README together) were the biggest time savers. Running the code and tests after every change mattered just as much, because it turned "looks right" into "works".
- **A suggestion I modified:** The natural place to put recurrence was inside `Task.mark_complete()`, but a task doesn't know its pet's task list, and that would have turned `Task` into more than a plain data object. I kept `mark_complete()` simple and put recurrence in `Pet.complete_task()`, with `Task.next_occurrence()` building the copy. The same instinct applied to conflicts: a full overlap check was possible, but I kept the simple exact-match check and documented the tradeoff. I also kept the Scheduler reading every pet through `Owner.get_all_tasks()` rather than looking at one pet.
- **Working in phases:** I split the project into phases (design, skeleton, logic, algorithms, tests, UI, docs). Each phase started from the files already on disk, such as the UML, `pawpal_system.py` and the tests, rather than from what an earlier conversation remembered. That kept each request narrow and made it easy to check what changed. It also meant the UML and README could go out of date between phases, so I had to schedule a deliberate step to bring them back in line.
- **What I learned as the architect:** The AI is fast and usually correct, but it will happily build whatever is asked, including more than is needed. My job was to decide what the system should be: which class owns which responsibility, what is out of scope for now, and which tradeoffs are acceptable. Then I had to check its work, because confident-looking code still contained bugs. The best results came from giving it small, specific tasks and reviewing each one.

---

## 4. Testing and Verification

**a. What you tested**

The suite in `tests/test_pawpal.py` has 34 tests covering:

- **Plan generation:** priority ordering, back-to-back times from the start time, stable order for ties, an empty owner or a pet with no tasks, a zero-minute budget, a task that exactly fits the remaining time versus one that is a minute too long, and exclusion of completed tasks. Overdue tasks are included.
- **Sorting and filtering:** chronological order including `"8:00"` versus `"18:00"`, untimed tasks last, equal times keeping their order, filtering by pet and by status, and an unknown pet.
- **Recurrence:** daily (+1 day) and weekly (+7 days) copies, one-off tasks not repeating, the copy keeping the task's details, and completing the same task twice not duplicating it.
- **Conflicts:** two or three tasks at the same time, same-pet versus different-pet labels, and ignoring completed, untimed and other-date tasks. A near-overlap is deliberately not flagged.
- **Validation:** invalid durations, frequencies, priorities and times, editing a task (including a failed edit leaving it unchanged), and unknown ids or fields.

These matter because the scheduler's value is that its output can be trusted: a plan that drops medication, loses a recurring task or crashes on an empty pet would defeat the purpose. The edge-case tests also found two real bugs.

**b. Confidence**

I am fairly confident in the core behavior: the plan respects the time budget and priority order, and sorting, filtering, recurrence and conflict detection behave as described, with every test passing. I am less confident outside what is tested, since the UI was checked by driving it through Streamlit's test harness and not by clicking through it in a browser.

If I had more time I would test:

- A plan that runs past midnight, which currently wraps the clock time.
- Overlapping tasks (a 30-minute task at 18:00 and another at 18:15), once overlap detection exists.
- Two pets with the same name, which makes filtering and removal ambiguous in the logic layer.
- Placing tasks at their fixed times in the plan, once that is implemented.
- The Streamlit app itself, with more automated UI tests.

---

## 5. Reflection

**a. What went well**

I am most satisfied with the separation between the data classes and the scheduling logic. `Owner`, `Pet` and `Task` just hold data, `Scheduler` does the thinking, and the UI only displays a `DailyPlan`. Because of that, I could add sorting, filtering, recurrence and conflict detection without rewriting anything, and the same logic runs in the terminal demo, the tests and the Streamlit app. I am also pleased that every decision in the plan comes with a reason the user can read.

**b. What you would improve**

In another iteration I would:

- **Place tasks at their fixed times.** Right now a task pinned to 18:00 can appear at 08:05 in the plan, which is the biggest gap between what the user enters and what the plan shows.
- **Detect overlapping tasks** by comparing start time plus duration, instead of only exact matches.
- **Use `preferred_time` and owner preferences** in the scheduler, as typed values instead of a free-form string and an unused dictionary.
- **Save data between sessions,** since pets and tasks currently disappear when the browser session ends.

**c. Key takeaway**

AI can produce a lot of working code quickly, but it cannot decide what the system should be or notice what is missing. The design decisions that mattered most were mine: which class owns which job, what to leave out for now, and which tradeoffs to accept. The most valuable habit was verifying everything. Running the code, writing edge-case tests and asking "what could go wrong here?" caught bugs that looked fine on the page. Treating the AI as a fast collaborator that I review, not an authority I trust, is what kept the design clean.
