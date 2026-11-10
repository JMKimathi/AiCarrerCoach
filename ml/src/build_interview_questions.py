"""Generate a broad, varied interview question bank for every catalogue role.

Writes ml/data/careers/interview_questions.csv. Each role gets a different mix
drawn from eight question styles:

  skill        probes each of the role's core skills, two different angles per skill
  behavioural  past behaviour ("tell me about a time...")
  situational  realistic scenarios written for the role's sector
  motivation   why this role, this field, this employer
  opportunity  one question per opportunity type (attachment, internship,
               graduate programme, full-time job)
  market       Kenya and international context
  ethics       only for commonly regulated roles
  curveball    reflective or unexpected questions

The wording a role receives is chosen by a stable hash of its career_id, so two
roles rarely share the same set and rebuilding gives the same file. Every row
carries what a strong answer shows and a follow-up probe an interviewer could ask.

`pick_interview_set` draws a fresh mixed set for one practice session. Pass a new
seed each session so a student does not meet the same questions in the same order.

Questions are synthetic practice material. They are not taken from any employer
and do not predict what a real panel will ask.

Usage (from the repository root):
  python ml/src/build_interview_questions.py
  python ml/src/build_interview_questions.py --check
  python ml/src/build_interview_questions.py --demo CAREER-002
"""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from build_career_catalogue import CATEGORIES, DATA_ORIGIN, DEFAULT_OUTPUT_DIR, build_rows, write_csv  # noqa: E402

# Each frame is (question, what a strong answer shows).
# Placeholders: {skill}, {role}, {a_role}, {focus}, {sector}.
SKILL_FRAMES = [
    ("Walk me through the last time you used {skill}. What were you trying to achieve and what happened?",
     "A specific example, their own actions, the result, and what they would do differently."),
    ("If you had ten minutes to teach {skill} to a first-year student, what would you cover first and why?",
     "A firm grip on the fundamentals and the ability to simplify without becoming wrong."),
    ("What is the most common mistake people make with {skill}, and how do you avoid making it yourself?",
     "Awareness of real pitfalls and a habit of checking their own work."),
    ("How do you decide that a piece of {skill} work is good enough to hand over?",
     "Clear quality standards, self-review, and knowing when to ask for a second opinion."),
    ("Tell me about something in {skill} that you found hard to learn. How did you get past it?",
     "Honesty about difficulty, a learning method, and persistence."),
    ("Your supervisor disagrees with how you approached a task involving {skill}. What do you do next?",
     "Listening first, explaining reasoning with evidence, and willingness to change course."),
    ("Where does {skill} show up in the daily work of {a_role}? Give me a realistic example.",
     "Understanding of the actual job, not only the textbook topic."),
    ("A piece of work that depends on {skill} has gone wrong. What do you check first?",
     "A calm, ordered approach to finding the cause before changing anything."),
    ("How have you kept your {skill} current outside the classroom?",
     "Self-driven learning with named sources, projects or practice."),
    ("Rate your {skill} honestly out of ten, then tell me what evidence supports that number.",
     "Accurate self-assessment backed by examples, without false modesty or exaggeration."),
    ("Describe a project where {skill} mattered more than you expected it to.",
     "Reflection on how skills connect to outcomes in real work."),
    ("Which tools or methods do you rely on for {skill}, and where do they fall short?",
     "Practical familiarity plus awareness of limits and alternatives."),
    ("You have one week before starting with us to get better at {skill}. How do you spend it?",
     "A realistic plan with priorities, not a list of everything."),
    ("Explain a decision you made in {skill} work that someone else might have made differently.",
     "Reasoning about trade-offs and ownership of the choice."),
    ("If I gave you a small {skill} task right now, how would you begin and what would you ask me?",
     "Clarifying the goal before acting and a sensible first step."),
    ("How would you explain the value of {skill} to a manager who does not have a {focus} background?",
     "Plain-language communication tied to results the manager cares about."),
]

