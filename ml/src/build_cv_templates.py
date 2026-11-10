"""Generate a CV template for every catalogue role and fill one from a student's details.

Writes ml/data/careers/cv_templates.jsonl (one JSON object per career_id). Each
template holds the section order that suits the field, the skills worth showing,
bullet-point starters, and CV tips. `render_cv` turns a template plus the details
a student supplies into a Markdown CV.

The renderer only uses what the student provides. It never invents experience,
grades, licences or employers. Where the student has nothing for a section it
leaves a bracketed prompt telling them what to add.

Templates are synthetic guidance, not an employer's or regulator's required format.

Usage (from the repository root):
  python ml/src/build_cv_templates.py
  python ml/src/build_cv_templates.py --check
  python ml/src/build_cv_templates.py --demo CAREER-002
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from build_career_catalogue import CATEGORIES, DATA_ORIGIN, DEFAULT_OUTPUT_DIR, build_rows  # noqa: E402

# Section ids understood by render_cv: summary, skills, projects, education,
# experience, certifications, extras, referees.
LAYOUTS = {
    "technical": [
        ("summary", "Professional Summary"), ("skills", "Technical Skills"), ("projects", "Projects"),
        ("education", "Education"), ("experience", "Work Experience and Attachments"),
        ("certifications", "Certifications"), ("referees", "Referees"),
    ],
    "engineering": [
        ("summary", "Professional Summary"), ("education", "Education"),
        ("projects", "Projects and Site Experience"), ("experience", "Work Experience and Attachments"),
        ("skills", "Technical Skills"), ("certifications", "Registration and Certifications"),
        ("referees", "Referees"),
    ],
    "clinical": [
        ("summary", "Professional Summary"), ("education", "Education and Licences"),
        ("experience", "Clinical Placements and Experience"), ("skills", "Key Skills"),
        ("certifications", "Certifications and Training"), ("extras", "Research and Community Service"),
        ("referees", "Referees"),
    ],
    "professional": [
        ("summary", "Professional Summary"), ("education", "Education"),
        ("experience", "Work Experience and Attachments"), ("skills", "Key Skills"),
        ("extras", "Leadership and Activities"), ("certifications", "Professional Qualifications"),
        ("referees", "Referees"),
    ],
    "creative": [
        ("summary", "Profile"), ("projects", "Portfolio and Selected Work"), ("skills", "Skills and Tools"),
        ("experience", "Experience"), ("education", "Education"), ("extras", "Awards and Exhibitions"),
        ("referees", "Referees"),
    ],
    "academic": [
        ("summary", "Professional Summary"), ("education", "Education"),
        ("experience", "Research and Teaching Experience"), ("skills", "Key Skills"),
        ("projects", "Research Projects"), ("certifications", "Certifications and Training"),
        ("referees", "Referees"),
    ],
    "service": [
        ("summary", "Professional Summary"), ("experience", "Work Experience and Attachments"),
        ("skills", "Key Skills"), ("education", "Education"), ("certifications", "Certificates"),
        ("extras", "Languages and Interests"), ("referees", "Referees"),
    ],
    "trade": [
        ("summary", "Professional Summary"), ("skills", "Trade Skills"),
        ("experience", "Work Experience and Attachments"), ("certifications", "Trade Tests and Certificates"),
        ("projects", "Jobs and Projects Completed"), ("education", "Education"), ("referees", "Referees"),
    ],
}

CATEGORY_LAYOUT = {
    "Technology and Data": "technical",
    "Engineering and Built Environment": "engineering",
    "Health and Medicine": "clinical",
    "Banking and Finance": "professional",
    "Business and Entrepreneurship": "professional",
    "Law and Governance": "professional",
    "Education and Teaching": "academic",
    "Agriculture and Environment": "professional",
    "Media and Creative Industries": "creative",
    "Tourism and Hospitality": "service",
    "Science and Research": "academic",
    "Logistics and Operations": "professional",
    "Social and Community Services": "professional",
    "Public Service and Development": "professional",
    "Energy, Manufacturing and Skilled Trades": "trade",
}

# layout -> (bullet starters, CV tips). {focus} and {skill} are filled per role.
LAYOUT_GUIDANCE = {
    "technical": (
        ["Built [what you built] using {skill}, which [result or number of users].",
         "Fixed or improved [system or feature] in {focus}, reducing [time, errors or cost] by [amount].",
         "Worked with [team size] people to deliver [project], taking the lead on [your part]."],
        ["Link a GitHub profile or live project.", "Name the tools and languages you actually used.",
         "Put projects above education if they are stronger than your grades."],
    ),
    "engineering": (
        ["Assisted on [project or site] during attachment, carrying out [task] under supervision.",
         "Produced [drawing, calculation or model] using {skill} for [purpose].",
         "Inspected or tested [component or works] and recorded results in [report or logbook]."],
        ["State attachment sites, dates and supervising engineer where allowed.",
         "List software and standards you have used.",
         "Mention graduate registration status only if you hold it."],
    ),
    "clinical": (
        ["Completed [number] weeks of supervised placement in [department] at [facility].",
         "Supported [procedure or care activity] under supervision, following [protocol].",
         "Delivered health education on [topic] to [audience] during [outreach or placement]."],
        ["List placements with facility, department and dates.",
         "State licences and registration numbers only if they are current and yours.",
         "Never describe supervised work as independent practice."],
    ),
    "professional": (
        ["Prepared [report, analysis or document] on [subject] used by [who] to [decision or result].",
         "Handled [task or volume] during [attachment or role] in {focus}, meeting [deadline or standard].",
         "Organised or led [club, event or team] of [size], achieving [result]."],
        ["Lead with results and numbers where you have them.",
         "Show professional exams passed and the stage you have reached.",
         "Keep it to one or two pages."],
    ),
    "creative": (
        ["Created [piece or campaign] for [client, class or audience], reaching [views, sales or response].",
         "Produced [type of work] using {skill}, from brief to final delivery.",
         "Collaborated with [who] on [production], responsible for [your role]."],
        ["Put the portfolio link at the top.", "Show three to five of your best pieces, not everything.",
         "Credit collaborators and state your exact role."],
    ),
    "academic": (
        ["Carried out [experiment, study or lesson series] on [topic] using {skill}.",
         "Collected and analysed [data] for [project], presenting findings to [audience].",
         "Taught or tutored [subject] to [group], improving [measure] by [amount]."],
        ["Give your project or dissertation title.", "List methods and instruments you can use unaided.",
         "Include teaching practice schools and dates for teaching roles."],
    ),
    "service": (
        ["Served [number] guests or customers per shift at [place], keeping [standard or rating].",
         "Resolved [type of request or complaint] by [action], leading to [result].",
         "Supported [event or operation] of [size], responsible for [your part]."],
        ["Show customer-facing experience first.", "List languages you speak and at what level.",
         "Include food-safety or first-aid certificates if you hold them."],
    ),
    "trade": (
        ["Installed, repaired or built [what] at [site or workshop], completing it in [time].",
         "Diagnosed [fault] using {skill} and fixed it by [action].",
         "Worked safely on [type of job] following [safety procedure], with no incidents."],
        ["List trade test grades and the dates you passed them.",
         "Name the tools, machines and equipment you can operate.",
         "Add photos or references for completed jobs where you can."],
    ),
}

REGULATED_NOTE = (
    "This is commonly a regulated role. Only list a licence, registration number or 'registered' "
    "title if you currently hold it; otherwise state the stage you have reached."
)
OPPORTUNITY_LABELS = {
    "internship": "an internship",
    "industrial attachment": "an industrial attachment",
    "graduate programme": "a graduate programme place",
    "full-time job": "a full-time role",
}


def build_templates() -> list[dict]:
    catalog, skills = build_rows()
    skills_by_career: dict[str, dict[str, list[str]]] = {}
    for row in skills:
        skills_by_career.setdefault(row["career_id"], {}).setdefault(row["skill_type"], []).append(row["skill"])
    templates = []
    for role in catalog:
        layout = CATEGORY_LAYOUT[role["category"]]
        role_skills = skills_by_career[role["career_id"]]
        core = role_skills.get("core", [])
        starters, tips = LAYOUT_GUIDANCE[layout]
        templates.append({
            "career_id": role["career_id"],
            "role_title": role["role_title"],
            "category": role["category"],
            "specialisation": role["specialisation"],
            "layout": layout,
            "sections": [{"id": section_id, "heading": heading} for section_id, heading in LAYOUTS[layout]],
            "headline_template": f"{{course}} student | Aspiring {role['role_title']}",
            "skills_to_highlight": core + role_skills.get("preferred", []),
            "transferable_skills": role_skills.get("transferable", []),
            "bullet_starters": [
                text.format(focus=role["specialisation"], skill=core[index % len(core)])
                for index, text in enumerate(starters)
            ],
            "cv_tips": tips,
            "regulated_note": REGULATED_NOTE if role["commonly_regulated"] == "yes" else "",
            "data_origin": DATA_ORIGIN,
            "is_synthetic": True,
        })
    return templates


def _clean_list(value) -> list[str]:
    if isinstance(value, str):
        value = value.replace(";", ",").split(",")
    return [str(item).strip() for item in (value or []) if str(item).strip()]


def render_cv(template: dict, profile: dict) -> dict:
    """Fill a template from a student's details and return Markdown plus skill notes.

    profile keys (all optional except full_name): full_name, email, phone, location,
    links, course, institution, graduation_year, target_opportunity, skills,
    projects [{title, description}], experience [{title, organisation, period,
    highlights}], certifications, activities, referees.
    """
    # Callers may send null for anything the student left blank.
    profile = {key: ("" if value is None else value) for key, value in profile.items()}
    name = str(profile.get("full_name", "")).strip()
    if not name:
        raise ValueError("full_name is required to build a CV")
    role, focus = template["role_title"], template["specialisation"]
    student_skills = _clean_list(profile.get("skills"))
    wanted = template["skills_to_highlight"] + template["transferable_skills"]
    wanted_keys = {skill.casefold() for skill in wanted}
    student_keys = {skill.casefold() for skill in student_skills}
    matched = [skill for skill in student_skills if skill.casefold() in wanted_keys]
    other = [skill for skill in student_skills if skill.casefold() not in wanted_keys]
    to_build = [skill for skill in template["skills_to_highlight"] if skill.casefold() not in student_keys]

    course = str(profile.get("course", "")).strip()
    institution = str(profile.get("institution", "")).strip()
    year = str(profile.get("graduation_year", "")).strip()
    opportunity = OPPORTUNITY_LABELS.get(str(profile.get("target_opportunity", "")).strip().lower(), "an opportunity")

    contact = [str(profile.get(key, "")).strip() for key in ("email", "phone", "location")]
    contact += _clean_list(profile.get("links"))
    lines = [f"# {name}", ""]
    if course:
        lines += [f"**{template['headline_template'].format(course=course)}**", ""]
    if any(contact):
        lines += [" | ".join(item for item in contact if item), ""]

    def summary() -> list[str]:
        study = f"{course} student" if course else "Student"
        if institution:
            study += f" at {institution}"
        if year:
            study += f" (graduating {year})"
        text = f"{study} seeking {opportunity} in {focus} as a {role}."
        shown = (matched or student_skills)[:4]
        if shown:
            text += f" Brings {', '.join(shown)}."
        text += " [Add one sentence on your strongest result or project.]"
        return [text]

    def skills() -> list[str]:
        if not student_skills:
            return [f"[List skills you can show evidence for. Relevant ones for this role: {', '.join(template['skills_to_highlight'][:5])}.]"]
        out = []
        if matched:
            out.append(f"- **Relevant to {role}:** {', '.join(matched)}")
        if other:
            out.append(f"- **Other skills:** {', '.join(other)}")
        return out

    def projects() -> list[str]:
        out = []
        for item in profile.get("projects") or []:
            title = str(item.get("title", "")).strip()
            if title:
                out.append(f"- **{title}:** {str(item.get('description', '')).strip() or '[Describe what you did and the result.]'}")
        return out or [f"- Example to adapt: {template['bullet_starters'][0]}"]

    def education() -> list[str]:
        if not (course or institution):
            return ["- [Course, institution, graduation year, and grade or class if strong.]"]
        entry = " | ".join(part for part in (course, institution, f"Expected {year}" if year else "") if part)
        return [f"- {entry}", "- [Add relevant units, your final-year project title, or awards.]"]

    def experience() -> list[str]:
        out = []
        for item in profile.get("experience") or []:
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            heading = " | ".join(part for part in (title, str(item.get("organisation", "")).strip(),
                                                   str(item.get("period", "")).strip()) if part)
            out.append(f"**{heading}**")
            highlights = _clean_list(item.get("highlights"))
            out += [f"- {point}" for point in highlights] or [f"- Example to adapt: {template['bullet_starters'][1]}"]
            out.append("")
        if out:
            return out[:-1]
        return [f"- Example to adapt: {starter}" for starter in template["bullet_starters"][1:]]

    def certifications() -> list[str]:
        items = _clean_list(profile.get("certifications"))
        return [f"- {item}" for item in items] or ["- [List certificates or professional exams you have passed, with dates.]"]

    def extras() -> list[str]:
        items = _clean_list(profile.get("activities"))
        return [f"- {item}" for item in items] or ["- [Clubs, volunteering, leadership roles, languages or awards.]"]

    def referees() -> list[str]:
        items = _clean_list(profile.get("referees"))
        return [f"- {item}" for item in items] or ["Available on request."]

    builders = {"summary": summary, "skills": skills, "projects": projects, "education": education,
                "experience": experience, "certifications": certifications, "extras": extras,
                "referees": referees}
    for section in template["sections"]:
        lines += [f"## {section['heading']}", "", *builders[section["id"]](), ""]
    if template["regulated_note"]:
        lines += [f"> Note: {template['regulated_note']}", ""]
    return {
        "career_id": template["career_id"],
        "role_title": role,
        "markdown": "\n".join(lines).rstrip() + "\n",
        "matched_skills": matched,
        "skills_to_build": to_build,
        "cv_tips": template["cv_tips"],
    }


ATS_HEADINGS = {
    "summary": "Professional Summary", "skills": "Skills", "projects": "Projects", "education": "Education",
    "experience": "Work Experience", "certifications": "Certifications",
    "extras": "Leadership and Activities", "referees": "Referees",
}


def render_final_cv(template: dict, profile: dict) -> dict:
    """Build a CV that is ready to send, laid out for applicant tracking systems (ATS).

    ATS-friendly here means: one column, standard section headings, plain text and
    simple bullets, no tables, images or text boxes, and skills written as words a
    recruiter would search for. The section order still follows the career's template.

    Unlike render_cv, nothing is invented and no prompts are left in the document:
    a section with no details is left out, and `checklist` tells the student what is
    still worth adding before they send it. Extra profile keys: summary, grade.
    """
    profile = {key: ("" if value is None else value) for key, value in profile.items()}
    name = str(profile.get("full_name", "")).strip()
    if not name:
        raise ValueError("full_name is required to build a CV")
    role, focus = template["role_title"], template["specialisation"]
    student_skills = _clean_list(profile.get("skills"))
    wanted_keys = {skill.casefold() for skill in template["skills_to_highlight"] + template["transferable_skills"]}
    student_keys = {skill.casefold() for skill in student_skills}
    matched = [skill for skill in student_skills if skill.casefold() in wanted_keys]
    other = [skill for skill in student_skills if skill.casefold() not in wanted_keys]
    to_build = [skill for skill in template["skills_to_highlight"] if skill.casefold() not in student_keys]

    def text(key: str) -> str:
        return " ".join(str(profile.get(key, "")).split())

    course, institution, year, grade = text("course"), text("institution"), text("graduation_year"), text("grade")
    own_summary = text("summary")
    opportunity = OPPORTUNITY_LABELS.get(text("target_opportunity").lower(), "")
    contact = [text("email"), text("phone"), text("location"), *_clean_list(profile.get("links"))]
    experience_items = [item for item in (profile.get("experience") or []) if str(item.get("title", "")).strip()]
    project_items = [item for item in (profile.get("projects") or []) if str(item.get("title", "")).strip()]

    def summary() -> list[str]:
        if own_summary:
            return [own_summary]
        if not (course or institution):
            return []
        sentence = f"{course} student" if course else "Student"
        if institution:
            sentence += f" at {institution}"
        if year:
            sentence += f", graduating in {year}"
        sentence += f", seeking {opportunity} in {focus}." if opportunity else f", with an interest in {focus}."
        shown = (matched or student_skills)[:5]
        if shown:
            sentence += f" Skills include {', '.join(shown)}."
        return [sentence]

    def skills() -> list[str]:
        return [", ".join(matched + other)] if student_skills else []

    def education() -> list[str]:
        if not (course or institution):
            return []
        entry = f"**{course or 'Studies'}**" + (f", {institution}" if institution else "")
        details = " | ".join(part for part in (f"Expected {year}" if year else "", grade) if part)
        return [entry + (f" | {details}" if details else "")]

    def experience() -> list[str]:
        out: list[str] = []
        for item in experience_items:
            heading = f"**{' '.join(str(item['title']).split())}**"
            organisation = " ".join(str(item.get("organisation", "")).split())
            period = " ".join(str(item.get("period", "")).split())
            heading += (f", {organisation}" if organisation else "") + (f" | {period}" if period else "")
            out.append(heading)
            out += [f"- {point}" for point in _clean_list(item.get("highlights"))]
            out.append("")
        return out[:-1]

    def projects() -> list[str]:
        out: list[str] = []
        for item in project_items:
            out.append(f"**{' '.join(str(item['title']).split())}**")
            description = " ".join(str(item.get("description", "")).split())
            if description:
                out.append(f"- {description}")
            out.append("")
        return out[:-1]

    def bullets(key: str) -> list[str]:
        return [f"- {item}" for item in _clean_list(profile.get(key))]

    builders = {
        "summary": summary, "skills": skills, "projects": projects, "education": education,
        "experience": experience, "certifications": lambda: bullets("certifications"),
        "extras": lambda: bullets("activities"),
        "referees": lambda: bullets("referees") or ["Available on request."],
    }
    lines = [f"# {name}", ""]
    if any(contact):
        lines += [" | ".join(item for item in contact if item), ""]
    # Follow the career's section order, then add any section it leaves out so that
    # nothing the student entered is dropped. Referees always come last.
    order = [section["id"] for section in template["sections"]]
    order += [section_id for section_id in ATS_HEADINGS if section_id not in order]
    order = [section_id for section_id in order if section_id != "referees"] + ["referees"]
    for section_id in order:
        content = builders[section_id]()
        if content:
            lines += [f"## {ATS_HEADINGS[section_id]}", "", *content, ""]

    checklist = []
    if not (text("email") or text("phone")):
        checklist.append("Add a phone number or email address so employers can reach you.")
    if not own_summary:
        checklist.append("Write a two or three sentence professional summary in your own words.")
    if not (course or institution):
        checklist.append("Add your course and institution.")
    if not student_skills:
        checklist.append("Add your skills. For this role, employers often look for: "
                         + ", ".join(template["skills_to_highlight"][:5]) + ".")
    if not experience_items and not project_items:
        checklist.append("Add at least one project, attachment or work experience entry.")
    elif any(not _clean_list(item.get("highlights")) for item in experience_items):
        checklist.append("For each role, add what you did and achieved, with numbers where you can.")
    if template["regulated_note"]:
        checklist.append(template["regulated_note"])
    return {
        "career_id": template["career_id"], "role_title": role,
        "markdown": "\n".join(lines).rstrip() + "\n",
        "matched_skills": matched, "skills_to_build": to_build,
        "cv_tips": template["cv_tips"], "checklist": checklist,
    }


DEMO_PROFILE = {
    "full_name": "Demo Student",
    "email": "demo.student@example.com",
    "location": "Nairobi, Kenya",
    "course": "BSc Informatics and Computer Science",
    "institution": "Example University",
    "graduation_year": "2027",
    "target_opportunity": "internship",
    "skills": ["Kotlin", "Android", "SQL", "teamwork"],
    "projects": [{"title": "Campus Events App", "description": "Android app listing student events, built in Kotlin."}],
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true", help="Validate templates without writing files.")
    parser.add_argument("--demo", metavar="CAREER_ID", help="Print a sample CV for a made-up student and exit.")
    args = parser.parse_args()

    missing = set(CATEGORIES) - set(CATEGORY_LAYOUT)
    if missing:
        raise ValueError(f"Categories without a CV layout: {sorted(missing)}")
    templates = build_templates()
    for template in templates:
        render_cv(template, {"full_name": "Check"})  # every template must render with minimal input

    if args.demo:
        chosen = next((item for item in templates if item["career_id"] == args.demo), None)
        if chosen is None:
            raise SystemExit(f"Unknown career_id: {args.demo}")
        print(render_cv(chosen, DEMO_PROFILE)["markdown"])
        return
    if args.check:
        print(f"{len(templates)} CV templates validated; no files written.")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "cv_templates.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for template in templates:
            handle.write(json.dumps(template, ensure_ascii=False) + "\n")
    print(f"Wrote {len(templates)} CV templates to {path}")


if __name__ == "__main__":
    main()
