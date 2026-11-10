"""Generate the detail tables that widen every career: titles, destinations, tasks, tools and neighbours.

Writes to ml/data/careers/:

  career_titles.csv         every job title connected to a role, by type:
                            alternative, specialism, entry, progression,
                            leadership, beyond (where the path can lead) and lateral
  career_tasks.csv          day-to-day tasks
  career_tools.csv          tools and technologies
  career_related.csv        up to ten neighbouring careers with the skills they share
  career_work_settings.csv  kinds of employer and working patterns
  career_details_manifest.json  counts, and how many roles have hand-written detail

Where detail comes from:
  - `authored`          written for that role in career_role_details.py
  - `category_default`  the role's category defaults in this file, used until the
                        role has authored detail
  - `derived`           built from the role title, its focus area or the
                        catalogue's own skills (entry, progression and related rows)

All rows are synthetic and illustrative. Titles differ between employers and
countries, and a listed destination is a possibility to explore, not a promised
route.

Usage (from the repository root):
  python ml/src/build_career_details.py
  python ml/src/build_career_details.py --check
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from build_career_catalogue import CATEGORIES, DATA_ORIGIN, DEFAULT_OUTPUT_DIR, build_rows, write_csv  # noqa: E402
from career_role_details import ROLE_DETAILS  # noqa: E402

RELATED_PER_CAREER = 10

DEFAULT_ENTRY = [
    "Attachment student ({focus})", "{title} intern", "Graduate trainee ({focus})",
    "Trainee {title}", "Junior {title}", "Assistant {title}", "Associate {title}",
]
DEFAULT_SENIOR = ["Senior {title}", "Lead {title}", "Principal {title}"]

# Per category: entry and senior title patterns (None = defaults), leadership destinations,
# where the path can lead beyond the role, default tasks, default tools, employers, working patterns.
CATEGORY_DETAILS = {
    "Technology and Data": {
        "entry": None, "senior": ["Senior {title}", "Lead {title}", "Staff {title}", "Principal {title}"],
        "leadership": ["Team Lead", "Engineering Manager", "Head of Engineering", "Director of Technology", "Chief Technology Officer", "Chief Information Officer"],
        "beyond": ["Technical Consultant", "Freelance or contract specialist", "Start-up founder", "Technical trainer or lecturer", "Developer advocate", "Product Manager"],
        "tasks": ["plan and deliver {focus} work with a team", "solve technical problems as they arise", "test and review work before release", "document what was built and why", "keep systems secure and reliable", "learn new tools as the field changes"],
        "tools": ["Git", "an issue tracker", "cloud platforms", "Linux command line", "collaboration tools"],
        "settings": ["technology company", "start-up", "bank or insurer technology team", "telecommunications company", "software consultancy or agency", "government ICT department", "non-governmental organisation", "remote team for an international employer"],
        "patterns": ["office, hybrid or fully remote", "project deadlines and release cycles", "on-call rotations in operations roles"],
    },
    "Engineering and Built Environment": {
        "entry": ["Attachment student ({focus})", "{title} intern", "Graduate {title}", "Graduate trainee ({focus})", "Assistant {title}", "Junior {title}", "Site assistant"],
        "senior": ["Senior {title}", "Principal {title}", "Chief {title}", "Registered professional in {focus}"],
        "leadership": ["Project Manager", "Resident Engineer", "Technical Director", "Head of Department", "Managing Partner of a consultancy", "County or national chief officer"],
        "beyond": ["Independent consultant", "Own consulting practice", "Contractor or developer", "Lecturer or researcher", "Regulator or standards officer", "Expert witness or arbitrator"],
        "tasks": ["prepare designs, drawings and specifications for {focus}", "visit sites to inspect work and safety", "check work against codes and standards", "coordinate with clients, contractors and other professionals", "estimate cost and time", "write technical reports"],
        "tools": ["AutoCAD", "spreadsheets", "project scheduling software", "surveying and measuring instruments", "design codes and standards"],
        "settings": ["engineering consultancy", "construction contractor", "county or national government works department", "utility or infrastructure agency", "manufacturer or industrial plant", "property developer", "international development project", "own practice"],
        "patterns": ["a mix of office design work and site visits", "project-based deadlines", "travel to sites, sometimes remote"],
    },
    "Health and Medicine": {
        "entry": ["Student on clinical placement ({focus})", "Intern {title}", "Newly registered {title}", "Locum {title}", "Assistant in {focus}", "Volunteer in {focus}"],
        "senior": ["Senior {title}", "Specialist {title}", "Consultant in {focus}", "In-charge of {focus}"],
        "leadership": ["Unit or ward in-charge", "Head of Department", "Hospital Administrator", "County Director of Health", "Medical Superintendent", "Programme Director"],
        "beyond": ["Private practice", "Public health programme officer", "Clinical researcher", "Lecturer or clinical instructor", "Health consultant for a non-governmental organisation", "Regulator or policy adviser"],
        "tasks": ["assess patients or clients in {focus}", "plan and deliver care or services", "keep accurate clinical records", "explain findings and next steps clearly", "follow infection prevention and safety procedures", "refer to colleagues when needed"],
        "tools": ["clinical records systems", "diagnostic equipment", "treatment guidelines and protocols", "personal protective equipment", "health information reporting tools"],
        "settings": ["public hospital", "county health centre or dispensary", "private hospital or clinic", "faith-based hospital", "health-focused non-governmental organisation", "research institute", "community outreach programme", "international health agency"],
        "patterns": ["shifts including nights and weekends in clinical roles", "on-call duties", "outreach and field visits in community roles"],
    },
    "Banking and Finance": {
        "entry": ["{title} intern", "Graduate trainee ({focus})", "Management trainee", "Trainee {title}", "Junior {title}", "Assistant {title}", "Associate {title}"],
        "senior": ["Senior {title}", "{title} Supervisor", "Manager, {focus}", "Head of {focus}"],
        "leadership": ["Branch Manager", "Finance Manager", "Head of Department", "Chief Finance Officer", "Chief Risk Officer", "Chief Executive Officer"],
        "beyond": ["Independent practice or advisory firm", "Consultant", "Fintech founder", "Lecturer or professional trainer", "Regulator or supervisory role", "Board or audit committee member"],
        "tasks": ["prepare and check figures for {focus}", "analyse financial information and explain what it means", "follow regulations and internal controls", "serve and advise clients or colleagues", "prepare reports on time", "keep accurate records"],
        "tools": ["Excel", "accounting or core banking systems", "financial reporting standards", "data analysis tools", "regulatory guidelines"],
        "settings": ["commercial bank", "audit or accounting firm", "insurance company", "SACCO or microfinance institution", "fintech company", "investment or asset management firm", "finance department of any organisation", "public finance office"],
        "patterns": ["office-based with client meetings", "busy month-end and year-end periods", "professional examinations alongside work"],
    },
    "Business and Entrepreneurship": {
        "entry": ["{title} intern", "Graduate trainee ({focus})", "Management trainee", "Trainee {title}", "Junior {title}", "Assistant {title}", "Coordinator, {focus}"],
        "senior": ["Senior {title}", "{title} Team Leader", "Manager, {focus}", "Head of {focus}"],
        "leadership": ["Department Manager", "Regional Manager", "General Manager", "Commercial Director", "Chief Operating Officer", "Chief Executive Officer"],
        "beyond": ["Business owner", "Independent consultant", "Agency founder", "Lecturer or corporate trainer", "Non-executive director", "Investor or mentor"],
        "tasks": ["plan and run {focus} activities", "understand what customers or colleagues need", "track results against targets", "work with other teams to get things done", "prepare reports and presentations", "manage budgets and suppliers"],
        "tools": ["spreadsheets and presentations", "customer relationship management systems", "analytics dashboards", "collaboration tools", "social media and email platforms"],
        "settings": ["consumer goods or retail company", "marketing or communications agency", "start-up or small business", "professional services firm", "bank or telecommunications company", "non-governmental organisation", "own business", "multinational regional office"],
        "patterns": ["office, hybrid or field-based", "targets and campaign deadlines", "client meetings and events"],
    },
    "Law and Governance": {
        "entry": ["Law student on attachment ({focus})", "Legal intern", "Pupil or trainee advocate", "Legal assistant", "Junior {title}", "Associate {title}", "Research assistant ({focus})"],
        "senior": ["Senior {title}", "Principal {title}", "Senior Associate ({focus})", "Head of {focus}"],
        "leadership": ["Partner in a law firm", "Head of Legal", "General Counsel", "Director of Legal Services", "Judge or senior judicial officer", "Commissioner or chairperson of a public body"],
        "beyond": ["Own law practice", "Arbitrator or mediator", "Legal consultant", "Lecturer in law", "Policy adviser", "Elected or appointed public office"],
        "tasks": ["research law and facts on {focus}", "draft documents accurately", "advise clients or decision makers", "prepare for and attend hearings or meetings", "manage files and deadlines", "keep client matters confidential"],
        "tools": ["legal research databases such as Kenya Law", "document drafting templates", "case management systems", "court e-filing systems", "statutes and regulations"],
        "settings": ["law firm", "in-house legal department", "public legal office", "judiciary", "regulator or commission", "legal aid or human-rights organisation", "international organisation", "own practice"],
        "patterns": ["office work with court or meeting attendance", "strict filing deadlines", "long hours before hearings or transactions"],
    },
    "Education and Teaching": {
        "entry": ["Student teacher on teaching practice", "Intern teacher", "Teaching assistant", "Assistant {title}", "Part-time or relief {title}", "Graduate assistant", "Volunteer tutor"],
        "senior": ["Senior {title}", "Lead {title}", "Head of subject or department", "Senior lecturer or master trainer"],
        "leadership": ["Deputy head teacher", "Head teacher or principal", "Dean or head of school", "Director of Studies", "County Director of Education", "Education programme director"],
        "beyond": ["Curriculum or examinations specialist", "Education consultant", "School owner", "Teacher trainer", "Ed-tech content developer", "Education policy adviser"],
        "tasks": ["plan and deliver lessons or sessions in {focus}", "assess learners and give feedback", "keep records of progress", "support learners with different needs", "work with parents, colleagues and the community", "take part in co-curricular activities"],
        "tools": ["schemes of work and lesson plans", "curriculum designs", "learning management systems", "presentation and classroom tools", "assessment records"],
        "settings": ["public primary or secondary school", "private or international school", "university or college", "TVET institution", "education non-governmental organisation", "ed-tech company", "tuition or training centre", "corporate training department"],
        "patterns": ["school terms and timetables", "marking and preparation outside class hours", "co-curricular duties"],
    },
    "Agriculture and Environment": {
        "entry": ["Attachment student ({focus})", "{title} intern", "Field assistant", "Graduate trainee ({focus})", "Trainee {title}", "Assistant {title}", "Junior {title}"],
        "senior": ["Senior {title}", "Principal {title}", "Technical specialist in {focus}", "Head of {focus}"],
        "leadership": ["Farm Manager", "Programme Manager", "County Director of Agriculture or Environment", "Technical Director", "General Manager of an agribusiness", "Country programme lead"],
        "beyond": ["Agripreneur or farm owner", "Independent consultant", "Researcher", "Lecturer or trainer", "Input supplier or agro-dealer", "Policy or regulatory officer"],
        "tasks": ["visit farms or field sites for {focus}", "collect samples and record data", "advise farmers or communities", "plan and monitor activities through the season", "write reports", "follow safety and environmental rules"],
        "tools": ["field data collection apps", "GPS devices", "sampling and testing kits", "spreadsheets", "farm or laboratory equipment"],
        "settings": ["commercial farm or agribusiness", "county agriculture or environment department", "research institute", "conservation organisation", "development organisation", "agro-input or food processing company", "own farm or enterprise", "international agency"],
        "patterns": ["field work in all weather", "seasonal peaks", "travel to rural areas"],
    },
    "Media and Creative Industries": {
        "entry": ["{title} intern", "Attachment student ({focus})", "Junior {title}", "Assistant {title}", "Freelance {title}", "Production assistant", "Trainee {title}"],
        "senior": ["Senior {title}", "Lead {title}", "Head of {focus}", "Executive {title}"],
        "leadership": ["Editor or producer in charge", "Creative Director", "Head of Content", "Studio or station manager", "Managing Director of an agency", "Executive Producer"],
        "beyond": ["Freelance practice", "Own studio or agency", "Independent creator", "Lecturer or trainer", "Brand or communications consultant", "Festival or arts programme director"],
        "tasks": ["develop ideas and briefs for {focus}", "produce work to a deadline", "revise work after feedback", "work with clients, editors or collaborators", "manage files, equipment and rights", "keep a portfolio up to date"],
        "tools": ["Adobe Creative Cloud", "cameras and audio equipment", "editing software", "content management systems", "social media platforms"],
        "settings": ["media house or broadcaster", "advertising or creative agency", "production studio", "in-house communications team", "publishing house", "digital platform", "freelance practice", "arts or cultural organisation"],
        "patterns": ["irregular hours around productions and news", "freelance and contract work is common", "tight deadlines"],
    },
    "Tourism and Hospitality": {
        "entry": ["Attachment student ({focus})", "{title} intern", "Trainee {title}", "Junior {title}", "Assistant {title}", "Seasonal or casual staff", "Management trainee"],
        "senior": ["Senior {title}", "{title} Supervisor", "Head of {focus}", "Executive {title}"],
        "leadership": ["Department Manager", "Operations Manager", "Deputy General Manager", "General Manager", "Regional or cluster manager", "Director of Operations"],
        "beyond": ["Own tour company, restaurant or lodge", "Hospitality consultant", "Trainer or lecturer", "Destination marketing role", "Cruise or international hotel roles", "Events entrepreneur"],
        "tasks": ["serve guests or customers in {focus}", "keep service standards high", "handle requests and complaints calmly", "coordinate with other departments", "follow hygiene and safety rules", "track bookings, stock or costs"],
        "tools": ["property or reservation management systems", "point-of-sale systems", "booking platforms", "kitchen or service equipment", "spreadsheets"],
        "settings": ["hotel, lodge or resort", "tour operator or travel agency", "airline or airport services company", "restaurant or catering business", "events company", "conference centre", "cruise ship or international hotel", "own business"],
        "patterns": ["shifts including weekends and holidays", "high and low tourist seasons", "long hours on your feet"],
    },
    "Science and Research": {
        "entry": ["Attachment student ({focus})", "Research intern", "Laboratory assistant", "Research assistant", "Graduate assistant", "Junior {title}", "Trainee {title}"],
        "senior": ["Senior {title}", "Principal {title}", "Research fellow in {focus}", "Chief {title}"],
        "leadership": ["Laboratory Manager", "Principal Investigator", "Head of Department", "Research Director", "Institute Director", "Chief Scientist"],
        "beyond": ["University lecturer or professor", "Industry research and development", "Science policy adviser", "Science communicator", "Consultant", "Science-based entrepreneur"],
        "tasks": ["plan and run experiments or studies in {focus}", "record methods and results carefully", "analyse data", "write reports and papers", "maintain equipment and follow safety rules", "present findings"],
        "tools": ["laboratory instruments", "R or Python", "statistical software", "reference managers", "laboratory information systems"],
        "settings": ["research institute", "university laboratory", "quality laboratory in industry", "government scientific agency", "hospital or diagnostic laboratory", "non-governmental research programme", "international research centre", "science start-up"],
        "patterns": ["laboratory or field work", "grant and publication deadlines", "postgraduate study is common for progression"],
    },
    "Logistics and Operations": {
        "entry": ["Attachment student ({focus})", "{title} intern", "Graduate trainee ({focus})", "Operations assistant", "Trainee {title}", "Junior {title}", "Assistant {title}"],
        "senior": ["Senior {title}", "{title} Supervisor", "Manager, {focus}", "Head of {focus}"],
        "leadership": ["Operations Manager", "Supply Chain Manager", "Regional Operations Manager", "Director of Operations", "Chief Operating Officer", "General Manager"],
        "beyond": ["Own logistics or clearing business", "Supply chain consultant", "Trainer or lecturer", "Humanitarian logistics roles", "Regulator or port authority roles", "International postings"],
        "tasks": ["plan and track {focus} activities", "coordinate drivers, suppliers or crews", "keep documents and records accurate", "solve delays and shortages", "follow safety and regulatory rules", "report on cost and performance"],
        "tools": ["ERP systems", "warehouse or transport management systems", "spreadsheets", "tracking and fleet systems", "customs and trade portals"],
        "settings": ["logistics or freight company", "manufacturer or retailer", "airline, port or transport operator", "clearing and forwarding firm", "e-commerce company", "humanitarian organisation", "public-sector supply unit", "own business"],
        "patterns": ["shifts in operations roles", "pressure around shipments and deadlines", "time in warehouses, ports or on the road"],
    },
    "Social and Community Services": {
        "entry": ["Attachment student ({focus})", "Volunteer in {focus}", "{title} intern", "Programme assistant", "Field assistant", "Junior {title}", "Assistant {title}"],
        "senior": ["Senior {title}", "{title} Team Leader", "Technical adviser in {focus}", "Head of {focus}"],
        "leadership": ["Programme Manager", "Area or field coordinator", "Head of Programmes", "Country Director", "Executive Director of an organisation", "County Director of Social Services"],
        "beyond": ["Independent consultant", "Founder of an organisation", "Researcher or evaluator", "Lecturer or trainer", "Policy adviser", "International organisation roles"],
        "tasks": ["work directly with people and communities on {focus}", "assess needs and plan support", "keep confidential case or project records", "run meetings, groups or training", "coordinate with partners and authorities", "report on activities and results"],
        "tools": ["case management systems", "mobile data collection tools", "monitoring and evaluation frameworks", "spreadsheets", "reporting templates"],
        "settings": ["non-governmental organisation", "county social services department", "faith-based or community organisation", "international humanitarian agency", "hospital or school", "children's or rehabilitation institution", "research or advocacy organisation", "own consultancy"],
        "patterns": ["field work in communities", "emotionally demanding situations", "project-based contracts are common"],
    },
    "Public Service and Development": {
        "entry": ["Attachment student ({focus})", "Public service intern", "Graduate trainee ({focus})", "Assistant {title}", "{title} II", "Research assistant", "Cadet or recruit"],
        "senior": ["Senior {title}", "Principal {title}", "Chief {title}", "Deputy Director, {focus}"],
        "leadership": ["Assistant Director", "Director", "County Chief Officer", "Principal Secretary", "Head of Mission or agency", "Commissioner"],
        "beyond": ["International organisation roles", "Policy consultant", "Researcher at a policy institute", "Lecturer", "Elected office", "Board or commission member"],
        "tasks": ["implement policies and programmes in {focus}", "serve citizens and respond to enquiries", "write briefs, minutes and reports", "analyse information for decisions", "follow public service procedures", "work with other agencies and partners"],
        "tools": ["government information systems", "spreadsheets and statistical tools", "policy and legal documents", "reporting templates", "records management systems"],
        "settings": ["national government ministry", "county government", "state corporation or agency", "development partner", "international organisation", "policy research institute", "regulator or commission", "disciplined service"],
        "patterns": ["office hours in most roles", "shifts and postings in disciplined services", "scheme-of-service grades and promotions"],
    },
    "Energy, Manufacturing and Skilled Trades": {
        "entry": ["Apprentice {title}", "Attachment student ({focus})", "Trainee {title}", "Helper or assistant", "Junior {title}", "Artisan (Grade III)", "Casual or contract worker"],
        "senior": ["Senior {title}", "Lead {title}", "Master craftsperson in {focus}", "Artisan (Grade I)"],
        "leadership": ["Foreman or charge hand", "Supervisor", "Workshop or site manager", "Maintenance Manager", "Plant or operations manager", "Technical Director"],
        "beyond": ["Own workshop or contracting business", "Licensed contractor", "Trainer at a TVET institution", "Inspector or assessor", "Supplier or dealer", "Work abroad on contracts"],
        "tasks": ["carry out {focus} work to a specification", "read drawings or job cards", "inspect and test finished work", "maintain tools and equipment", "follow safety procedures", "estimate materials and time"],
        "tools": ["hand and power tools", "measuring instruments", "personal protective equipment", "technical drawings", "testing equipment"],
        "settings": ["manufacturing plant", "energy company or contractor", "workshop or garage", "construction or maintenance contractor", "utility company", "small trade business", "own business", "overseas contract employer"],
        "patterns": ["physical, hands-on work", "shifts in plants", "work on sites and at height or outdoors in some trades"],
    },
}

TITLE_COLUMNS = ["career_id", "role_title", "title", "title_type", "detail_source", "data_origin", "is_synthetic"]
TASK_COLUMNS = ["career_id", "role_title", "task", "detail_source", "data_origin", "is_synthetic"]
TOOL_COLUMNS = ["career_id", "role_title", "tool", "detail_source", "data_origin", "is_synthetic"]
RELATED_COLUMNS = ["career_id", "role_title", "related_career_id", "related_role_title", "related_category",
                   "relation", "common_ground", "data_origin", "is_synthetic"]
SETTING_COLUMNS = ["career_id", "role_title", "setting_type", "setting", "data_origin", "is_synthetic"]


def _split(text: str) -> list[str]:
    return [item.strip() for item in text.split(";") if item.strip()]


def _capital(text: str) -> str:
    """Capitalise a lower-case first word, leaving names such as iOS or dbt-style terms alone."""
    first = text.split(" ", 1)[0]
    return text[:1].upper() + text[1:] if first.islower() else text


# Words too general to say two careers are alike.
COMMON_WORDS = {
    "and", "the", "for", "with", "management", "systems", "system", "skills", "basics", "knowledge", "work",
    "engineer", "officer", "manager", "analyst", "specialist", "technician", "assistant", "developer",
    "services", "service", "support", "other", "such", "tools", "software",
}


def _words(*texts: str) -> set[str]:
    cleaned = " ".join(texts).lower()
    for mark in ",;()/.-":
        cleaned = cleaned.replace(mark, " ")
    return {word for word in cleaned.split() if len(word) > 2 and word not in COMMON_WORDS}


def build_details() -> dict:
    catalog, skills = build_rows()
    core: dict[str, list[str]] = {}
    for row in skills:
        if row["skill_type"] == "core":
            core.setdefault(row["career_id"], []).append(row["skill"])
    core_sets = {career_id: {skill.casefold() for skill in items} for career_id, items in core.items()}
    # Vocabulary of each role: its title, focus, core skills and, where written, its other
    # titles, specialisms and tools. Task sentences are left out because their verbs are too general.
    vocabulary = {
        role["career_id"]: _words(
            role["role_title"], role["specialisation"], *core[role["career_id"]],
            *(part for index, part in enumerate(ROLE_DETAILS.get(role["role_title"], ())) if index != 2))
        for role in catalog
    }
    stamp = {"data_origin": DATA_ORIGIN, "is_synthetic": "true"}

    titles, tasks, tools, related, settings = [], [], [], [], []
    for role in catalog:
        career_id, title, focus, category = (role["career_id"], role["role_title"],
                                             role["specialisation"], role["category"])
        defaults = CATEGORY_DETAILS[category]
        authored = ROLE_DETAILS.get(title)
        base = {"career_id": career_id, "role_title": title}
        seen = {title.casefold()}

        def add_title(text: str, title_type: str, source: str) -> None:
            text = _capital(text.strip())
            if text.casefold() in seen:
                return
            seen.add(text.casefold())
            titles.append({**base, "title": text, "title_type": title_type, "detail_source": source, **stamp})

        if authored:
            for item in _split(authored[0]):
                add_title(item, "alternative", "authored")
            for item in _split(authored[1]):
                add_title(f"{title} ({item})", "specialism", "authored")
        for pattern in defaults["entry"] or DEFAULT_ENTRY:
            add_title(pattern.format(title=title, focus=focus), "entry", "derived")
        for pattern in defaults["senior"] or DEFAULT_SENIOR:
            add_title(pattern.format(title=title, focus=focus), "progression", "derived")
        for item in defaults["leadership"]:
            add_title(item, "leadership", "category_default")
        for item in defaults["beyond"]:
            add_title(item, "beyond", "category_default")

        task_items = _split(authored[2]) if authored else [item.format(focus=focus) for item in defaults["tasks"]]
        for item in task_items:
            tasks.append({**base, "task": _capital(item), "detail_source": "authored" if authored else "category_default", **stamp})
        tool_items = _split(authored[3]) if authored else defaults["tools"]
        for item in tool_items:
            tools.append({**base, "tool": item, "detail_source": "authored" if authored else "category_default", **stamp})

        # Neighbouring careers: shared core skills count most, then shared vocabulary, then the same category.
        scored = []
        for other in catalog:
            other_id = other["career_id"]
            if other_id == career_id:
                continue
            shared_core = core_sets[career_id] & core_sets[other_id]
            shared_words = vocabulary[career_id] & vocabulary[other_id]
            same_category = other["category"] == category
            overlap = len(shared_words) / max(len(vocabulary[career_id] | vocabulary[other_id]), 1)
            score = 3.0 * len(shared_core) + 12.0 * overlap + (1.0 if same_category else 0.0)
            if shared_core or shared_words:
                scored.append((score, other_id, other, shared_core, shared_words, same_category))
        scored.sort(key=lambda item: (-item[0], item[1]))
        for _, other_id, other, shared_core, shared_words, same_category in scored[:RELATED_PER_CAREER]:
            shared_names = [skill for skill in core[career_id] if skill.casefold() in shared_core]
            related.append({
                **base, "related_career_id": other_id, "related_role_title": other["role_title"],
                "related_category": other["category"],
                "relation": "same field" if same_category else "another field",
                "common_ground": "; ".join(shared_names or sorted(shared_words)[:6]), **stamp,
            })
        for item in scored[:4]:
            add_title(item[2]["role_title"], "lateral", "derived")

        for item in defaults["settings"]:
            settings.append({**base, "setting_type": "employer", "setting": item, **stamp})
        for item in defaults["patterns"]:
            settings.append({**base, "setting_type": "working pattern", "setting": item, **stamp})

    return {"catalog": catalog, "titles": titles, "tasks": tasks, "tools": tools,
            "related": related, "settings": settings}


def validate(details: dict) -> dict:
    catalog = details["catalog"]
    missing = set(CATEGORIES) - set(CATEGORY_DETAILS)
    if missing:
        raise ValueError(f"Categories without detail defaults: {sorted(missing)}")
    known = {role["role_title"] for role in catalog}
    unknown = set(ROLE_DETAILS) - known
    if unknown:
        raise ValueError(f"career_role_details.py names roles that are not in the catalogue: {sorted(unknown)}")
    for title, entry in ROLE_DETAILS.items():
        if len(entry) != 4 or any(len(_split(part)) < 4 for part in entry):
            raise ValueError(f"{title} needs four lists with at least four items each")
    per_career = Counter(row["career_id"] for row in details["titles"])
    ids = [role["career_id"] for role in catalog]
    thin = [career_id for career_id in ids if per_career[career_id] < 15]
    if thin:
        raise ValueError(f"Roles with fewer than 15 connected titles: {thin[:5]}")
    for name in ("tasks", "tools", "settings"):
        covered = {row["career_id"] for row in details[name]}
        if covered != set(ids):
            raise ValueError(f"Some roles have no {name}")
    related_counts = Counter(row["career_id"] for row in details["related"])
    authored_roles = sum(role["role_title"] in ROLE_DETAILS for role in catalog)
    authored_by_category = Counter(role["category"] for role in catalog if role["role_title"] in ROLE_DETAILS)
    return {
        "careers": len(ids),
        "title_rows": len(details["titles"]),
        "titles_per_career_min": min(per_career.values()),
        "titles_per_career_max": max(per_career.values()),
        "titles_by_type": dict(Counter(row["title_type"] for row in details["titles"])),
        "task_rows": len(details["tasks"]),
        "tool_rows": len(details["tools"]),
        "related_rows": len(details["related"]),
        "careers_with_no_related_roles": sum(related_counts[career_id] == 0 for career_id in ids),
        "work_setting_rows": len(details["settings"]),
        "roles_with_authored_detail": authored_roles,
        "roles_using_category_defaults": len(ids) - authored_roles,
        "authored_roles_by_category": dict(authored_by_category),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true", help="Validate the tables without writing files.")
    args = parser.parse_args()

    details = build_details()
    summary = validate(details)
    if args.check:
        print(json.dumps(summary, indent=2))
        print("Validation passed; no files written.")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "career_titles.csv", TITLE_COLUMNS, details["titles"])
    write_csv(args.output_dir / "career_tasks.csv", TASK_COLUMNS, details["tasks"])
    write_csv(args.output_dir / "career_tools.csv", TOOL_COLUMNS, details["tools"])
    write_csv(args.output_dir / "career_related.csv", RELATED_COLUMNS, details["related"])
    write_csv(args.output_dir / "career_work_settings.csv", SETTING_COLUMNS, details["settings"])
    (args.output_dir / "career_details_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {summary['title_rows']} titles, {summary['task_rows']} tasks, {summary['tool_rows']} tools, "
          f"{summary['related_rows']} related-career links and {summary['work_setting_rows']} work settings "
          f"to {args.output_dir}")
    print(f"Hand-written detail covers {summary['roles_with_authored_detail']} of {summary['careers']} roles; "
          "the rest use category defaults.")


if __name__ == "__main__":
    main()