BEHAVIOURAL_FRAMES = [
    ("Tell me about a time you had to deliver something with less time than you needed.",
     "Prioritising, communicating early about risk, and delivering something usable."),
    ("Describe a disagreement with a teammate and how it ended.",
     "Respect for the other view, focus on the work rather than the person, and a resolution."),
    ("Tell me about a mistake of yours that someone else noticed before you did.",
     "Ownership without excuses and a concrete change made afterwards."),
    ("When did you last change your mind about something important because of evidence?",
     "Openness to being wrong and the ability to update a position."),
    ("Describe a time you had to learn something quickly with very little help.",
     "Resourcefulness and a method for learning under pressure."),
    ("Tell me about feedback you received that you did not agree with.",
     "Listening, separating the useful part from the rest, and responding professionally."),
    ("Give me an example of taking responsibility for something that was not strictly your job.",
     "Initiative balanced with respect for other people's roles."),
    ("Describe a time you explained something complicated to someone outside your field.",
     "Adjusting language to the listener and checking they understood."),
    ("Tell me about a goal you set for yourself and did not reach.",
     "Honest reflection on why and what changed in their approach."),
    ("When have you worked with someone whose working style was very different from yours?",
     "Adaptability and finding a way to work together that suited both."),
    ("Describe a time you noticed a problem nobody had asked you to look for.",
     "Attention, curiosity and raising the issue through the right channel."),
    ("Tell me about a time you had to say no to a request.",
     "Judgment about priorities and saying no clearly and politely."),
    ("Describe the piece of work you are proudest of and your exact part in it.",
     "Clarity about their own contribution versus the team's."),
    ("Tell me about a time you led without having the title.",
     "Influence through example, organisation and encouragement."),
    ("When did you last ask for help, and what made you decide to ask?",
     "Knowing their limits and asking at the right moment."),
    ("Describe a period when you balanced your studies with another serious commitment.",
     "Time management and realistic choices about what to drop."),
    ("Tell me about a time a plan you were following stopped working halfway through.",
     "Recognising the change early and adjusting rather than pushing on."),
    ("Describe a time you had to work with incomplete or unreliable information.",
     "Stating assumptions, reducing risk, and checking back when facts arrived."),
]

MOTIVATION_FRAMES = [
    ("What first made you think about becoming {a_role}?",
     "A real origin story that connects to the work itself."),
    ("What do you think people misunderstand about working in {focus}?",
     "Realistic knowledge of the field beyond its public image."),
    ("Which part of {a_role}'s work do you expect to enjoy least, and how will you handle it?",
     "Realism about the job and a mature plan for the dull or hard parts."),
    ("If this role did not exist, what would you do instead and why?",
     "Self-knowledge about what really drives them."),
    ("Why should we invest in training you rather than someone with more experience?",
     "Evidence of learning speed, attitude and what they already bring."),
    ("Where do you want your work in {focus} to have taken you five years from now?",
     "Direction without rigidity, and a link between this role and the goal."),
    ("What have you done in the last six months that shows you are serious about {focus}?",
     "Recent, concrete action rather than stated interest."),
    ("What would make you leave a job in {sector}?",
     "Honest values and reasonable expectations of an employer."),
    ("Who in {sector} do you learn from, and what have you taken from them?",
     "Engagement with the field through people, writing or communities."),
    ("What does a good day at work as {a_role} look like to you?",
     "An accurate picture of the role and what they find rewarding."),
]

