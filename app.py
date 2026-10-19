import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant: add pets and tasks, then generate today's plan.")

# --- Application "memory" ---------------------------------------------------
# Streamlit reruns this script on every interaction, so the Owner is kept in
# st.session_state and only created if it isn't there yet.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)
owner: Owner = st.session_state.owner

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
        c4, c5 = st.columns(2)
        with c4:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        with c5:
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
                            preferred_time=None if when == "any" else when,
                            frequency=frequency,
                            start_time=fixed_time.strip() or None,
                        )
                    )
                    st.success(f"Added '{title.strip()}' to {target}.")
                except ValueError as err:
                    st.error(str(err))

    scheduler = Scheduler(owner)
    all_tasks = scheduler.sort_by_time()
    for warning in scheduler.detect_conflicts():
        st.warning(warning)
    if all_tasks:
        st.write("Current tasks (sorted by time):")
        st.table(
            [
                {
                    "Pet": pet.name,
                    "Task": task.title,
                    "Minutes": task.duration_minutes,
                    "Priority": task.priority.name.lower(),
                    "Time": task.start_time or "-",
                    "Time of day": task.preferred_time or "any",
                    "Frequency": task.frequency,
                }
                for pet, task in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule ---------------------------------------------------------------
st.subheader("Today's Schedule")
if st.button("Generate schedule"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        plan = Scheduler(owner).generate_plan()
        st.success(
            f"Scheduled {len(plan.entries)} task(s), {plan.total_minutes} of "
            f"{owner.available_minutes} minutes."
        )
        if plan.entries:
            st.table(
                [
                    {
                        "Time": f"{i.start:%H:%M}-{i.end:%H:%M}",
                        "Pet": i.pet.name,
                        "Task": i.task.title,
                        "Priority": i.task.priority.name.lower(),
                    }
                    for i in plan.entries
                ]
            )
        if plan.skipped:
            st.warning("Skipped (not enough time):")
            for s in plan.skipped:
                st.write(f"- {s.pet.name}: {s.task.title} — {s.reason}")
        with st.expander("Why this plan?"):
            st.text(plan.explain())
