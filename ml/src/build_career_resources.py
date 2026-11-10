"""Link every catalogue role to official sources a student can check for themselves.

Writes to ml/data/careers/:

  trusted_sources.csv   one row per official source (regulators, examination and
                        admissions bodies, occupational references)
  career_resources.csv  one row per (career, source) link, keyed by career_id

Only sources whose official web address was confirmed by a web search on
VERIFIED_ON are listed. Confirmation means the address appeared in search
results as that organisation's own site; the pages were not read in full, and
addresses can change. Bodies that could not be confirmed that day (for example
the Engineers Board of Kenya, BORAQS and the Pharmacy and Poisons Board) are
deliberately left out here and remain named in career_education.csv, so the
student still knows who to ask.

The links say where to look. They do not state requirements, and nothing here
replaces checking the source itself.

Usage (from the repository root):
  python ml/src/build_career_resources.py
  python ml/src/build_career_resources.py --check
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from build_career_catalogue import CATEGORIES, DEFAULT_OUTPUT_DIR, build_rows, write_csv  # noqa: E402

VERIFIED_ON = "2026-11-10"
VERIFICATION_METHOD = "official address confirmed by web search; page content not reviewed"

# source_id -> (name, url, source_type, market, what to check there)
SOURCES = {
    "KUCCPS": ("Kenya Universities and Colleges Central Placement Service", "https://kuccps.net/",
               "admissions", "Kenya", "Course placement, programme choices and cluster information."),
    "CUE": ("Commission for University Education", "https://www.cue.or.ke/",
            "accreditation", "Kenya", "Whether a university and its programmes are accredited."),
    "KNQA": ("Kenya National Qualifications Authority", "https://www.knqa.go.ke/",
             "qualifications", "Kenya", "How qualifications are levelled and recognised in Kenya."),
    "TVETA": ("Technical and Vocational Education and Training Authority", "https://www.tveta.go.ke/",
              "accreditation", "Kenya", "Whether a TVET institution and its trainers are registered."),
    "NITA": ("National Industrial Training Authority", "https://nita.go.ke/our-services/trade-testing.html",
             "examinations", "Kenya", "Government trade tests, grades and industrial attachment."),
    "PSC": ("Public Service Commission of Kenya", "https://publicservice.go.ke/",
            "public employer", "Kenya", "Public service vacancies and the Public Service Internship Programme."),
    "ONET": ("O*NET OnLine", "https://www.onetonline.org/",
             "occupational reference", "International", "Tasks, skills and work context for occupations. It describes United States occupations, so use it for exploration."),
    "ISCO": ("ILO International Standard Classification of Occupations (ISCO-08)", "https://isco.ilo.org/en/isco-08",
             "occupational reference", "International", "How occupations are defined and grouped internationally."),
    "KMPDC": ("Kenya Medical Practitioners and Dentists Council", "https://kmpdc.go.ke/",
              "regulator", "Kenya", "Registration, internship and licensing of medical and dental practitioners."),
    "NCK": ("Nursing Council of Kenya", "https://nckenya.com/",
            "regulator", "Kenya", "Approved nursing and midwifery training, examinations and licensing."),
    "COC": ("Clinical Officers Council", "https://clinicalofficerscouncil.org/",
            "regulator", "Kenya", "Registration, examinations and licensing of clinical officers."),
    "KMLTTB": ("Kenya Medical Laboratory Technicians and Technologists Board", "https://www.kmlttb.org/",
               "regulator", "Kenya", "Registration and licensing of medical laboratory professionals."),
    "KNDI": ("Kenya Nutritionists and Dieticians Institute", "https://www.kndi.institute/",
             "regulator", "Kenya", "Registration and licensing of nutritionists and dieticians."),
    "CPB": ("Counsellors and Psychologists Board", "https://cpb.health.go.ke/",
            "regulator", "Kenya", "Registration and licensing of counsellors and psychologists."),
    "KVB": ("Kenya Veterinary Board", "https://kenyavetboard.or.ke/",
            "regulator", "Kenya", "Registration of veterinary surgeons and veterinary paraprofessionals."),
    "ICPAK": ("Institute of Certified Public Accountants of Kenya", "https://www.icpak.com/",
              "professional body", "Kenya", "Membership and practising requirements for accountants."),
    "KASNEB": ("Kasneb", "https://www.kasneb.or.ke/",
               "examinations", "Kenya", "Professional examinations such as CPA, CS and CIFA."),
    "CMA": ("Capital Markets Authority", "https://www.cma.or.ke/",
            "regulator", "Kenya", "Licensing of capital markets intermediaries and their staff."),
    "LSK": ("Law Society of Kenya", "https://lsk.or.ke/",
            "professional body", "Kenya", "Membership of advocates and practising certificates."),
    "CLE": ("Council of Legal Education", "https://cle.or.ke/",
            "regulator", "Kenya", "Licensed legal education providers and the bar examination."),
    "TSC": ("Teachers Service Commission", "https://tsc.go.ke/index.php/teacher-registration",
            "regulator", "Kenya", "Teacher registration and recruitment."),
    "KCAA": ("Kenya Civil Aviation Authority", "https://kcaa.or.ke/personnel-licencing",
             "regulator", "Kenya", "Licences for pilots, air traffic controllers, aircraft engineers, dispatchers and cabin crew."),
    "KMA": ("Kenya Maritime Authority", "https://kma.go.ke/",
            "regulator", "Kenya", "Seafarer certification and maritime training requirements."),
    "EPRA": ("Energy and Petroleum Regulatory Authority", "https://www.epra.go.ke/",
             "regulator", "Kenya", "Licences for electrical workers, contractors and solar PV technicians."),
    "MCK": ("Media Council of Kenya", "https://mediacouncil.or.ke/",
            "regulator", "Kenya", "Accreditation of journalists and the code of conduct."),
    "TRA": ("Tourism Regulatory Authority", "https://tra.go.ke/",
            "regulator", "Kenya", "Licensing of tourism activities and services."),
    "ODPC": ("Office of the Data Protection Commissioner", "https://www.odpc.go.ke/",
             "regulator", "Kenya", "Data protection law, guidance notes and registration of data handlers."),
    "NEMA": ("National Environment Management Authority", "https://nema.go.ke/registration-of-experts/",
             "regulator", "Kenya", "Registration of environmental impact assessment experts."),
}

# Sources every role links to.
GENERAL_SOURCES = ["KUCCPS", "CUE", "KNQA", "ONET", "ISCO", "PSC"]

# Sources that apply to a whole category.
CATEGORY_SOURCES = {
    "Energy, Manufacturing and Skilled Trades": ["TVETA", "NITA"],
    "Tourism and Hospitality": ["TVETA"],
    "Banking and Finance": ["KASNEB"],
}

# Sources that apply to named roles.
ROLE_SOURCES = {
    "KMPDC": ["Medical Doctor", "Dentist", "Surgeon", "Paediatrician"],
    "NCK": ["Registered Nurse", "Midwife"],
    "COC": ["Clinical Officer"],
    "KMLTTB": ["Medical Laboratory Technologist"],
    "KNDI": ["Nutritionist and Dietitian"],
    "CPB": ["Psychologist", "Counsellor", "School Counsellor", "Addiction Counsellor", "Marriage and Family Therapist"],
    "KVB": ["Veterinary Doctor", "Animal Health Technician"],
    "ICPAK": ["Accountant", "Auditor", "Forensic Accountant", "Cost Accountant", "Financial Controller"],
    "KASNEB": ["Company Secretary"],
    "CMA": ["Securities Dealer", "Investment Analyst", "Equity Trader"],
    "LSK": ["Advocate", "Corporate Lawyer", "State Counsel", "Prosecutor", "Environmental Lawyer", "Family Lawyer", "Tax Lawyer"],
    "CLE": ["Advocate", "Corporate Lawyer", "State Counsel", "Prosecutor", "Environmental Lawyer", "Family Lawyer", "Tax Lawyer", "Paralegal"],
    "TSC": ["Primary School Teacher", "Secondary School Teacher", "Special Needs Educator", "Language Teacher",
            "Music Teacher", "Sports Coach and PE Teacher", "School Head and Administrator"],
    "KCAA": ["Commercial Pilot", "Air Traffic Controller", "Aircraft Maintenance Engineer", "Flight Dispatcher",
             "Drone Operations Pilot", "Cabin Crew Member"],
    "KMA": ["Marine Officer", "Marine Engineer"],
    "EPRA": ["Electrician", "Solar PV Technician"],
    "MCK": ["Journalist", "Broadcast Presenter", "Editor"],
    "TRA": ["Tour Operator", "Tour Guide", "Travel Consultant", "Hotel Manager", "Safari Lodge Manager",
            "Ecotourism Officer", "Tourism Product Developer"],
    "ODPC": ["Data Protection Officer", "Data Privacy Counsel"],
    "NEMA": ["Environmental Consultant", "Environmental Engineer", "Environmental Scientist"],
    "TVETA": ["TVET Trainer"],
}

SOURCE_COLUMNS = ["source_id", "source_name", "url", "source_type", "market", "what_to_check",
                  "verified_on", "verification_method"]
LINK_COLUMNS = ["career_id", "role_title", "source_id", "source_name", "url", "source_type", "market",
                "link_reason", "what_to_check", "verified_on", "verification_method"]


def build_links(catalog: list[dict]) -> list[dict]:
    by_role: dict[str, list[str]] = {}
    for source_id, titles in ROLE_SOURCES.items():
        for title in titles:
            by_role.setdefault(title, []).append(source_id)
    rows = []
    for role in catalog:
        wanted: list[tuple[str, str]] = [(source_id, "role-specific") for source_id in by_role.get(role["role_title"], [])]
        wanted += [(source_id, "sector-wide") for source_id in CATEGORY_SOURCES.get(role["category"], [])]
        wanted += [(source_id, "general") for source_id in GENERAL_SOURCES]
        seen: set[str] = set()
        for source_id, reason in wanted:
            if source_id in seen:
                continue
            seen.add(source_id)
            name, url, source_type, market, check = SOURCES[source_id]
            rows.append({
                "career_id": role["career_id"], "role_title": role["role_title"], "source_id": source_id,
                "source_name": name, "url": url, "source_type": source_type, "market": market,
                "link_reason": reason, "what_to_check": check,
                "verified_on": VERIFIED_ON, "verification_method": VERIFICATION_METHOD,
            })
    return rows


def validate(catalog: list[dict], links: list[dict]) -> dict:
    titles = {role["role_title"] for role in catalog}
    for source_id, names in ROLE_SOURCES.items():
        if source_id not in SOURCES:
            raise ValueError(f"ROLE_SOURCES uses unknown source {source_id}")
        unknown = set(names) - titles
        if unknown:
            raise ValueError(f"{source_id} is linked to roles not in the catalogue: {sorted(unknown)}")
    for category, source_ids in CATEGORY_SOURCES.items():
        if category not in CATEGORIES or set(source_ids) - set(SOURCES):
            raise ValueError(f"Bad category source mapping for {category}")
    for source_id, (_, url, _, _, _) in SOURCES.items():
        if not url.startswith("https://"):
            raise ValueError(f"{source_id} must use an https address")
    used = {row["source_id"] for row in links}
    unused = set(SOURCES) - used
    if unused:
        raise ValueError(f"Sources never linked to a role: {sorted(unused)}")
    per_career = Counter(row["career_id"] for row in links)
    return {
        "sources": len(SOURCES),
        "career_links": len(links),
        "role_specific_links": sum(row["link_reason"] == "role-specific" for row in links),
        "careers_with_role_specific_source": len({row["career_id"] for row in links if row["link_reason"] == "role-specific"}),
        "min_links_per_career": min(per_career.values()),
        "max_links_per_career": max(per_career.values()),
        "verified_on": VERIFIED_ON,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true", help="Validate the tables without writing files.")
    args = parser.parse_args()

    catalog, _ = build_rows()
    links = build_links(catalog)
    summary = validate(catalog, links)
    if args.check:
        print(json.dumps(summary, indent=2))
        print("Validation passed; no files written.")
        return
    sources = [
        {"source_id": source_id, "source_name": name, "url": url, "source_type": source_type, "market": market,
         "what_to_check": check, "verified_on": VERIFIED_ON, "verification_method": VERIFICATION_METHOD}
        for source_id, (name, url, source_type, market, check) in SOURCES.items()
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "trusted_sources.csv", SOURCE_COLUMNS, sources)
    write_csv(args.output_dir / "career_resources.csv", LINK_COLUMNS, links)
    print(f"Wrote {len(sources)} sources and {len(links)} career links to {args.output_dir}")


if __name__ == "__main__":
    main()