OPPORTUNITY_FRAMES = {
    "industrial attachment": [
        ("What do you hope to have learned by the end of your attachment that your course cannot teach you?",
         "Specific learning goals tied to practice."),
        ("How will you make yourself useful in your first two weeks, before you know much?",
         "Humility, observation and willingness to do small tasks well."),
        ("How do you plan to record what you learn during attachment?",
         "A habit of keeping a logbook or notes and reflecting on them."),
    ],
    "internship": [
        ("What would make this internship a success for you and for us?",
         "Thinking about value to the employer as well as their own learning."),
        ("Interns are often given routine tasks. How do you stay engaged and still learn?",
         "A positive attitude and looking for the reason behind each task."),
        ("Tell me about a project you would like to own by the end of the internship.",
         "Initiative with a realistic scope."),
    ],
    "graduate programme": [
        ("Graduate programmes rotate you through teams. How do you settle into a new team quickly?",
         "Asking good questions, learning names and context, and contributing early."),
        ("What would you want from a mentor during the programme?",
         "Self-awareness about growth areas and openness to coaching."),
        ("How will you decide where to specialise once the rotations end?",
         "A way of weighing interest, strength and opportunity."),
    ],
    "full-time job": [
        ("What will you need from us in your first ninety days to do this job well?",
         "A clear onboarding plan and realistic expectations."),
        ("How do you manage your own work when nobody is checking on you?",
         "Self-management, planning and reporting progress unprompted."),
        ("What would your first independent piece of work here look like?",
         "Understanding of the role's real outputs."),
    ],
}

MARKET_FRAMES = [
    ("How is work in {focus} different in Kenya from what you read about internationally?",
     "Awareness of local conditions, resources and regulation alongside global practice."),
    ("What change in {sector} over the next few years do you think will affect {a_role} most?",
     "Curiosity about trends and reasoned, non-hyped thinking."),
    ("If you wanted to work in {focus} outside Kenya later, what would you need to add to your profile?",
     "Knowledge that qualifications and expectations differ between countries."),
    ("Which organisations in Kenya do you think do {focus} well, and what do you notice about how they work?",
     "Having looked at real employers and practices."),
    ("How might new technology change the day-to-day work of {a_role}?",
     "Balanced view of tools as help and risk, with an example."),
    ("What does a client, patient, learner or customer in Kenya expect from {a_role} that a textbook would not tell you?",
     "Understanding of people served and local context."),
    ("How do you keep up with what is happening in {sector}?",
     "Named, credible sources and a regular habit."),
]

ETHICS_FRAMES = [
    ("You are asked to do something that is outside what you are licensed or trained to do. What happens next?",
     "Refusing clearly, explaining why, and escalating to a supervisor."),
    ("A senior colleague asks you to sign off work you have not checked. How do you respond?",
     "Protecting standards and the public while staying respectful."),
    ("How would you handle discovering an error in work that has already gone out under your name?",
     "Prompt disclosure, correction and learning, not concealment."),
    ("What does professional confidentiality mean in the work of {a_role}, and where are its limits?",
     "Understanding of duty to clients or patients and of lawful exceptions."),
    ("Why does registration or licensing matter for {a_role}?",
     "Seeing regulation as public protection, not only paperwork."),
    ("A friend or relative asks you for a professional favour that bends the rules. What do you say?",
     "Managing conflict of interest and personal pressure."),
]

CURVEBALL_FRAMES = [
    ("What is something you believed about {focus} a year ago that you no longer believe?",
     "Evidence of growth and thinking for themselves."),
    ("If you could redesign one thing about how {sector} works in Kenya, what would it be?",
     "Original thinking grounded in a real problem."),
    ("What question were you hoping I would not ask you today?",
     "Honesty and composure when facing a weak area."),
    ("Teach me something in two minutes that has nothing to do with {focus}.",
     "Clear communication and personality beyond the CV."),
    ("What would your harshest lecturer or supervisor say about you, and would they be right?",
     "Self-awareness and ability to take criticism."),
    ("Tell me about a time you were bored at work or school. What did you do about it?",
     "Self-motivation and constructive use of slow periods."),
    ("If we hired you and it went badly, what would the most likely reason be?",
     "Insight into their own risks and how to manage them."),
    ("What have you read, watched or built recently that changed how you think?",
     "Curiosity and reflection."),
    ("Which rule do you think is most often broken in {focus}, and why?",
     "Practical knowledge of the field and judgment about standards."),
    ("What would you like to ask me about this role that is not on our website?",
     "Preparation and real interest in the work."),
]

