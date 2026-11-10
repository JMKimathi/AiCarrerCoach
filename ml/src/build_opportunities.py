"""Generate opportunity templates for every catalogue role (Kenya and international).

Writes ml/data/careers/opportunity_templates.csv. Each role gets seven templates:

  industrial attachment   Kenya
  internship              Kenya and international
  graduate programme      Kenya and international
  full-time job           Kenya and international

A template describes what that kind of opening usually looks like for the role:
the sort of employer, when students apply, how long it lasts, what applicants
usually show, which documents are asked for, where such openings are advertised
and what to type into a job board to find real ones.

These are NOT vacancies. No employer is named, no opening is claimed to exist and
`is_live_vacancy` is always false. Durations and timings are typical patterns
for orientation, not rules. Real openings must come from employers' own pages.

Usage (from the repository root):
  python ml/src/build_opportunities.py
  python ml/src/build_opportunities.py --check
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from build_career_catalogue import CATEGORIES, DATA_ORIGIN, DEFAULT_OUTPUT_DIR, build_rows, write_csv  # noqa: E402

# category -> (kinds of employer, where openings are usually advertised)
CATEGORY_MARKET = {
    "Technology and Data": (
        ["technology company or start-up", "bank or telecommunications firm with an in-house technology team",
         "software consultancy or agency", "government ICT department or parastatal"],
        ["company careers pages", "university career offices and tech hubs", "professional networking sites and developer communities"],
    ),
    "Engineering and Built Environment": (
        ["engineering consultancy", "construction contractor", "county or national government works department",
         "utility or infrastructure agency"],
        ["company careers pages", "professional institution notices", "government and parastatal advertisements"],
    ),
    "Health and Medicine": (
        ["public hospital or county health facility", "private or faith-based hospital",
         "health-focused non-governmental organisation", "research institute or diagnostic laboratory"],
        ["county public service board advertisements", "hospital careers pages", "regulator and professional association notices"],
    ),
    "Banking and Finance": (
        ["commercial bank", "audit or accounting firm", "insurance company or pension administrator",
         "SACCO, microfinance institution or fintech"],
        ["company graduate-recruitment pages", "professional body job boards", "university career fairs"],
    ),
    "Business and Entrepreneurship": (
        ["consumer goods or retail company", "marketing or communications agency",
         "start-up or small business", "professional services firm"],
        ["company careers pages", "professional networking sites", "university career offices"],
    ),
    "Law and Governance": (
        ["law firm", "in-house legal department", "public legal office or commission",
         "legal aid or human-rights organisation"],
        ["law firm websites", "public service and judiciary advertisements", "law school and professional society notices"],
    ),
    "Education and Teaching": (
        ["public school", "private or international school", "college, university or TVET institution",
         "education-focused non-governmental organisation or ed-tech company"],
        ["teacher recruitment portals and advertisements", "school and institution websites", "education job boards"],
    ),
    "Agriculture and Environment": (
        ["commercial farm or agribusiness", "county agriculture or environment department",
         "research institute", "conservation or development organisation"],
        ["county public service board advertisements", "organisation careers pages", "sector job boards"],
    ),
    "Media and Creative Industries": (
        ["media house or broadcaster", "advertising or creative agency",
         "production studio", "in-house communications team or freelance practice"],
        ["company careers pages", "creative communities and portfolio platforms", "referrals and open calls"],
    ),
    "Tourism and Hospitality": (
        ["hotel, lodge or resort", "tour operator or travel agency",
         "airline or airport services company", "restaurant, events or catering business"],
        ["company careers pages", "hospitality college placement offices", "sector job boards"],
    ),
    "Science and Research": (
        ["research institute", "university laboratory or department",
         "manufacturing or pharmaceutical quality laboratory", "government scientific agency"],
        ["institute and university vacancy pages", "research funder and fellowship calls", "scientific society notices"],
    ),
    "Logistics and Operations": (
        ["logistics or freight company", "manufacturer or retailer with a supply chain team",
         "airline, port or transport operator", "humanitarian or public-sector supply chain unit"],
        ["company careers pages", "professional body job boards", "government and parastatal advertisements"],
    ),
    "Social and Community Services": (
        ["non-governmental organisation", "county social services department",
         "faith-based or community organisation", "international humanitarian agency"],
        ["organisation careers pages", "development-sector job boards", "county public service board advertisements"],
    ),
    "Public Service and Development": (
        ["national government ministry or agency", "county government",
         "development partner or international organisation", "policy research institute"],
        ["Public Service Commission advertisements", "county public service board advertisements", "international organisation careers portals"],
    ),
    "Energy, Manufacturing and Skilled Trades": (
        ["manufacturing plant or factory", "energy company or contractor",
         "workshop, garage or small trade business", "construction or maintenance contractor"],
        ["company careers pages and notice boards", "TVET institution placement offices", "referrals from tradespeople and site supervisors"],
    ),
}

# opportunity type -> (markets, title pattern, eligibility, duration, timing, documents)
OPPORTUNITY_TYPES = {
    "industrial attachment": (
        ["Kenya"], "Attachment student ({focus})",
        "Continuing student whose course requires attachment",
        "Usually 8 to 12 weeks",
        "Apply two to three months before the attachment term or long vacation",
        "Introduction letter from the institution; CV; insurance cover where requested; attachment logbook",
    ),
    "internship": (
        ["Kenya", "International"], "{title} intern",
        "Final-year student or recent graduate",
        "Usually 3 to 6 months",
        "Openings appear through the year, with more around graduation periods",
        "CV; cover letter; academic transcript; certificates",
    ),
    "graduate programme": (
        ["Kenya", "International"], "Graduate trainee ({focus})",
        "Recent graduate, often within two years of finishing",
        "Usually 12 to 24 months with rotations",
        "Many programmes recruit once a year; check each employer's own calendar",
        "CV; academic transcript; cover letter or application questions; online assessments where used",
    ),
    "full-time job": (
        ["Kenya", "International"], "Junior {title}",
        "Graduate or qualified candidate ready for an entry-level role",
        "Permanent or fixed-term contract",
        "Openings appear through the year",
        "CV; cover letter; certificates; referees",
    ),
}

LOCAL_EMPLOYER_WORDS = ("government", "county", "public", "parastatal")
INTERNATIONAL_CHANNELS = "employer careers pages; international job boards; professional networking sites"
INTERNATIONAL_NOTE = (
    "For roles outside Kenya, check visa and work-permit rules and whether your qualification is recognised there."
)
REGULATED_NOTE = "Registration or a licence may be required before practising; confirm with the regulator."

COLUMNS = [
    "opportunity_id", "career_id", "role_title", "opportunity_type", "market", "example_title",
    "employer_type", "eligibility", "typical_duration", "typical_timing", "applicants_usually_show",
    "documents_usually_requested", "where_advertised", "search_phrases", "notes",
    "is_live_vacancy", "data_origin", "is_synthetic",
]


def _choose(pool: list[str], key: str) -> str:
    return pool[int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % len(pool)]


def build_opportunities() -> list[dict]:
    catalog, skills = build_rows()
    core: dict[str, list[str]] = {}
    for row in skills:
        if row["skill_type"] == "core":
            core.setdefault(row["career_id"], []).append(row["skill"])
    rows = []
    for role in catalog:
        career_id, title, focus = role["career_id"], role["role_title"], role["specialisation"]
        employers, channels = CATEGORY_MARKET[role["category"]]
        regulated = role["commonly_regulated"] == "yes"
        number = 0
        for opportunity, (markets, pattern, eligibility, duration, timing, documents) in OPPORTUNITY_TYPES.items():
            for market in markets:
                number += 1
                pool, advertised = employers, "; ".join(channels)
                if market == "International":
                    # Government and county employers are local, so leave them out abroad.
                    pool = [item for item in employers
                            if not any(word in item for word in LOCAL_EMPLOYER_WORDS)] or employers
                    advertised = INTERNATIONAL_CHANNELS
                employer = _choose(pool, f"{career_id}:{opportunity}:{market}")
                if market == "International":
                    employer = f"international or remote-first {employer}"
                shown = core[career_id][:3]
                if opportunity == "industrial attachment":
                    show = f"Interest in {focus}, a basic grounding in {shown[0]}, and willingness to learn"
                elif opportunity == "internship":
                    show = f"Coursework or a small project using {shown[0]} and {shown[1]}"
                elif opportunity == "graduate programme":
                    show = f"A solid academic record, evidence of {shown[0]} and {shown[1]}, and teamwork"
                else:
                    show = f"Demonstrated {', '.join(shown)} through projects, attachment or earlier work"
                notes = [note for note, applies in ((INTERNATIONAL_NOTE, market == "International"),
                                                    (REGULATED_NOTE, regulated and opportunity != "industrial attachment"))
                         if applies]
                place = "Kenya" if market == "Kenya" else "remote OR international"
                rows.append({
                    "opportunity_id": f"OPP-{career_id.split('-')[1]}-{number:02d}",
                    "career_id": career_id, "role_title": title, "opportunity_type": opportunity,
                    "market": market, "example_title": pattern.format(title=title, focus=focus),
                    "employer_type": employer, "eligibility": eligibility,
                    "typical_duration": duration, "typical_timing": timing,
                    "applicants_usually_show": show,
                    "documents_usually_requested": documents + ("; registration or licence where the role is regulated"
                                                                if regulated and opportunity == "full-time job" else ""),
                    "where_advertised": advertised,
                    "search_phrases": f"{title} {opportunity} {place}; {focus} {opportunity} {place}",
                    "notes": " ".join(notes),
                    "is_live_vacancy": "false", "data_origin": DATA_ORIGIN, "is_synthetic": "true",
                })
    return rows


def validate(rows: list[dict]) -> dict:
    missing = set(CATEGORIES) - set(CATEGORY_MARKET)
    if missing:
        raise ValueError(f"Categories without market defaults: {sorted(missing)}")
    ids = [row["opportunity_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate opportunity_id values")
    if any(row["is_live_vacancy"] != "false" for row in rows):
        raise ValueError("Templates must never be marked as live vacancies")
    per_career = Counter(row["career_id"] for row in rows)
    if set(per_career.values()) != {7}:
        raise ValueError("Every role needs exactly seven templates")
    return {
        "opportunity_templates": len(rows),
        "careers": len(per_career),
        "by_type": dict(Counter(row["opportunity_type"] for row in rows)),
        "by_market": dict(Counter(row["market"] for row in rows)),
        "live_vacancies": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true", help="Validate the templates without writing files.")
    args = parser.parse_args()

    rows = build_opportunities()
    summary = validate(rows)
    if args.check:
        print(json.dumps(summary, indent=2))
        print("Validation passed; no files written.")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "opportunity_templates.csv", COLUMNS, rows)
    print(f"Wrote {len(rows)} opportunity templates to {args.output_dir}")


if __name__ == "__main__":
    main()
