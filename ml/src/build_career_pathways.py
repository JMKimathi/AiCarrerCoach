"""Generate synthetic education and pathway tables for every catalogue role.

Reads the role list from build_career_catalogue.py and writes to ml/data/careers/:

  career_education.csv  study areas, qualification levels, example certifications
                        and the body a student should verify requirements with
  career_pathways.csv   five illustrative stages per role, from attachment to
                        senior practice, each tagged with an opportunity type

All rows are synthetic and illustrative. Study areas, levels, certifications and
stage timings are examples to explore. They are not admission criteria, accredited
programme lists, licensing rules or guaranteed routes. `verify_with` names the
body commonly associated with a regulated role in Kenya so the student knows
where to confirm current requirements; it does not state those requirements.

Usage (from the repository root):
  python ml/src/build_career_pathways.py
  python ml/src/build_career_pathways.py --check
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from build_career_catalogue import (  # noqa: E402
    CATEGORIES, DATA_ORIGIN, DEFAULT_OUTPUT_DIR, EVIDENCE_STATUS, build_rows, write_csv,
)

DEFAULT_VERIFY = "the relevant Kenyan regulator or professional body"
UNREGULATED_VERIFY = "target employers and training institutions"

# category -> (typical study areas, typical qualification levels, example certifications, progression options)
CATEGORY_EDUCATION = {
    "Technology and Data": (
        "Computer Science; Informatics; Information Technology; Software Engineering; Data Science",
        "Diploma; Bachelor's degree; Master's degree for research roles",
        "AWS Cloud Practitioner; Cisco CCNA; CompTIA Security+; Google Data Analytics Certificate",
        "technical specialist; engineering lead; architect; technology management; founder",
    ),
    "Engineering and Built Environment": (
        "Civil Engineering; Mechanical Engineering; Electrical Engineering; Architecture; Quantity Surveying; Geospatial Engineering",
        "Diploma; Bachelor's degree; professional registration where required",
        "AutoCAD certification; Project Management Professional (PMP); GIS certification; occupational safety training",
        "registered professional; project lead; consulting practice; technical director",
    ),
    "Health and Medicine": (
        "Medicine and Surgery; Nursing; Pharmacy; Clinical Medicine; Medical Laboratory Science; Public Health",
        "Diploma; Bachelor's degree; internship and licensing where required; postgraduate specialisation",
        "Basic Life Support; Good Clinical Practice; infection prevention training; health data management course",
        "specialist practice; clinical leadership; public health; health research; health management",
    ),
    "Banking and Finance": (
        "Commerce; Finance; Accounting; Actuarial Science; Economics; Financial Engineering",
        "Diploma; Bachelor's degree; professional examinations",
        "CPA (KASNEB); ACCA; CFA; Certified Investment and Financial Analyst (CIFA)",
        "senior analyst; finance manager; portfolio manager; chief finance officer; independent practice",
    ),
    "Business and Entrepreneurship": (
        "Business Administration; Commerce; Marketing; Human Resource Management; Entrepreneurship; Communication",
        "Certificate; Diploma; Bachelor's degree; MBA for senior roles",
        "Google Digital Marketing Certificate; Certified Human Resource Professional (CHRP); PRINCE2 or PMP; sales training",
        "team lead; department manager; consultant; business owner; executive leadership",
    ),
    "Law and Governance": (
        "Law (LLB); Political Science; Public Policy; International Relations; Criminology",
        "Diploma in Law; Bachelor of Laws; postgraduate bar training where required",
        "Certified Secretary (CS, KASNEB); mediation training; compliance certification; data protection training",
        "senior counsel; partner in a firm; in-house legal lead; judicial service; policy leadership",
    ),
    "Education and Teaching": (
        "Education (Arts or Science); Early Childhood Education; Special Needs Education; Educational Psychology; Library Science",
        "Certificate; Diploma; Bachelor of Education; postgraduate diploma in education",
        "Competency-based curriculum training; ICT integration in teaching; TVET trainer certification; first aid",
        "senior teacher; head of department; school leadership; curriculum specialist; education consultancy",
    ),
    "Agriculture and Environment": (
        "Agriculture; Agribusiness; Horticulture; Veterinary Medicine; Environmental Science; Natural Resource Management",
        "Certificate; Diploma; Bachelor's degree; professional registration where required",
        "Good Agricultural Practices training; HACCP food safety; environmental impact assessment course; GIS basics",
        "senior technical officer; farm or enterprise manager; consultant; researcher; agripreneur",
    ),
    "Media and Creative Industries": (
        "Journalism; Communication; Film and Animation; Graphic Design; Fine Art; Music; Fashion Design",
        "Certificate; Diploma; Bachelor's degree; portfolio-based entry",
        "Adobe Certified Professional; digital marketing certificate; media law and ethics training; audio production course",
        "senior creative; editor or producer; creative director; studio owner; independent practice",
    ),
    "Tourism and Hospitality": (
        "Hospitality Management; Tourism Management; Culinary Arts; Travel Operations; Events Management",
        "Certificate; Diploma; Bachelor's degree",
        "Food safety and hygiene certificate; IATA travel course; tour guiding certification; first aid",
        "supervisor; department head; general manager; hospitality entrepreneur; destination specialist",
    ),
    "Science and Research": (
        "Chemistry; Biology; Biochemistry; Physics; Mathematics; Statistics; Geology; Biotechnology",
        "Diploma; Bachelor's degree; Master's degree; PhD for independent research",
        "Research ethics training; laboratory quality (ISO 17025) awareness; R or Python for data analysis; scientific writing course",
        "senior scientist; principal investigator; laboratory manager; science policy; industry research lead",
    ),
    "Logistics and Operations": (
        "Supply Chain Management; Procurement; Logistics; Aviation; Maritime Studies; Operations Management",
        "Certificate; Diploma; Bachelor's degree; licence where required",
        "CIPS procurement qualification; KISM membership training; clearing and forwarding course; dangerous goods handling",
        "senior coordinator; operations manager; supply chain director; licensed senior crew; consultancy",
    ),
    "Social and Community Services": (
        "Social Work; Community Development; Sociology; Psychology; Counselling; Development Studies",
        "Certificate; Diploma; Bachelor's degree; Master's degree for specialist roles",
        "Monitoring and evaluation course; psychological first aid; safeguarding training; project management for development",
        "senior officer; programme manager; technical adviser; country lead; independent consultant",
    ),
    "Public Service and Development": (
        "Public Administration; Economics; Political Science; Development Studies; International Relations; Statistics",
        "Diploma; Bachelor's degree; Master's degree for senior policy roles",
        "Public financial management course; policy analysis training; monitoring and evaluation course; languages",
        "senior officer; director; policy adviser; international organisation roles; elected or appointed leadership",
    ),
    "Energy, Manufacturing and Skilled Trades": (
        "Electrical and Electronic Engineering; Mechanical Engineering; Renewable Energy; Automotive Engineering; Building Trades",
        "Trade test (artisan); Craft certificate; Diploma; Bachelor's degree for engineering roles",
        "NITA trade test; solar PV installation licence classes; occupational safety and health training; welding certification",
        "senior technician; supervisor; licensed contractor; workshop owner; plant or operations manager",
    ),
}

# Bodies commonly associated with regulated roles in Kenya, as pointers for verification only.
VERIFY_WITH = {
    **dict.fromkeys(
        ["Civil Engineer", "Structural Engineer", "Mechanical Engineer", "Electrical Engineer",
         "Water and Sanitation Engineer", "Agricultural Engineer", "Geotechnical Engineer",
         "Highway and Transport Engineer", "Renewable Energy Engineer", "Power Systems Engineer",
         "Petroleum Engineer", "Mining Engineer"],
        "Engineers Board of Kenya (EBK)"),
    **dict.fromkeys(["Architect", "Quantity Surveyor", "Landscape Architect"],
                    "Board of Registration of Architects and Quantity Surveyors (BORAQS)"),
    "Land Surveyor": "Land Surveyors Board",
    "Urban and Regional Planner": "Physical Planners Registration Board",
    **dict.fromkeys(["Medical Doctor", "Dentist", "Surgeon", "Paediatrician"],
                    "Kenya Medical Practitioners and Dentists Council (KMPDC)"),
    "Clinical Officer": "Clinical Officers Council",
    **dict.fromkeys(["Registered Nurse", "Midwife"], "Nursing Council of Kenya"),
    **dict.fromkeys(["Pharmacist", "Pharmaceutical Technologist"], "Pharmacy and Poisons Board"),
    "Medical Laboratory Technologist": "Kenya Medical Laboratory Technicians and Technologists Board (KMLTTB)",
    "Physiotherapist": "Physiotherapy Council of Kenya",
    "Nutritionist and Dietitian": "Kenya Nutritionists and Dieticians Institute (KNDI)",
    **dict.fromkeys(["Psychologist", "Counsellor", "School Counsellor", "Addiction Counsellor",
                     "Marriage and Family Therapist"], "Counsellors and Psychologists Board"),
    **dict.fromkeys(["Accountant", "Auditor"], "Institute of Certified Public Accountants of Kenya (ICPAK)"),
    "Securities Dealer": "Capital Markets Authority (CMA)",
    "Real Estate Agent": "Estate Agents Registration Board",
    **dict.fromkeys(["Advocate", "Corporate Lawyer", "State Counsel", "Prosecutor", "Environmental Lawyer",
                     "Family Lawyer", "Tax Lawyer"], "Law Society of Kenya and the Council of Legal Education"),
    "Judicial Officer": "Judicial Service Commission",
    "Company Secretary": "Institute of Certified Secretaries (ICS)",
    **dict.fromkeys(["Primary School Teacher", "Secondary School Teacher", "Special Needs Educator"],
                    "Teachers Service Commission (TSC)"),
    "Veterinary Doctor": "Kenya Veterinary Board",
    **dict.fromkeys(["Commercial Pilot", "Air Traffic Controller", "Aircraft Maintenance Engineer",
                     "Flight Dispatcher", "Drone Operations Pilot"], "Kenya Civil Aviation Authority (KCAA)"),
    "Marine Officer": "Kenya Maritime Authority",
    "Electrician": "Energy and Petroleum Regulatory Authority (EPRA)",
}

EDUCATION_COLUMNS = [
    "career_id", "role_title", "typical_study_areas", "typical_qualification_levels",
    "example_certifications", "commonly_regulated", "verify_with", "verification_note",
    "data_origin", "is_synthetic", "evidence_status",
]
PATHWAY_COLUMNS = [
    "career_id", "role_title", "stage_number", "stage_name", "example_title", "opportunity_type",
    "typical_timing", "what_to_build", "data_origin", "is_synthetic", "evidence_status",
]


def build_education(catalog: list[dict]) -> list[dict]:
    rows = []
    for role in catalog:
        study, levels, certifications, _ = CATEGORY_EDUCATION[role["category"]]
        regulated = role["commonly_regulated"] == "yes"
        verify = VERIFY_WITH.get(role["role_title"], DEFAULT_VERIFY) if regulated else UNREGULATED_VERIFY
        note = (
            f"Practising as a {role['role_title']} commonly needs registration or a licence. "
            f"Confirm accredited programmes, examinations and registration steps with {verify}."
            if regulated else
            "No single licence is assumed for this role. Confirm what each employer or institution currently asks for."
        )
        rows.append({
            "career_id": role["career_id"], "role_title": role["role_title"],
            "typical_study_areas": study, "typical_qualification_levels": levels,
            "example_certifications": certifications,
            "commonly_regulated": role["commonly_regulated"], "verify_with": verify,
            "verification_note": note, "data_origin": DATA_ORIGIN, "is_synthetic": "true",
            "evidence_status": EVIDENCE_STATUS,
        })
    return rows


def build_pathways(catalog: list[dict]) -> list[dict]:
    rows = []
    for role in catalog:
        title, focus = role["role_title"], role["specialisation"]
        progression = CATEGORY_EDUCATION[role["category"]][3]
        regulated = role["commonly_regulated"] == "yes"
        licence_step = " Complete any registration or licensing step that applies." if regulated else ""
        stages = [
            ("Attachment during study", f"Attachment student ({focus})", "industrial attachment",
             "During the course, often in a long vacation or attachment term",
             f"First exposure to {focus}; a logbook or short report of the tasks observed and done."),
            ("Internship", f"{title} intern", "internship",
             "Final year or the first months after graduating",
             "One or two pieces of supervised work that can be described on a CV with clear results."),
            ("Graduate entry", f"Graduate trainee ({focus})", "graduate programme",
             "After graduating, typically a structured one to two year programme",
             "Rotations across teams and a mentor; evidence of learning quickly and working with others."),
            ("Early career", f"Junior {title}", "full-time job",
             "First full-time role, with or without a graduate programme first",
             f"Independent delivery of routine {focus} work.{licence_step}"),
            ("Established and senior practice", f"Senior {title}", "full-time job",
             "After several years of practice",
             f"A track record and a chosen direction, for example: {progression}."),
        ]
        for number, (stage, example, opportunity, timing, build) in enumerate(stages, start=1):
            rows.append({
                "career_id": role["career_id"], "role_title": title, "stage_number": number,
                "stage_name": stage, "example_title": example, "opportunity_type": opportunity,
                "typical_timing": timing, "what_to_build": build,
                "data_origin": DATA_ORIGIN, "is_synthetic": "true", "evidence_status": EVIDENCE_STATUS,
            })
    return rows


def validate(catalog: list[dict], education: list[dict], pathways: list[dict]) -> None:
    missing = set(CATEGORIES) - set(CATEGORY_EDUCATION)
    if missing:
        raise ValueError(f"Categories without education defaults: {sorted(missing)}")
    titles = {role["role_title"] for role in catalog}
    unknown = set(VERIFY_WITH) - titles
    if unknown:
        raise ValueError(f"VERIFY_WITH names roles that are not in the catalogue: {sorted(unknown)}")
    regulated_titles = {role["role_title"] for role in catalog if role["commonly_regulated"] == "yes"}
    unflagged = set(VERIFY_WITH) - regulated_titles
    if unflagged:
        raise ValueError(f"VERIFY_WITH roles not marked as regulated in the catalogue: {sorted(unflagged)}")
    if len(education) != len(catalog):
        raise ValueError("Every role needs exactly one education row")
    if len(pathways) != len(catalog) * 5:
        raise ValueError("Every role needs exactly five pathway stages")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true", help="Validate the generated tables without writing files.")
    args = parser.parse_args()

    catalog, _ = build_rows()
    education = build_education(catalog)
    pathways = build_pathways(catalog)
    validate(catalog, education, pathways)
    named_bodies = sum(row["verify_with"] not in (DEFAULT_VERIFY, UNREGULATED_VERIFY) for row in education)
    summary = {
        "education_rows": len(education), "pathway_rows": len(pathways),
        "regulated_roles_with_named_body": named_bodies,
        "regulated_roles_with_generic_pointer": sum(row["verify_with"] == DEFAULT_VERIFY for row in education),
    }
    if args.check:
        print(json.dumps(summary, indent=2))
        print("Validation passed; no files written.")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "career_education.csv", EDUCATION_COLUMNS, education)
    write_csv(args.output_dir / "career_pathways.csv", PATHWAY_COLUMNS, pathways)
    print(f"Wrote {len(education)} education rows and {len(pathways)} pathway rows to {args.output_dir}")


if __name__ == "__main__":
    main()