# Scenarios written per sector: (question, what a strong answer shows).
SITUATIONAL = {
    "Technology and Data": [
        ("A release you worked on breaks a feature for users on a Friday evening. Nobody senior is online. What do you do?", "Containing the damage, communicating, and not guessing in production."),
        ("You are given a dataset or codebase with no documentation and a deadline of three days. How do you start?", "Exploring methodically and asking targeted questions."),
        ("A non-technical colleague insists on a feature you believe is a security risk. How do you handle it?", "Explaining risk in plain terms and proposing a safer option."),
        ("Your estimate for a task was two days and you are on day four. What do you tell the team?", "Honest status, cause, and a revised plan."),
        ("You find that a teammate's work contains copied code with an incompatible licence. What next?", "Raising it privately first and understanding why it matters."),
        ("Two people give you conflicting requirements for the same piece of work. What do you do?", "Bringing both together and getting one agreed decision."),
        ("The internet or power fails during a client demonstration. How do you recover?", "Preparation, composure and a backup plan."),
    ],
    "Engineering and Built Environment": [
        ("On site you notice work that does not match the approved drawing. The foreman says it is always done that way. What do you do?", "Stopping to verify, recording, and escalating through the right person."),
        ("Your calculation and a senior engineer's differ by a wide margin. How do you proceed?", "Rechecking assumptions and raising the difference respectfully."),
        ("Materials delivered are below specification and the project is behind schedule. What do you recommend?", "Putting safety and quality ahead of programme pressure."),
        ("A client wants to cut cost by removing something you consider necessary. How do you respond?", "Explaining consequences and offering alternatives."),
        ("You see a worker without protective equipment in a dangerous area. What do you do?", "Acting immediately on safety, then reporting."),
        ("Heavy rain has damaged part of the works overnight. Walk me through your first hour on site.", "Making safe, assessing, recording and informing."),
    ],
    "Health and Medicine": [
        ("A patient refuses a treatment you believe they need. How do you handle the conversation?", "Respect for autonomy, clear information and documentation."),
        ("You realise you may have recorded the wrong information in a patient's file. What do you do?", "Reporting immediately and correcting through the proper process."),
        ("The ward or clinic is short-staffed and three people need attention at once. How do you decide?", "Triage by urgency and asking for help."),
        ("A relative demands information about a patient who has not given consent. What do you say?", "Confidentiality handled with empathy."),
        ("You are asked to carry out a procedure you have only observed. How do you respond?", "Stating limits and requesting supervision."),
        ("A patient speaks a language you do not know well. How do you make sure they understand?", "Using interpreters and checking understanding rather than assuming."),
        ("Supplies you need have run out mid-shift. What do you do?", "Safe alternatives, escalation and reporting the gap."),
    ],
    "Banking and Finance": [
        ("The figures in your report do not reconcile an hour before it is due. What do you do?", "Finding the cause, flagging early, and never forcing a balance."),
        ("A customer asks you to bypass a verification step because they are in a hurry. How do you respond?", "Holding the control firmly while staying helpful."),
        ("You suspect a transaction is fraudulent but the client is important. What happens next?", "Following procedure and escalating regardless of status."),
        ("Your manager asks you to present numbers in a way you think is misleading. What do you do?", "Raising the concern and proposing an honest presentation."),
        ("A client wants an investment product that does not suit their situation. How do you advise them?", "Putting the client's interest and suitability first."),
        ("You discover an error you made in last month's accounts. Nobody has noticed. What now?", "Disclosure and correction."),
    ],
    "Business and Entrepreneurship": [
        ("A campaign or launch you planned gets almost no response in the first week. What do you do?", "Looking at data, testing changes and reporting honestly."),
        ("Your biggest customer threatens to leave over a problem that is partly their fault. How do you handle it?", "Listening, owning your part and solving rather than blaming."),
        ("You have budget for only one of two good ideas. How do you choose?", "A clear way of comparing cost, impact and risk."),
        ("A colleague takes credit for your idea in a meeting. What do you do?", "Addressing it calmly and directly."),
        ("You are asked to hit a sales target using claims you know are exaggerated. How do you respond?", "Refusing to mislead customers and offering an honest route."),
        ("Two departments blame each other for a failed project you are managing. What is your first move?", "Establishing facts and focusing on recovery."),
    ],
    "Law and Governance": [
        ("A client tells you something that would help their case but appears to be untrue. What do you do?", "Duty to the court and honesty with the client."),
        ("You find a precedent that goes against the position your supervisor wants to argue. What next?", "Disclosing it and working out how to address it."),
        ("A deadline for filing is today and a key document is missing. How do you proceed?", "Calm prioritising, informing the supervisor and exploring lawful options."),
        ("Someone offers you a gift to speed up a process. How do you respond?", "Refusal and reporting where required."),
        ("A member of the public who cannot afford a lawyer asks for your help. What can you do?", "Knowing the limits of your role and pointing to legal aid."),
        ("Two clients of your firm turn out to have opposing interests. What should happen?", "Recognising and escalating a conflict of interest."),
    ],
    "Education and Teaching": [
        ("Half the class has clearly not understood the lesson and the bell is about to ring. What do you do?", "Checking understanding and planning to reteach differently."),
        ("A learner who is usually lively becomes withdrawn for several days. How do you respond?", "Noticing, a gentle conversation, and following safeguarding steps."),
        ("A parent angrily disputes a grade you gave. How do you handle the meeting?", "Listening, showing evidence and staying professional."),
        ("You have sixty learners and textbooks for fifteen. How do you run the lesson?", "Creative use of group work and available resources."),
        ("Two learners are caught copying in an exam. What do you do?", "Following policy fairly and treating it as a teaching moment."),
        ("A colleague regularly arrives late and you have to cover their class. How do you deal with it?", "Speaking to them first, then using proper channels."),
    ],
    "Agriculture and Environment": [
        ("A farmer has followed your advice and the crop still failed. How do you handle the visit?", "Empathy, investigation and honesty about uncertainty."),
        ("You find a pest or disease you cannot identify in the field. What do you do?", "Sampling, recording, seeking expert identification and not guessing."),
        ("A community depends on an activity that is damaging the local environment. How do you approach them?", "Respect, listening and proposing workable alternatives."),
        ("Your field data contradicts what the funder expects to see. What do you report?", "Reporting what was found."),
        ("A supplier offers cheaper inputs that you suspect are counterfeit. What is your advice?", "Protecting the farmer and verifying sources."),
        ("Rains fail in the middle of a season you planned for. How do you adjust?", "Practical adaptation and clear communication with farmers."),
    ],
    "Media and Creative Industries": [
        ("A client rejects your work the day before the deadline without saying why. What do you do?", "Asking precise questions and managing the timeline."),
        ("You are given a story or brief that you find dull. How do you make it worth someone's attention?", "Craft, curiosity and respect for the audience."),
        ("A source gives you information you cannot verify, and a competitor is about to publish. What do you do?", "Accuracy before speed."),
        ("You are asked to use someone else's image or music without permission. How do you respond?", "Respect for copyright and proposing a legal alternative."),
        ("A post you made for a brand attracts angry comments. What is your first step?", "Pausing, assessing and responding with care."),
        ("Your creative direction and the client's taste are far apart. How do you find a way forward?", "Serving the brief while arguing for quality."),
    ],
    "Tourism and Hospitality": [
        ("A guest arrives and their booking cannot be found. The property is full. What do you do?", "Calm ownership, alternatives and follow-through."),
        ("A guest complains loudly in front of other guests. How do you handle it?", "Moving the conversation, listening and solving."),
        ("A tour is disrupted by weather or a vehicle breakdown far from town. What happens next?", "Safety first, communication and a backup plan."),
        ("You notice a food-safety problem in the kitchen during a busy service. What do you do?", "Stopping the risk even under pressure."),
        ("A guest asks for something that goes against company policy or local law. How do you respond?", "Polite refusal and offering what is allowed."),
        ("Two large groups arrive at the same time and you are short of staff. How do you manage?", "Prioritising, communicating waits and asking for help."),
    ],
    "Science and Research": [
        ("Your results do not match the hypothesis or a published study. What do you do?", "Checking method, then reporting honestly."),
        ("A sample may have been contaminated but repeating the work will take weeks. What do you decide?", "Integrity of data over convenience."),
        ("A senior researcher suggests leaving out data points that weaken the conclusion. How do you respond?", "Understanding of research ethics and how to raise concerns."),
        ("Key equipment fails halfway through an experiment. How do you proceed?", "Safe shutdown, recording and salvaging what is valid."),
        ("You are asked to explain your research to a group of secondary school students. How do you do it?", "Clear, accurate simplification."),
        ("You notice a safety rule being ignored in the laboratory by people senior to you. What do you do?", "Speaking up through the right route."),
    ],
    "Logistics and Operations": [
        ("A shipment is held at the port or border and the customer needs it tomorrow. What do you do?", "Finding the cause, communicating and working options."),
        ("Stock on the system does not match stock on the shelf. How do you investigate?", "Methodical checking and fixing the cause, not just the count."),
        ("A driver or operator reports feeling too tired to continue. The delivery is urgent. What do you decide?", "Putting safety ahead of the deadline."),
        ("A supplier you depend on suddenly raises prices sharply. How do you respond?", "Negotiation, alternatives and informing stakeholders."),
        ("You are offered a payment to favour one supplier in a tender. What do you do?", "Refusal and reporting."),
        ("Demand doubles for a week with no warning. How do you cope?", "Prioritising, temporary capacity and clear communication."),
    ],
    "Social and Community Services": [
        ("A client tells you something that suggests a child may be at risk, and asks you to keep it secret. What do you do?", "Explaining limits of confidentiality and following safeguarding procedure."),
        ("A community meeting you organised is taken over by one dominant voice. How do you respond?", "Facilitation that brings in quieter people."),
        ("You are emotionally affected by a case you are working on. How do you look after yourself and the client?", "Using supervision and maintaining boundaries."),
        ("Resources run out before everyone eligible has been helped. How do you decide who receives support?", "Fair, transparent criteria."),
        ("A beneficiary offers you a gift in thanks. What do you do?", "Understanding of boundaries and organisational policy."),
        ("Local leaders disagree with your organisation's approach. How do you proceed?", "Respectful engagement and willingness to adapt."),
    ],
    "Public Service and Development": [
        ("A member of the public has been sent from office to office and arrives at your desk angry. What do you do?", "Taking ownership and solving or guiding properly."),
        ("You are asked to prepare a policy brief by tomorrow on a topic you know little about. How do you approach it?", "Fast, credible research and stating limits."),
        ("A senior person asks you to process a request out of turn for someone they know. How do you respond?", "Fairness and following procedure."),
        ("Data you need from another department is not being shared. What do you do?", "Building relationships and using formal channels."),
        ("A project you are coordinating is underspending and the financial year is ending. What do you recommend?", "Value for money over spending for its own sake."),
        ("Two communities both claim priority for the same limited resource. How would you advise the decision-maker?", "Evidence, consultation and transparent reasoning."),
    ],
    "Energy, Manufacturing and Skilled Trades": [
        ("A customer wants the job done faster and asks you to skip a safety step. What do you say?", "Refusing the shortcut and explaining the risk."),
        ("You arrive on site and the fault is not what was described. How do you proceed?", "Diagnosing properly and agreeing new scope and cost before working."),
        ("A machine keeps failing after you repair it. What do you do differently the third time?", "Looking for the root cause."),
        ("You notice a colleague working on live equipment without isolating it. What do you do?", "Stopping the work immediately."),
        ("The correct part is not available and the customer needs the equipment today. What are your options?", "Safe temporary measures and honesty about limits."),
        ("A finished job fails inspection. How do you respond to the inspector and the customer?", "Accepting the finding, fixing it and learning."),
        ("Production is behind target and quality checks are slowing the line. What do you advise?", "Keeping quality while finding the real bottleneck."),
    ],
}

