# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

The agent was Claude Code, running in VS Code with access to the project files, a terminal and the project's virtual environment. I gave it one phase at a time and it edited several files per request.

**What task did you give the agent?**

I asked for the project in phases. Each request named the goal and the constraints, and the agent worked across files without me editing each one:

| Phase | What I asked | Files the agent modified or created |
|-------|--------------|-------------------------------------|
| Design | Identify the core user actions, brainstorm the classes with attributes and methods, draw a Mermaid UML | `diagrams/uml.mmd` (later renamed), `reflection.md` |
| Skeleton and logic | Generate dataclass stubs from the UML, then implement `Task`, `Pet`, `Owner` and `Scheduler`, with the Scheduler reading every pet through `Owner.get_all_tasks()` | `pawpal_system.py`, `main.py` |
| UI | Connect the classes to Streamlit and keep the data in `st.session_state` | `app.py` |
| Smarter scheduling | Sorting by time, filtering, recurring tasks, conflict detection | `pawpal_system.py`, `main.py`, `app.py`, `tests/test_pawpal.py`, `README.md`, `reflection.md` |
| Testing | Plan edge cases, then build the suite | `tests/test_pawpal.py`, `pytest.ini`, `pawpal_system.py` (bug fixes) |
| Final UML | Update the diagram to match the final code | `diagrams/uml_final.mmd` |
| Challenges | Data persistence to `data.json`, priority-first sorting, formatted output, and the third algorithm (next available slot) | `pawpal_system.py`, `pawpal_format.py` (new), `main.py`, `app.py`, `requirements.txt`, `tests/test_pawpal.py`, `tests/test_format.py` (new), `README.md` |

For this challenge in particular, I asked for a third algorithm beyond the basics. The agent proposed and built `Scheduler.find_next_slot()`: given a duration, it returns the earliest free gap in the day around pending tasks with fixed times.

**What did the agent do?**

For the next-available-slot algorithm it:

1. Chose the feature because it fills a real gap. The exact-match conflict check can't see overlaps, and fixed times were only used for sorting.
2. Wrote `find_next_slot()` in `pawpal_system.py`. It sorts the blocked time ranges, sweeps once with a cursor, and returns the first gap that fits or `None`. It works in whole minutes so nothing wraps past midnight.
3. Wrote 10 tests covering an empty day, an exact fit, an early gap, overlapping and unsorted tasks, a full day, running past the end of the day, ignored tasks (completed, untimed, other day), a custom day and window, and bad arguments.
4. Added a third demo to `main.py`, a "Find a free time slot" panel in `app.py`, and a README section with the real CLI output.
5. Ran the tests, `main.py` and the Streamlit app (through Streamlit's test harness) to check each change.

Across the whole project it also ran `pytest` after each phase, regenerated the README's CLI output from real runs, and installed `tabulate` and `wcwidth` into the virtual environment.

**What did you have to verify or fix manually?**

The agent's output needed checking, and some of it was wrong:

- **Bugs in code that looked fine.** Asking the agent for an edge-case test plan found two real bugs in code it had already written: completing the same recurring task twice created duplicate copies, and a failed `edit_task` raised an error but still changed the task. I had the agent fix both and add tests.
- **Leftover draft code.** The first version of `find_next_slot()` left an unused draft block and called a helper that didn't exist yet. The editor's diagnostics flagged it, and the agent removed the draft and added the helper before anything was run.
- **A hand-typed mistake in the README.** While updating the priority example, the agent typed "Evening walk" into the sample output where the real output said "Dinner". Later it regenerated every CLI block in the README directly from real program output so they can't drift.
- **A shell command that never ran.** One long command failed to parse, so none of its changes were applied. Splitting it into smaller steps made the failure clear instead of leaving a half-applied state.
- **Environment surprises.** `pytest` and `tabulate` are installed in the project's virtual environment, not the system Python, so plain `python` commands failed or behaved differently. The default Windows console also can't print emoji, so `main.py` now switches its output to UTF-8.
- **My own corrections.** I pasted real terminal output into the README, shortened some wording in `reflection.md`, and reviewed each reflection answer against what really happened. In the AI collaboration section, I treated the agent's descriptions of my choices as drafts to confirm.
- **Judgment calls I kept.** I accepted three suggestions from the agent's design review and deferred four, and kept conflict detection to exact matches. Where the plan ignores fixed times, I let it stay as a documented limitation rather than a rushed fix.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
