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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

I used an AI assistant at every stage, not only for writing code:

- **Design brainstorming:** I asked it to list the building blocks of the system with their attributes and methods, then turned that into a Mermaid class diagram.
- **Scaffolding:** I had it generate the class skeleton in `pawpal_system.py` from the UML, using dataclasses for Task, Pet and Owner.
- **Design review:** I asked it to review the skeleton for missing relationships and logic bottlenecks.
- **Implementation and tests:** It filled in the class logic, wrote a `main.py` terminal demo, drafted the first two pytest tests, and added docstrings.

The most helpful prompts were specific and tied to the code that already existed, such as "review my skeleton for missing relationships and bottlenecks" and "make the Scheduler read from an Owner method rather than a single pet". Broad prompts gave generic answers. Prompts that named a concrete constraint gave answers I could act on.

**b. Judgment and verification**

I did not accept the AI's design review wholesale. It raised seven points: identifying tasks by id, a derived `total_minutes`, a priority string-to-enum conversion, recurring tasks, a free-form `preferred_time`, the greedy fit-to-time behavior, and the midnight limitation of `start_time`. I accepted the first three because each fixed a concrete problem: duplicate titles breaking edit and remove, a stored total that could drift from the entries, and the UI sending strings where the model uses an enum. I rejected the rest for now. They would have made the first version much bigger, and the greedy behavior is a tradeoff I want to describe myself in section 2. I recorded them in section 1b so they are not lost.

I verified the result instead of trusting it:

- I ran `main.py` with two pets and six tasks and read the schedule and the reasons. This showed the multi-pet logic works, and it also exposed a weakness: a high-priority evening medication was scheduled at 08:40, because `preferred_time` only affects ordering and does not pin a time slot.
- I wrote pytest tests for task completion and for adding a task to a pet, and ran them in the project's virtual environment. Both pass.

These checks cover only the basics. I have not yet tested the Scheduler's edge cases, such as an empty plan or a task longer than the whole time budget.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