# Follow-up probes are worded so that any probe fits any question of its type.
FOLLOW_UPS = {
    "skill": ["Give me a specific example.", "Why that approach rather than another?",
              "How would you check that it had worked?", "What is the hardest part of that for you?",
              "What would you ask a senior colleague about that?"],
    "behavioural": ["What exactly did you do, as opposed to the team?", "What was the hardest moment in that?",
                    "What did you learn about yourself?", "Would you handle it the same way today?",
                    "What was the result, in concrete terms?"],
    "situational": ["And if that did not work?", "Who would you tell, and when?",
                    "What would you write down afterwards?", "What is the risk in the approach you chose?",
                    "How would you explain your decision to your supervisor the next morning?"],
    "motivation": ["Why does that matter to you?", "Can you give me an example from your own experience?",
                   "What makes you say that?", "How does that connect to this particular role?"],
    "opportunity": ["How would we be able to tell that it had gone well?", "What would that look like in week one?",
                    "What help would you need from your supervisor?"],
    "market": ["Can you give me an example you have seen?", "Where did you learn that?",
               "How would that affect your first year of work?"],
    "ethics": ["What could go wrong if that were handled badly?", "Who would you turn to for guidance?",
               "Where would you look to confirm the rule?"],
    "curveball": ["Why that one?", "Tell me more about that.", "What does that say about how you work?"],
}

