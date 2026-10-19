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

*To be completed after implementation.* No backend code exists yet, so the design has not changed. After building the classes, I will reveiw this agian.

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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
