from pathlib import Path

import streamlit as st

from pawpal_format import CATEGORY_EMOJI, priority_badge, status_badge, task_label
from pawpal_system import Owner, Pet, Priority, Scheduler, Task

DATA_FILE = Path(__file__).parent / "data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant: add pets and tasks, then generate today's plan.")

# --- Application "memory" ---------------------------------------------------
# Streamlit reruns this script on every interaction, so the Owner is kept in
# st.session_state and only created if it isn't there yet. On a fresh start it is
# loaded from data.json, so pets and tasks survive restarts.
if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
    except FileNotFoundError:
        st.session_state.owner = Owner(name="Jordan", available_minutes=90)
    except ValueError as err:
        # Keep the unreadable file as a backup instead of overwriting it.
        DATA_FILE.replace(DATA_FILE.with_name(DATA_FILE.name + ".corrupt"))
        st.session_state.owner = Owner(name="Jordan", available_minutes=90)
        st.warning(f"Saved data could not be read and was set aside as data.json.corrupt ({err}).")
owner: Owner = st.session_state.owner


def save() -> None:
    """Write the current owner to data.json."""
    try:
        owner.save_to_json(DATA_FILE)
    except OSError as err:
        st.error(f"Could not save your data: {err}")

# --- Owner ------------------------------------------------------------------
st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Minutes available today", min_value=5, max_value=600,
            value=owner.available_minutes, step=5,
        )
    )

st.divider()

# --- Pets -------------------------------------------------------------------
st.subheader("Pets")
with st.form("add_pet_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        pet_name = st.text_input("Pet name")
    with c2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        name = pet_name.strip()
        if not name:
            st.error("Please enter a pet name.")
        elif any(p.name.lower() == name.lower() for p in owner.pets):
            st.error(f"You already have a pet named {name}.")
        else:
            owner.add_pet(Pet(name=name, species=species))
            st.success(f"Added {name}.")

if owner.pets:
    st.write("Your pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks ------------------------------------------------------------------
st.subheader("Tasks")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        target = st.selectbox("Pet", [p.name for p in owner.pets])
        title = st.text_input("Task title", placeholder="Morning walk")
        c1, c2, c3 = st.columns(3)
        with c1:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with c2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with c3:
            when = st.selectbox("Time of day", ["any", "morning", "afternoon", "evening"])
        c4, c5, c6 = st.columns(3)
        with c4:
            category = st.selectbox(
                "Type", list(CATEGORY_EMOJI), format_func=lambda c: f"{CATEGORY_EMOJI[c]} {c}"
            )
        with c5:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        with c6:
            fixed_time = st.text_input("Fixed time (HH:MM, optional)", placeholder="18:00")
        if st.form_submit_button("Add task"):
            if not title.strip():
                st.error("Please enter a task title.")
            else:
                pet = next(p for p in owner.pets if p.name == target)
                try:
                    pet.add_task(
                        Task(
                            title=title.strip(),
                            duration_minutes=int(duration),
                            priority=Priority.from_str(priority),
                            category=category,
                            preferred_time=None if when == "any" else when,
                            frequency=frequency,
                            start_time=fixed_time.strip() or None,
                        )
                    )
                    st.success(f"Added '{title.strip()}' to {target}.")
                except ValueError as err:
                    st.error(str(err))

    scheduler = Scheduler(owner)

    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))

    # Conflict warnings come first so the owner sees problems before the list.
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts:
        st.warning(
            f"**Time clash.** {warning}\n\n"
            "You can't do these at once. Use *Change a task's time* below to move one of them."
        )

    # Filters: pet and status, applied with Scheduler.filter_tasks().
    f1, f2 = st.columns(2)
    with f1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with f2:
        status_filter = st.radio("Show status", ["Pending", "Completed", "All"], horizontal=True)

    shown = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"Pending": False, "Completed": True, "All": None}[status_filter],
    )
    shown = scheduler.sort_by_time(shown)  # chronological, untimed tasks last

    if shown:
        st.caption(f"{len(shown)} task(s), sorted by time (tasks with no fixed time last).")
        st.table(
            [
                {
                    "Time": task.start_time or "-",
                    "Pet": pet.name,
                    "Task": task_label(task),
                    "Minutes": task.duration_minutes,
                    "Priority": priority_badge(task.priority),
                    "Repeats": task.frequency,
                    "Due": task.due_date.isoformat(),
                    "Status": status_badge(task),
                }
                for pet, task in shown
            ]
        )
    elif owner.get_all_tasks():
        st.info("No tasks match these filters.")
    else:
        st.info("No tasks yet. Add one above.")

    def label(pet: Pet, task: Task) -> str:
        return f"{pet.name}: {task.title} ({task.start_time or 'no fixed time'}, due {task.due_date})"

    pending = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    if pending:
        options = {label(p, t): (p, t) for p, t in pending}

        with st.expander("Mark a task complete"):
            choice = st.selectbox("Task", list(options), key="complete_choice")
            if st.button("Mark complete"):
                pet, task = options[choice]
                nxt = pet.complete_task(task.task_id)
                st.session_state.flash = (
                    f"Completed '{task.title}'. Next one is due {nxt.due_date}."
                    if nxt
                    else f"Completed '{task.title}'."
                )
                save()
                st.rerun()

        with st.expander("Change a task's time"):
            choice = st.selectbox("Task", list(options), key="edit_choice")
            new_time = st.text_input("New fixed time (HH:MM, blank to clear)", key="new_time")
            if st.button("Update time"):
                pet, task = options[choice]
                try:
                    pet.edit_task(task.task_id, start_time=new_time.strip() or None)
                    st.session_state.flash = f"Updated the time for '{task.title}'."
                    save()
                    st.rerun()
                except ValueError as err:
                    st.error(str(err))

    with st.expander("Find a free time slot"):
        st.caption("Looks for the earliest gap between 08:00 and 22:00 around today's fixed-time tasks.")
        need = st.number_input("Minutes needed", min_value=1, max_value=600, value=30, key="slot_minutes")
        if st.button("Find slot"):
            slot = Scheduler(owner).find_next_slot(int(need))
            if slot is None:
                st.warning(f"No free {int(need)}-minute gap left today.")
            else:
                st.success(f"🕒 Next free {int(need)}-minute slot starts at {slot:%H:%M}.")

st.divider()

# --- Schedule ---------------------------------------------------------------
st.subheader("Today's Schedule")
st.caption(
    "The plan fills your available time by priority, starting at 08:00. "
    "Fixed times are used for sorting and clash warnings."
)
if st.button("Generate schedule"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        plan = Scheduler(owner).generate_plan()
        m1, m2, m3 = st.columns(3)
        m1.metric("Scheduled", f"{len(plan.entries)} tasks")
        m2.metric("Time used", f"{plan.total_minutes} / {owner.available_minutes} min")
        m3.metric("Skipped", f"{len(plan.skipped)} tasks")

        if plan.entries:
            st.success("Here is today's plan.")
            st.table(
                [
                    {
                        "Time": f"{i.start:%H:%M}-{i.end:%H:%M}",
                        "Pet": i.pet.name,
                        "Task": task_label(i.task),
                        "Priority": priority_badge(i.task.priority),
                    }
                    for i in plan.entries
                ]
            )
        else:
            st.info("Nothing to schedule today: every task is done or not due yet.")
        if plan.skipped:
            st.warning("Some tasks did not fit in your available time:")
            for s in plan.skipped:
                st.write(f"- **{s.pet.name}: {s.task.title}** — {s.reason}")
        with st.expander("Why this plan?"):
            st.text(plan.explain())

# Persist whatever the user changed during this run.
save()