DIFFICULTY = {
    "behavioural": "entry", "motivation": "entry", "opportunity": "entry",
    "skill": "intermediate", "situational": "intermediate", "market": "intermediate",
    "ethics": "stretch", "curveball": "stretch",
}

COLUMNS = [
    "question_id", "career_id", "role_title", "question_type", "difficulty", "opportunity_type",
    "skill_assessed", "question", "strong_answer_shows", "follow_up_probe", "data_origin", "is_synthetic",
]


def _rank(key: str) -> int:
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)


def _pick(pool: list, key: str, count: int) -> list:
    """Choose `count` items from `pool` in a stable order that differs per key."""
    ordered = sorted(range(len(pool)), key=lambda index: _rank(f"{key}:{index}"))
    return [pool[index] for index in ordered[:count]]


def _article(text: str) -> str:
    return ("an " if text[:1].lower() in "aeiou" else "a ") + text


def build_questions() -> list[dict]:
    catalog, skills = build_rows()
    core: dict[str, list[str]] = {}
    for row in skills:
        if row["skill_type"] == "core":
            core.setdefault(row["career_id"], []).append(row["skill"])
    rows: list[dict] = []
    for role in catalog:
        career_id, title = role["career_id"], role["role_title"]
        fill = {
            "role": title, "a_role": _article(title), "focus": role["specialisation"],
            "sector": CATEGORIES[role["category"]][0],
        }
        selected: list[tuple[str, str, str, tuple[str, str]]] = []  # type, opportunity, skill, frame
        for skill in core[career_id]:
            for frame in _pick(SKILL_FRAMES, f"{career_id}:skill:{skill}", 2):
                selected.append(("skill", "any", skill, frame))
        for frame in _pick(BEHAVIOURAL_FRAMES, f"{career_id}:behavioural", 5):
            selected.append(("behavioural", "any", "", frame))
        for frame in _pick(SITUATIONAL[role["category"]], f"{career_id}:situational", 4):
            selected.append(("situational", "any", "", frame))
        for frame in _pick(MOTIVATION_FRAMES, f"{career_id}:motivation", 3):
            selected.append(("motivation", "any", "", frame))
        for opportunity, frames in OPPORTUNITY_FRAMES.items():
            selected.append(("opportunity", opportunity, "", _pick(frames, f"{career_id}:{opportunity}", 1)[0]))
        for frame in _pick(MARKET_FRAMES, f"{career_id}:market", 2):
            selected.append(("market", "any", "", frame))
        if role["commonly_regulated"] == "yes":
            for frame in _pick(ETHICS_FRAMES, f"{career_id}:ethics", 3):
                selected.append(("ethics", "any", "", frame))
        for frame in _pick(CURVEBALL_FRAMES, f"{career_id}:curveball", 3):
            selected.append(("curveball", "any", "", frame))

        seen: set[str] = set()
        number = 0
        for question_type, opportunity, skill, (question, strong) in selected:
            text = question.format(skill=skill, **fill)
            if text in seen:  # the same frame can be drawn for two skills only with different text
                continue
            seen.add(text)
            number += 1
            probes = FOLLOW_UPS[question_type]
            rows.append({
                "question_id": f"IQ-{career_id.split('-')[1]}-{number:02d}",
                "career_id": career_id, "role_title": title, "question_type": question_type,
                "difficulty": DIFFICULTY[question_type], "opportunity_type": opportunity,
                "skill_assessed": skill, "question": text, "strong_answer_shows": strong,
                "follow_up_probe": probes[_rank(f"{career_id}:{number}") % len(probes)],
                "data_origin": DATA_ORIGIN, "is_synthetic": "true",
            })
    return rows


def pick_interview_set(rows: list[dict], career_id: str, count: int = 8,
                       seed: int | None = None, opportunity_type: str | None = None) -> list[dict]:
    """Return a mixed practice set for one session.

    Starts with a motivation question, alternates question styles so no two
    neighbours are the same type where possible, and ends with a curveball.
    A different seed gives a different set and order.
    """
    pool = [row for row in rows if row["career_id"] == career_id
            and row["opportunity_type"] in ("any", opportunity_type or "any")]
    if not pool:
        raise ValueError(f"No questions for career_id {career_id}")
    rng = random.Random(seed)
    by_type: dict[str, list[dict]] = {}
    for row in pool:
        by_type.setdefault(row["question_type"], []).append(row)
    for items in by_type.values():
        rng.shuffle(items)
    opener = by_type.get("motivation", [None])[0]
    closer = by_type.get("curveball", [None])[0]
    middle_types = [name for name in by_type if name not in ("motivation", "curveball")]
    rng.shuffle(middle_types)
    middle: list[dict] = []
    used = {id(opener), id(closer)}
    target = max(count - (opener is not None) - (closer is not None), 0)
    while len(middle) < target and any(by_type[name] for name in middle_types):
        for name in middle_types:
            if len(middle) >= target:
                break
            while by_type[name]:
                candidate = by_type[name].pop()
                if id(candidate) not in used:
                    used.add(id(candidate))
                    middle.append(candidate)
                    break
    return [item for item in ([opener] + middle + [closer]) if item is not None][:count]


def validate(rows: list[dict]) -> dict:
    missing = set(CATEGORIES) - set(SITUATIONAL)
    if missing:
        raise ValueError(f"Categories without situational scenarios: {sorted(missing)}")
    ids = [row["question_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate question_id values")
    for row in rows:
        if "{" in row["question"] or "}" in row["question"]:
            raise ValueError(f"Unfilled placeholder in {row['question_id']}")
    per_career = Counter(row["career_id"] for row in rows)
    return {
        "questions": len(rows),
        "careers": len(per_career),
        "min_per_career": min(per_career.values()),
        "max_per_career": max(per_career.values()),
        "distinct_question_texts": len({row["question"] for row in rows}),
        "by_type": dict(Counter(row["question_type"] for row in rows)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true", help="Validate the question bank without writing files.")
    parser.add_argument("--demo", metavar="CAREER_ID", help="Print two different practice sets for one career.")
    args = parser.parse_args()

    rows = build_questions()
    summary = validate(rows)
    if args.demo:
        for seed in (1, 2):
            print(f"\n--- Practice session with seed {seed} ---")
            for index, item in enumerate(pick_interview_set(rows, args.demo, count=6, seed=seed), start=1):
                print(f"{index}. [{item['question_type']}] {item['question']}")
                print(f"   Follow-up: {item['follow_up_probe']}")
        return
    if args.check:
        print(json.dumps(summary, indent=2))
        print("Validation passed; no files written.")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "interview_questions.csv", COLUMNS, rows)
    print(f"Wrote {len(rows)} interview questions for {summary['careers']} careers to {args.output_dir}")


if __name__ == "__main__":
    main()
