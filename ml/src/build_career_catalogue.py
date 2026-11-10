"""Generate the synthetic career catalogue and skills tables (Kenya and international).

Writes small, traceable CSV files to ml/data/careers/:

  career_catalog.csv  one row per career role, shared key `career_id`
  career_skills.csv   core, preferred and transferable skills per role
  catalogue_manifest.json  row counts and per-category counts

Every row is marked synthetic and unverified. Descriptions are templated drafts
built from the role's focus area and skills. They are illustrative guidance for
exploration, not verified Kenyan qualification, licensing or hiring rules.
Roles whose titles end in `*` in CATALOGUE below are commonly regulated
professions; students must confirm requirements with the relevant professional
body or authority.

Later pipeline stages (education, pathways, resources, interview questions,
opportunities, training data) reuse `career_id` to link back to this table.

Usage (from the repository root):
  python ml/src/build_career_catalogue.py
  python ml/src/build_career_catalogue.py --check
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "ml" / "data" / "careers"

EVIDENCE_STATUS = "illustrative_guidance_not_verified_local_requirements"
DATA_ORIGIN = "synthetic"
MARKET_SCOPE = "Kenya; International"
OPPORTUNITY_TYPES = "internship; industrial attachment; graduate programme; full-time job"
DESCRIPTION_STATUS = "templated_draft"

TRANSFERABLE_SKILLS = [
    "communication", "teamwork", "problem solving", "digital literacy", "time management",
]

# Sector names match the existing synthetic pathway dataset (14 sectors) plus one new sector.
# category -> (short phrase used in descriptions, preferred skills shared by the category)
CATEGORIES = {
    "Technology and Data": ("technology and data", ["analytical thinking", "continuous learning", "documentation"]),
    "Engineering and Built Environment": ("engineering and the built environment", ["technical drawing", "mathematics", "safety awareness"]),
    "Health and Medicine": ("health and medicine", ["biology", "ethics", "patient communication"]),
    "Banking and Finance": ("banking, finance and accounting", ["numeracy", "attention to detail", "regulatory awareness"]),
    "Business and Entrepreneurship": ("business, marketing and entrepreneurship", ["customer insight", "negotiation", "planning"]),
    "Law and Governance": ("law and governance", ["legal research", "critical reading", "ethics"]),
    "Education and Teaching": ("education and teaching", ["lesson planning", "learner engagement", "assessment design"]),
    "Agriculture and Environment": ("agriculture and the environment", ["field observation", "sustainability", "data recording"]),
    "Media and Creative Industries": ("media and the creative industries", ["storytelling", "creativity", "audience awareness"]),
    "Tourism and Hospitality": ("tourism and hospitality", ["customer service", "cultural awareness", "service coordination"]),
    "Science and Research": ("science and research", ["scientific method", "data analysis", "laboratory safety"]),
    "Logistics and Operations": ("logistics, transport and operations", ["process improvement", "planning", "regulatory compliance"]),
    "Social and Community Services": ("social and community services", ["empathy", "case documentation", "community engagement"]),
    "Public Service and Development": ("public service and development", ["policy literacy", "report writing", "stakeholder engagement"]),
    "Energy, Manufacturing and Skilled Trades": ("energy, manufacturing and skilled trades", ["technical safety", "equipment handling", "quality checking"]),
}

# category -> list of (role title, focus area, "core skill; core skill; core skill; ...").
# A trailing `*` on the title marks a commonly regulated profession.
CATALOGUE = {
    "Technology and Data": [
        ("Software Developer", "software engineering", "programming; algorithms; version control; testing"),
        ("Mobile Application Developer", "mobile development", "Kotlin; Android; UI design; API integration"),
        ("Web Developer", "web development", "HTML and CSS; JavaScript; responsive design; web security basics"),
        ("Data Analyst", "data analysis", "SQL; spreadsheets; data visualisation; statistics"),
        ("Data Scientist", "machine learning", "Python; statistics; machine learning; data wrangling"),
        ("Machine Learning Engineer", "AI engineering", "Python; model deployment; MLOps; deep learning"),
        ("Data Engineer", "data infrastructure", "SQL; ETL pipelines; cloud platforms; data modelling"),
        ("Cloud Engineer", "cloud computing", "cloud platforms; networking; infrastructure as code; monitoring"),
        ("DevOps Engineer", "delivery automation", "CI/CD; Linux; containers; scripting"),
        ("Cybersecurity Analyst", "information security", "threat analysis; network security; incident response; risk assessment"),
        ("Network Engineer", "networking", "routing and switching; network design; troubleshooting; network security"),
        ("Database Administrator", "data management", "SQL; backup and recovery; performance tuning; data security"),
        ("UI/UX Designer", "product design", "user research; wireframing; prototyping; usability testing"),
        ("Quality Assurance Engineer", "software testing", "test design; test automation; bug reporting; requirements analysis"),
        ("IT Support Specialist", "IT operations", "troubleshooting; customer support; operating systems; hardware support"),
        ("Systems Analyst", "systems analysis", "requirements gathering; process modelling; documentation; stakeholder communication"),
        ("Embedded Systems Engineer", "embedded systems and IoT", "C programming; microcontrollers; electronics basics; debugging"),
        ("Technology Product Manager", "product management", "product strategy; roadmapping; stakeholder management; analytics"),
    ],
    "Engineering and Built Environment": [
        ("Civil Engineer*", "civil works", "structural analysis; surveying; construction materials; project coordination"),
        ("Structural Engineer*", "structural design", "structural analysis; design codes; CAD modelling; load calculations"),
        ("Mechanical Engineer*", "mechanical systems", "thermodynamics; machine design; CAD modelling; maintenance planning"),
        ("Electrical Engineer*", "electrical systems", "circuit analysis; power systems; electrical safety; testing and commissioning"),
        ("Electronics and Telecommunications Engineer", "communication systems", "signal processing; circuit design; network protocols; radio systems"),
        ("Mechatronics Engineer", "automation and robotics", "control systems; sensors and actuators; PLC programming; electronics"),
        ("Chemical Engineer", "process engineering", "process design; mass and energy balances; plant safety; process control"),
        ("Architect*", "building design", "architectural design; CAD and BIM; building regulations; site coordination"),
        ("Quantity Surveyor*", "construction costing", "cost estimation; bills of quantities; contract administration; valuation"),
        ("Land Surveyor*", "land and geospatial survey", "surveying instruments; mapping; cadastral survey; GIS"),
        ("Urban and Regional Planner*", "spatial planning", "spatial analysis; land-use planning; policy review; community consultation"),
        ("Construction Project Manager", "construction management", "scheduling; site supervision; budgeting; contract management"),
        ("Geospatial and GIS Specialist", "geospatial analysis", "GIS software; remote sensing; spatial databases; cartography"),
        ("Water and Sanitation Engineer*", "water systems", "hydraulics; water treatment; pipe network design; sanitation planning"),
        ("Biomedical Engineer", "medical devices", "medical instrumentation; electronics; equipment maintenance; regulatory awareness"),
        ("Industrial Engineer", "process optimisation", "work study; process mapping; lean methods; production planning"),
        ("Building Services Engineer", "building systems", "HVAC design; electrical services; plumbing design; energy efficiency"),
        ("Environmental Engineer", "environmental systems", "environmental assessment; waste treatment; pollution control; sustainability reporting"),
    ],
    "Health and Medicine": [
        ("Medical Doctor*", "clinical medicine", "clinical assessment; diagnosis; patient management; medical ethics"),
        ("Clinical Officer*", "primary clinical care", "clinical assessment; minor procedures; patient triage; referral management"),
        ("Registered Nurse*", "nursing care", "patient care; medication administration; vital signs monitoring; health education"),
        ("Pharmacist*", "pharmaceutical care", "pharmacology; dispensing; medication counselling; inventory control"),
        ("Dentist*", "oral health", "dental diagnosis; restorative procedures; infection control; patient communication"),
        ("Medical Laboratory Technologist*", "diagnostic laboratory", "specimen handling; laboratory testing; quality control; instrument operation"),
        ("Radiographer*", "medical imaging", "imaging techniques; radiation safety; patient positioning; image quality assessment"),
        ("Physiotherapist*", "rehabilitation", "movement assessment; therapeutic exercise; manual therapy; treatment planning"),
        ("Nutritionist and Dietitian*", "clinical and community nutrition", "nutritional assessment; diet planning; counselling; community outreach"),
        ("Occupational Therapist*", "functional rehabilitation", "functional assessment; activity planning; assistive devices; client coaching"),
        ("Psychologist*", "mental health", "psychological assessment; counselling skills; case formulation; confidentiality"),
        ("Public Health Officer", "disease prevention", "epidemiology basics; health promotion; surveillance; community engagement"),
        ("Epidemiologist", "disease surveillance", "epidemiology; biostatistics; outbreak investigation; data interpretation"),
        ("Health Records and Information Officer", "health information", "records management; health data coding; data privacy; reporting"),
        ("Health Informatics Specialist", "digital health", "health information systems; data standards; analytics; system support"),
        ("Biomedical Scientist", "biomedical research", "laboratory techniques; research design; data analysis; scientific writing"),
        ("Health Services Manager", "health administration", "service planning; budgeting; quality improvement; staff coordination"),
        ("Community Health Promoter", "community health", "health education; household visits; referral; behaviour change communication"),
    ],
    "Banking and Finance": [
        ("Accountant*", "financial accounting", "bookkeeping; financial reporting; reconciliation; accounting software"),
        ("Auditor*", "assurance and audit", "audit planning; internal controls; evidence gathering; report writing"),
        ("Financial Analyst", "financial analysis", "financial modelling; forecasting; spreadsheets; valuation basics"),
        ("Investment Analyst", "investment research", "equity research; portfolio analysis; financial modelling; market monitoring"),
        ("Banking Relationship Officer", "retail and corporate banking", "customer advisory; product knowledge; sales; account management"),
        ("Credit Analyst", "credit assessment", "credit scoring; financial statement analysis; risk assessment; loan structuring"),
        ("Risk Analyst", "enterprise risk", "risk assessment; data analysis; scenario analysis; reporting"),
        ("Actuarial Analyst*", "insurance and pensions modelling", "probability; statistics; actuarial modelling; spreadsheets"),
        ("Insurance Underwriter", "insurance underwriting", "risk evaluation; policy pricing; claims awareness; documentation"),
        ("Tax Consultant", "taxation", "tax law basics; tax computation; compliance filing; client advisory"),
        ("Treasury Officer", "treasury operations", "cash management; foreign exchange basics; liquidity planning; financial controls"),
        ("Fintech Product Analyst", "digital financial services", "payments knowledge; product analytics; customer research; regulatory awareness"),
        ("Compliance Officer", "financial compliance", "regulatory knowledge; policy review; monitoring; investigation support"),
        ("Microfinance Officer", "inclusive finance", "client assessment; loan monitoring; group lending; financial literacy training"),
        ("Securities Dealer*", "capital markets", "market knowledge; trade execution; client advisory; regulatory compliance"),
        ("Financial Planner", "personal finance", "financial planning; investment basics; client advisory; budgeting"),
        ("Forensic Accountant", "financial investigation", "fraud detection; audit techniques; data analysis; evidence documentation"),
        ("Mobile Money and Payments Specialist", "payment systems", "payment systems; reconciliation; agent network support; fraud monitoring"),
    ],
    "Business and Entrepreneurship": [
        ("Marketing Executive", "marketing", "campaign planning; market research; copywriting; marketing analytics"),
        ("Digital Marketing Specialist", "digital marketing", "SEO; social media advertising; analytics; content planning"),
        ("Brand Manager", "brand management", "brand strategy; market research; campaign management; stakeholder coordination"),
        ("Sales Executive", "sales", "prospecting; negotiation; CRM tools; closing deals"),
        ("Business Development Officer", "business growth", "market scanning; partnership building; proposal writing; negotiation"),
        ("Entrepreneur and Startup Founder", "venture building", "opportunity identification; business modelling; fundraising basics; resilience"),
        ("Business Analyst", "business analysis", "requirements gathering; process mapping; data analysis; stakeholder communication"),
        ("Human Resource Officer", "human resources", "recruitment support; employee relations; HR records; labour law awareness"),
        ("Talent Acquisition Specialist", "recruitment", "candidate sourcing; interviewing; employer branding; applicant tracking systems"),
        ("Customer Experience Manager", "customer experience", "customer research; service design; complaint resolution; metrics tracking"),
        ("Management Consultant", "advisory services", "structured problem solving; presentation; research; client management"),
        ("Market Research Analyst", "market research", "survey design; data analysis; segmentation; reporting"),
        ("Project Manager", "project delivery", "project planning; risk management; stakeholder management; budgeting"),
        ("E-commerce Manager", "online retail", "online storefronts; digital advertising; inventory coordination; conversion analytics"),
        ("Public Relations Officer", "corporate communication", "media relations; press writing; reputation management; event coordination"),
        ("Retail Manager", "retail operations", "store operations; staff supervision; merchandising; inventory control"),
        ("Corporate Strategy Analyst", "strategy", "market analysis; financial analysis; strategic planning; presentation"),
        ("Social Enterprise Manager", "social enterprise", "impact measurement; business modelling; partnership building; funding"),
    ],
    "Law and Governance": [
        ("Advocate*", "litigation and advisory", "legal research; legal drafting; advocacy; client advisory"),
        ("Corporate Lawyer*", "corporate and commercial law", "contract drafting; due diligence; company law; negotiation"),
        ("Legal Officer", "in-house legal support", "legal research; contract review; compliance support; documentation"),
        ("Paralegal", "legal support", "case file preparation; legal research; document drafting; court procedures"),
        ("Judicial Officer*", "judicial service", "legal analysis; impartial judgment; case management; court procedure"),
        ("State Counsel*", "public legal service", "legal drafting; litigation support; government law; advisory"),
        ("Compliance and Regulatory Officer", "regulatory compliance", "regulatory knowledge; policy review; audit support; reporting"),
        ("Human Rights Officer", "human rights", "human rights law; monitoring; report writing; advocacy"),
        ("Legal Researcher", "legal research", "case law research; statutory interpretation; academic writing; summarisation"),
        ("Contracts Manager", "contract management", "contract drafting; negotiation; risk assessment; vendor management"),
        ("Mediator and Arbitrator", "dispute resolution", "mediation; negotiation; active listening; neutral decision-making"),
        ("Intellectual Property Specialist", "intellectual property", "IP law; trademark and patent searches; licensing; documentation"),
        ("Conveyancing Officer", "property law", "land law; title searches; document drafting; registry procedures"),
        ("Company Secretary*", "corporate governance", "company law; board administration; governance; regulatory filings"),
        ("Legislative Drafter", "law-making support", "legal drafting; legislative procedure; policy analysis; precision writing"),
        ("Elections and Governance Officer", "democratic governance", "electoral procedures; civic education; monitoring; report writing"),
    ],
    "Education and Teaching": [
        ("Primary School Teacher*", "primary education", "lesson planning; classroom management; literacy teaching; assessment"),
        ("Secondary School Teacher*", "secondary education", "subject expertise; lesson planning; classroom management; assessment"),
        ("Early Childhood Educator", "early years", "child development; play-based learning; safeguarding; parent communication"),
        ("Special Needs Educator*", "inclusive education", "individual learning plans; assistive tools; behaviour support; parent collaboration"),
        ("University Lecturer", "higher education", "subject expertise; lecturing; research supervision; assessment design"),
        ("Education Officer", "education administration", "policy implementation; school inspection; report writing; stakeholder liaison"),
        ("Curriculum Developer", "curriculum design", "learning outcomes design; content development; assessment alignment; research"),
        ("Instructional Designer", "learning design", "learning design; content authoring tools; storyboarding; evaluation"),
        ("School Counsellor*", "learner guidance", "counselling skills; career guidance; case recording; referral"),
        ("Educational Technologist", "learning technology", "learning platforms; digital content; teacher training; data use"),
        ("TVET Trainer", "technical and vocational training", "practical demonstration; competency assessment; workshop safety; curriculum delivery"),
        ("Librarian and Information Officer", "library services", "cataloguing; information retrieval; digital resources; user support"),
        ("School Head and Administrator", "school leadership", "leadership; school budgeting; staff management; community engagement"),
        ("Language Teacher", "language teaching", "language instruction; communication; cultural awareness; assessment"),
        ("Adult Education Facilitator", "adult and community learning", "facilitation; literacy instruction; needs assessment; community engagement"),
        ("Corporate Trainer", "workplace learning", "training needs analysis; facilitation; presentation; evaluation"),
        ("Learning Coach and Tutor", "learner support", "one-to-one tutoring; study skills; progress tracking; encouragement"),
    ],
    "Agriculture and Environment": [
        ("Agronomist", "crop production", "crop science; soil management; pest management; field trials"),
        ("Agricultural Extension Officer", "farmer advisory", "farmer training; crop and livestock advice; demonstration; reporting"),
        ("Agribusiness Manager", "agricultural value chains", "farm budgeting; market linkage; supply chain coordination; negotiation"),
        ("Veterinary Doctor*", "animal health", "animal diagnosis; treatment; disease control; animal welfare"),
        ("Animal Health Technician", "livestock health support", "vaccination; animal handling; disease surveillance; record keeping"),
        ("Horticulturist", "fruits, vegetables and flowers", "crop propagation; greenhouse management; post-harvest handling; pest control"),
        ("Soil Scientist", "soil and land management", "soil sampling; laboratory analysis; fertiliser planning; land assessment"),
        ("Food Scientist", "food processing", "food chemistry; product development; quality testing; food safety"),
        ("Food Safety Officer", "food safety and inspection", "food safety standards; inspection; hazard analysis; audit reporting"),
        ("Fisheries and Aquaculture Officer", "aquatic resources", "fish farming; stock assessment; water quality; extension services"),
        ("Forestry Officer", "forests and tree resources", "forest management; tree nursery; conservation; resource monitoring"),
        ("Environmental Consultant", "environmental advisory", "environmental assessment; regulatory knowledge; field survey; report writing"),
        ("Climate Change Analyst", "climate adaptation", "climate data analysis; vulnerability assessment; policy review; communication"),
        ("Wildlife Conservation Officer", "conservation", "wildlife monitoring; field survey; community engagement; data recording"),
        ("Water Resources Officer", "water resources", "hydrology basics; water quality monitoring; resource planning; stakeholder engagement"),
        ("Agricultural Economist", "agricultural economics", "economic analysis; survey design; statistics; policy analysis"),
        ("Precision Agriculture Technician", "agricultural technology", "drones and sensors; GIS basics; data collection; equipment maintenance"),
        ("Waste Management Officer", "solid and liquid waste", "waste regulations; recycling systems; site supervision; community awareness"),
    ],
    "Media and Creative Industries": [
        ("Journalist", "news reporting", "reporting; interviewing; fact checking; news writing"),
        ("Broadcast Presenter", "radio and television", "voice delivery; scripting; interviewing; live production"),
        ("Video Producer", "video production", "video editing; camera operation; storyboarding; production planning"),
        ("Film Director", "film and drama", "storytelling; directing; script analysis; team leadership"),
        ("Graphic Designer", "visual design", "layout design; typography; design software; brand identity"),
        ("Animator", "animation", "motion design; storyboarding; 2D and 3D software; visual storytelling"),
        ("Photographer", "photography", "camera technique; lighting; photo editing; visual composition"),
        ("Content Creator", "digital content", "content planning; video and audio editing; audience growth; scripting"),
        ("Copywriter", "persuasive writing", "copywriting; editing; brand voice; research"),
        ("Editor", "editorial", "editing; proofreading; story selection; style guides"),
        ("Communications Officer", "organisational communication", "writing; media relations; social media; event coordination"),
        ("Social Media Manager", "social media", "content calendars; community management; analytics; paid campaigns"),
        ("Sound Engineer", "audio engineering", "audio recording; mixing; equipment setup; acoustics"),
        ("Music Producer", "music production", "music composition; digital audio workstations; arrangement; mixing"),
        ("Game Developer", "game development", "game engines; programming; game design; asset integration"),
        ("Fashion Designer", "fashion and textiles", "sketching; pattern making; fabric knowledge; trend research"),
        ("Interior Designer", "interior design", "space planning; CAD; materials knowledge; client briefing"),
        ("Illustrator", "illustration", "drawing; digital illustration tools; visual storytelling; client briefs"),
        ("Creative Director", "creative leadership", "creative strategy; team leadership; concept development; client presentation"),
    ],
    "Tourism and Hospitality": [
        ("Hotel Manager", "hotel operations", "hotel operations; revenue awareness; staff management; guest relations"),
        ("Front Office Officer", "guest reception", "reservations; guest check-in; communication; hospitality software"),
        ("Chef", "culinary arts", "food preparation; menu planning; kitchen hygiene; cost control"),
        ("Pastry Chef", "baking and pastry", "baking; dessert design; food hygiene; production planning"),
        ("Food and Beverage Manager", "food and beverage service", "service operations; inventory control; staff supervision; cost control"),
        ("Tour Operator", "tour packages", "itinerary design; supplier negotiation; costing; customer service"),
        ("Tour Guide", "guided experiences", "storytelling; local knowledge; group management; first aid awareness"),
        ("Travel Consultant", "travel advisory", "booking systems; itinerary planning; customer advisory; destination knowledge"),
        ("Events Planner", "events", "event planning; vendor management; budgeting; on-site coordination"),
        ("Conference and Meetings Coordinator", "conferences", "logistics planning; registration; stakeholder coordination; budgeting"),
        ("Revenue Manager", "hospitality revenue", "pricing; demand forecasting; analytics; distribution channels"),
        ("Safari Lodge Manager", "lodge and camp operations", "lodge operations; guest experience; staff supervision; conservation awareness"),
        ("Cabin Crew Member", "air travel service", "passenger safety; customer service; emergency procedures; teamwork"),
        ("Ground Handling Officer", "airport operations", "passenger processing; baggage handling; safety procedures; coordination"),
        ("Restaurant Manager", "restaurant operations", "service quality; staff scheduling; inventory control; guest relations"),
        ("Barista and Coffee Specialist", "specialty coffee", "coffee preparation; sensory evaluation; equipment care; customer service"),
        ("Housekeeping Manager", "accommodation services", "housekeeping standards; staff supervision; inventory control; quality inspection"),
        ("Tourism Marketing Officer", "destination marketing", "destination marketing; digital content; partnerships; campaign analytics"),
        ("Cultural Heritage Officer", "heritage tourism", "heritage interpretation; research; community engagement; exhibition support"),
    ],
    "Science and Research": [
        ("Research Scientist", "scientific research", "research design; data analysis; scientific writing; laboratory techniques"),
        ("Laboratory Technician", "laboratory operations", "sample preparation; instrument operation; record keeping; laboratory safety"),
        ("Chemist", "chemistry", "analytical chemistry; instrumentation; safety procedures; data interpretation"),
        ("Biologist", "biological sciences", "field and laboratory methods; data analysis; specimen handling; scientific writing"),
        ("Microbiologist", "microbiology", "culture techniques; aseptic technique; laboratory analysis; biosafety"),
        ("Biotechnologist", "biotechnology", "molecular biology techniques; cell culture; bioprocess basics; data analysis"),
        ("Physicist", "physics", "mathematical modelling; experimental methods; data analysis; programming"),
        ("Statistician", "statistics", "statistical modelling; sampling; data analysis; statistical software"),
        ("Mathematician", "mathematics", "mathematical modelling; proof and reasoning; computation; problem solving"),
        ("Geologist", "earth sciences", "field mapping; rock and mineral identification; geological data analysis; report writing"),
        ("Meteorologist", "weather and climate", "weather analysis; forecasting; atmospheric data; communication"),
        ("Bioinformatician", "computational biology", "Python or R; sequence analysis; statistics; biological databases"),
        ("Research Assistant", "research support", "literature review; data collection; data entry; reporting"),
        ("Science Communicator", "science communication", "plain-language writing; presentation; research; public engagement"),
        ("Materials Scientist", "materials research", "materials characterisation; experimental design; data analysis; technical writing"),
        ("Forensic Scientist", "forensic analysis", "evidence handling; laboratory analysis; documentation; court reporting"),
        ("Marine Scientist", "marine and aquatic science", "field sampling; marine ecology; data analysis; research reporting"),
        ("Quality Control Analyst", "laboratory quality control", "analytical testing; quality standards; documentation; instrument calibration"),
        ("Clinical Research Associate", "clinical trials", "trial protocols; good clinical practice; data monitoring; documentation"),
    ],
    "Logistics and Operations": [
        ("Logistics Coordinator", "logistics coordination", "shipment tracking; documentation; carrier coordination; inventory awareness"),
        ("Supply Chain Analyst", "supply chain planning", "data analysis; demand forecasting; inventory optimisation; spreadsheets"),
        ("Procurement Officer", "procurement", "sourcing; tender evaluation; supplier negotiation; contract management"),
        ("Warehouse Manager", "warehousing", "inventory control; warehouse safety; staff supervision; warehouse systems"),
        ("Clearing and Forwarding Agent", "freight and customs", "customs procedures; documentation; freight coordination; client communication"),
        ("Customs Officer", "customs control", "customs regulations; inspection; documentation; risk profiling"),
        ("Operations Manager", "operations management", "process management; staff leadership; budgeting; performance monitoring"),
        ("Fleet Manager", "fleet operations", "fleet scheduling; vehicle maintenance planning; route optimisation; compliance"),
        ("Commercial Pilot*", "aviation", "flight operations; navigation; aviation safety; decision-making"),
        ("Air Traffic Controller*", "air traffic services", "airspace management; communication; situational awareness; safety procedures"),
        ("Aircraft Maintenance Engineer*", "aircraft maintenance", "aircraft systems; inspection; maintenance records; safety compliance"),
        ("Marine Officer*", "maritime operations", "navigation; vessel safety; cargo operations; maritime regulations"),
        ("Railway Operations Officer", "rail operations", "train scheduling; safety procedures; control systems; incident response"),
        ("Inventory Planner", "inventory planning", "stock analysis; forecasting; replenishment planning; ERP tools"),
        ("Demand Planner", "demand planning", "demand forecasting; statistics; sales analysis; planning tools"),
        ("Last-Mile Delivery Manager", "delivery operations", "route planning; rider coordination; customer communication; delivery metrics"),
        ("Port Operations Officer", "port and terminal operations", "cargo handling; port regulations; coordination; safety management"),
        ("Production Planner", "production scheduling", "production scheduling; capacity planning; materials planning; ERP tools"),
        ("Transport Planner", "transport systems", "transport modelling; data analysis; policy review; stakeholder consultation"),
    ],
    "Social and Community Services": [
        ("Social Worker*", "social work", "case management; assessment; counselling skills; referral"),
        ("Community Development Officer", "community development", "community mobilisation; participatory methods; project support; reporting"),
        ("Youth Worker", "youth development", "youth engagement; mentoring; programme delivery; safeguarding"),
        ("Counsellor*", "counselling", "active listening; counselling techniques; confidentiality; case notes"),
        ("Child Protection Officer", "child protection", "safeguarding; case management; child rights; multi-agency coordination"),
        ("NGO Programme Officer", "programme management", "programme planning; donor reporting; budgeting; stakeholder coordination"),
        ("Monitoring and Evaluation Officer", "monitoring and evaluation", "indicator design; data collection; data analysis; impact reporting"),
        ("Humanitarian Aid Worker", "humanitarian response", "needs assessment; logistics support; coordination; resilience"),
        ("Gender and Inclusion Officer", "gender and social inclusion", "gender analysis; training facilitation; policy review; community engagement"),
        ("Disability Inclusion Officer", "disability inclusion", "accessibility assessment; advocacy; training facilitation; stakeholder engagement"),
        ("Peacebuilding Officer", "peace and conflict", "conflict analysis; mediation; community dialogue; reporting"),
        ("Psychosocial Support Officer", "psychosocial support", "psychological first aid; active listening; group facilitation; referral"),
        ("Volunteer Coordinator", "volunteer management", "volunteer recruitment; scheduling; training; communication"),
        ("Fundraising Officer", "resource mobilisation", "proposal writing; donor research; relationship building; reporting"),
        ("Community Mobiliser", "community outreach", "community outreach; facilitation; local language communication; record keeping"),
        ("Refugee Protection Officer", "forced displacement", "protection assessment; case management; interviewing; international law awareness"),
        ("Probation Officer", "rehabilitation and reintegration", "case assessment; counselling skills; report writing; community liaison"),
        ("Sociologist", "social research", "research methods; social theory; qualitative analysis; report writing"),
    ],
    "Public Service and Development": [
        ("Public Administrator", "public administration", "public policy; administration; report writing; stakeholder coordination"),
        ("Public Policy Analyst", "policy analysis", "policy research; data analysis; briefing writing; stakeholder consultation"),
        ("Economist", "economic analysis", "economic modelling; statistics; research; report writing"),
        ("Development Economist", "development economics", "impact evaluation; econometrics; survey analysis; policy writing"),
        ("County Government Officer", "devolved government", "county planning; public service delivery; budgeting; community engagement"),
        ("Diplomat and Foreign Service Officer", "foreign affairs", "diplomacy; negotiation; international relations; report writing"),
        ("Development Planning Officer", "development planning", "planning frameworks; data analysis; consultation; report writing"),
        ("Revenue Officer", "tax administration", "tax law basics; compliance auditing; taxpayer service; data analysis"),
        ("Immigration Officer", "border and immigration services", "document verification; immigration law; interviewing; risk screening"),
        ("Development Project Coordinator", "development projects", "project coordination; donor reporting; budget tracking; stakeholder management"),
        ("International Relations Analyst", "international affairs", "geopolitical analysis; research; briefing writing; languages"),
        ("Trade Policy Analyst", "trade and regional integration", "trade policy; economic analysis; negotiation support; research"),
        ("Public Finance Officer", "public financial management", "budgeting; public financial regulations; financial reporting; internal controls"),
        ("Parliamentary Researcher", "legislative research", "legislative research; policy briefing; stakeholder analysis; writing"),
        ("Government Statistician", "official statistics", "survey methods; statistical analysis; data quality; reporting"),
        ("Grants Manager", "grants and funding", "grant management; compliance; budgeting; reporting"),
        ("Urban Development Officer", "urban development", "urban planning basics; project oversight; stakeholder engagement; policy review"),
        ("Disaster Risk Management Officer", "disaster preparedness", "risk assessment; emergency planning; coordination; community training"),
        ("ICT Policy Officer", "digital government", "digital policy; stakeholder consultation; data governance; report writing"),
    ],
    "Energy, Manufacturing and Skilled Trades": [
        ("Solar PV Technician", "solar energy", "solar installation; electrical safety; system testing; customer support"),
        ("Renewable Energy Engineer*", "renewable energy systems", "energy system design; solar and wind systems; energy modelling; project coordination"),
        ("Power Systems Engineer*", "power transmission and distribution", "power system analysis; protection systems; load flow; electrical safety"),
        ("Petroleum Engineer*", "oil and gas", "reservoir basics; drilling fundamentals; production optimisation; safety management"),
        ("Geothermal Technician", "geothermal energy", "plant operation; instrumentation; maintenance; safety procedures"),
        ("Electrician*", "electrical installation", "wiring; electrical testing; electrical safety; fault finding"),
        ("Plumber", "plumbing and pipework", "pipe installation; blueprint reading; fault finding; safety procedures"),
        ("Welder and Fabricator", "metal fabrication", "welding techniques; blueprint reading; metal cutting; safety procedures"),
        ("Automotive Technician", "vehicle maintenance", "engine diagnostics; electrical systems; repair; customer service"),
        ("Diesel and Heavy Equipment Mechanic", "heavy equipment", "diesel engines; hydraulics; maintenance schedules; fault diagnosis"),
        ("Manufacturing Engineer", "manufacturing processes", "process design; lean methods; quality systems; equipment improvement"),
        ("Production Supervisor", "factory operations", "team supervision; production planning; quality monitoring; safety management"),
        ("Quality Control Inspector", "manufacturing quality", "inspection techniques; measuring instruments; quality standards; documentation"),
        ("Industrial Maintenance Technician", "plant maintenance", "preventive maintenance; mechanical repair; electrical basics; troubleshooting"),
        ("Mining Engineer*", "mining operations", "mine planning; geology basics; safety management; equipment selection"),
        ("Carpenter and Joiner", "woodwork", "measuring and cutting; joinery; blueprint reading; finishing"),
        ("Refrigeration and Air-Conditioning Technician", "cooling systems", "refrigeration cycles; installation; fault finding; safety procedures"),
        ("Textile and Garment Technologist", "textiles and apparel", "fabric technology; production planning; quality control; pattern knowledge"),
        ("Instrumentation Technician", "industrial instrumentation", "sensors and calibration; control loops; electrical basics; troubleshooting"),
        ("Occupational Health and Safety Officer", "workplace safety", "hazard identification; safety inspection; incident investigation; safety training"),
        ("Energy Auditor", "energy efficiency", "energy measurement; data analysis; efficiency recommendations; report writing"),
        ("CNC Machinist", "precision machining", "CNC programming; blueprint reading; precision measuring; machine setup"),
    ],
}

# Second wave of roles. These are numbered after every CATALOGUE role so that
# existing career_id values never change when the catalogue grows. Add new roles
# to the END of a list here (or in a later wave) rather than inserting them.
EXTENDED_CATALOGUE = {
    "Technology and Data": [
        ("Site Reliability Engineer", "service reliability", "monitoring; incident response; automation; Linux"),
        ("Solutions Architect", "systems architecture", "architecture design; cloud platforms; integration patterns; technical communication"),
        ("Business Intelligence Developer", "reporting and dashboards", "SQL; dashboard tools; data modelling; requirements analysis"),
        ("Penetration Tester", "offensive security testing", "vulnerability assessment; ethical hacking tools; report writing; web security"),
        ("Blockchain Developer", "distributed ledgers", "smart contracts; cryptography basics; programming; security testing"),
        ("Natural Language Processing Engineer", "language AI", "Python; text processing; transformer models; evaluation methods"),
        ("Computer Vision Engineer", "image and video AI", "Python; image processing; deep learning; model optimisation"),
        ("IT Project Manager", "technology delivery", "project planning; agile methods; risk management; vendor coordination"),
        ("ERP Consultant", "enterprise systems", "ERP configuration; business process analysis; user training; data migration"),
        ("Data Protection Officer", "privacy compliance", "data protection law; privacy impact assessment; policy writing; audit"),
        ("IT Auditor", "technology assurance", "IT controls; audit methodology; risk assessment; report writing"),
        ("Technical Writer", "technical documentation", "documentation; API writing; information design; editing"),
    ],
    "Engineering and Built Environment": [
        ("Aerospace Engineer", "aircraft and space systems", "aerodynamics; structural analysis; propulsion basics; simulation"),
        ("Agricultural Engineer*", "farm machinery and irrigation", "irrigation design; farm machinery; soil and water engineering; project planning"),
        ("Marine Engineer", "ship systems", "marine engines; maintenance planning; safety systems; fault diagnosis"),
        ("Geotechnical Engineer*", "soils and foundations", "soil mechanics; site investigation; foundation design; laboratory testing"),
        ("Highway and Transport Engineer*", "roads and transport infrastructure", "road design; traffic analysis; pavement materials; surveying"),
        ("Telecommunications Network Planner", "network planning", "radio planning; fibre networks; capacity analysis; planning tools"),
        ("Robotics Engineer", "robotics", "robot programming; control systems; mechanical design; sensor integration"),
        ("Fire Safety Engineer", "fire protection", "fire risk assessment; suppression systems; building codes; safety audits"),
        ("Materials Engineer", "engineering materials", "materials testing; failure analysis; metallurgy basics; quality standards"),
        ("Landscape Architect*", "outdoor space design", "landscape design; planting knowledge; CAD; site analysis"),
        ("Facilities Manager", "building operations", "maintenance planning; vendor management; budgeting; safety compliance"),
    ],
    "Health and Medicine": [
        ("Surgeon*", "surgical care", "surgical technique; anatomy; decision-making; perioperative care"),
        ("Paediatrician*", "child health", "child assessment; growth monitoring; family communication; clinical management"),
        ("Midwife*", "maternal and newborn care", "antenatal care; safe delivery; newborn care; health education"),
        ("Optometrist*", "eye care", "eye examination; refraction; patient counselling; referral"),
        ("Pharmaceutical Technologist*", "pharmacy practice support", "dispensing; stock control; medication counselling; record keeping"),
        ("Dental Technologist", "dental laboratory", "dental prosthetics; laboratory techniques; materials handling; precision work"),
        ("Orthopaedic Technologist", "orthopaedic devices", "casting and splinting; prosthetics basics; patient handling; measurement"),
        ("Speech and Language Therapist", "communication disorders", "speech assessment; therapy planning; family coaching; documentation"),
        ("Emergency Medical Technician", "pre-hospital care", "first response; patient stabilisation; triage; ambulance procedures"),
        ("Health Economist", "health financing", "economic evaluation; statistics; health systems knowledge; report writing"),
        ("Medical Social Worker", "hospital social services", "psychosocial assessment; counselling skills; discharge planning; referral"),
        ("Medical Sales Representative", "healthcare products", "product knowledge; relationship building; presentation; territory planning"),
    ],
    "Banking and Finance": [
        ("Bank Operations Officer", "branch and back-office operations", "transaction processing; reconciliation; customer service; controls"),
        ("Financial Controller", "finance leadership", "financial reporting; budgeting; internal controls; team leadership"),
        ("Pension Fund Administrator", "retirement benefits", "member records; benefits calculation; regulatory compliance; reporting"),
        ("Insurance Claims Analyst", "claims", "claims assessment; investigation; policy interpretation; customer communication"),
        ("Islamic Finance Specialist", "Sharia-compliant finance", "Islamic finance principles; product structuring; compliance; client advisory"),
        ("SACCO Manager", "co-operative finance", "credit management; member services; financial reporting; governance"),
        ("Equity Trader", "securities trading", "market analysis; trade execution; risk management; quick decision-making"),
        ("Budget Analyst", "budgeting", "budget preparation; variance analysis; spreadsheets; reporting"),
        ("Anti-Money Laundering Analyst", "financial crime", "transaction monitoring; customer due diligence; investigation; regulatory reporting"),
        ("Cost Accountant", "cost and management accounting", "cost analysis; budgeting; inventory valuation; management reporting"),
        ("Venture Capital Analyst", "startup investment", "deal sourcing; financial modelling; market research; due diligence"),
    ],
    "Business and Entrepreneurship": [
        ("Real Estate Agent*", "property sales and letting", "property knowledge; negotiation; client advisory; marketing"),
        ("Property Manager", "property management", "tenant relations; maintenance coordination; rent collection; reporting"),
        ("Administrative Assistant", "office administration", "scheduling; records management; correspondence; office software"),
        ("Executive Assistant", "executive support", "calendar management; confidentiality; minute taking; travel coordination"),
        ("Customer Service Representative", "customer support", "active listening; complaint handling; product knowledge; CRM tools"),
        ("Call Centre Team Leader", "contact centre operations", "team coaching; performance monitoring; escalation handling; scheduling"),
        ("Innovation Manager", "innovation and new ventures", "design thinking; idea validation; portfolio management; facilitation"),
        ("Product Owner", "agile product delivery", "backlog management; user stories; stakeholder communication; prioritisation"),
        ("Growth Marketer", "growth experiments", "experimentation; funnel analytics; paid acquisition; email marketing"),
        ("Export Trade Officer", "international trade", "export documentation; trade regulations; market research; buyer relations"),
        ("Office Manager", "office operations", "office coordination; vendor management; budgeting; staff support"),
        ("Franchise and Distribution Manager", "distribution networks", "channel management; partner training; sales analysis; contract management"),
    ],
    "Law and Governance": [
        ("Prosecutor*", "criminal prosecution", "criminal law; evidence analysis; courtroom advocacy; case preparation"),
        ("Environmental Lawyer*", "environmental and land law", "environmental law; legal research; litigation; advisory"),
        ("Family Lawyer*", "family and succession law", "family law; mediation; legal drafting; client counselling"),
        ("Tax Lawyer*", "tax law", "tax legislation; dispute resolution; legal drafting; advisory"),
        ("Court Clerk", "court administration", "court procedures; records management; scheduling; public service"),
        ("Legal Aid Officer", "access to justice", "legal advice basics; client interviewing; community outreach; referral"),
        ("Data Privacy Counsel", "data protection law", "data protection law; contract review; compliance advisory; policy drafting"),
        ("Ombudsman Officer", "public complaints", "complaint investigation; administrative law; mediation; report writing"),
        ("Anti-Corruption Investigator", "integrity and ethics", "investigation; evidence gathering; interviewing; report writing"),
        ("Land Registrar", "land registration", "land law; registry procedures; document verification; records management"),
        ("Legal Technologist", "legal technology", "legal process knowledge; document automation; data analysis; tool configuration"),
    ],
    "Education and Teaching": [
        ("Examinations Officer", "assessment administration", "exam logistics; data accuracy; confidentiality; scheduling"),
        ("Education Researcher", "education research", "research methods; data analysis; academic writing; policy analysis"),
        ("Sports Coach and PE Teacher", "physical education", "coaching; fitness training; safety management; team building"),
        ("Music Teacher", "music education", "instrument instruction; music theory; performance preparation; lesson planning"),
        ("STEM Educator", "science and technology learning", "hands-on experiments; coding instruction; project-based learning; mentoring"),
        ("Sign Language Interpreter", "deaf education and access", "Kenyan Sign Language; interpreting; cultural awareness; confidentiality"),
        ("Quality Assurance and Standards Officer", "school standards", "school assessment; standards knowledge; report writing; advisory"),
        ("Dean of Students", "student affairs", "student welfare; discipline management; counselling skills; programme coordination"),
        ("E-learning Content Developer", "digital learning content", "content authoring tools; video production; instructional writing; learning platforms"),
        ("Career Guidance Officer", "career services", "career counselling; employer liaison; workshop facilitation; labour market awareness"),
        ("Admissions Officer", "student recruitment", "application review; outreach; records management; advising"),
    ],
    "Agriculture and Environment": [
        ("Dairy Technologist", "milk processing", "dairy processing; quality testing; hygiene standards; equipment operation"),
        ("Poultry Farm Manager", "poultry production", "flock management; biosecurity; feed planning; record keeping"),
        ("Apiculturist", "beekeeping", "hive management; honey processing; pollination knowledge; farmer training"),
        ("Irrigation Technician", "irrigation systems", "system installation; water scheduling; maintenance; field measurement"),
        ("Seed Technologist", "seed production", "seed testing; variety maintenance; certification procedures; laboratory analysis"),
        ("Range Management Officer", "rangelands and pastoral systems", "rangeland assessment; livestock systems; community engagement; drought planning"),
        ("Coffee and Tea Quality Controller", "beverage crop quality", "sensory evaluation; grading; processing knowledge; quality records"),
        ("Environmental Educator", "environmental awareness", "environmental knowledge; facilitation; programme design; community outreach"),
        ("Carbon Project Officer", "carbon markets", "carbon accounting; project monitoring; field data collection; reporting standards"),
        ("Plant Pathologist", "crop diseases", "disease diagnosis; laboratory techniques; field surveys; management advice"),
        ("Livestock Production Officer", "livestock systems", "animal nutrition; breeding; herd management; extension services"),
        ("Greenhouse Manager", "protected cultivation", "climate control; crop scheduling; pest management; staff supervision"),
    ],
    "Media and Creative Industries": [
        ("Documentary Filmmaker", "non-fiction film", "research; interviewing; cinematography; editing"),
        ("Screenwriter", "scripts for film and television", "story structure; dialogue writing; research; revision"),
        ("Radio Producer", "radio programming", "programme planning; audio editing; scripting; guest coordination"),
        ("Art Director", "visual direction", "visual concepts; layout; team direction; brand consistency"),
        ("UX Writer", "product language", "microcopy; user research; content design; editing"),
        ("Motion Graphics Designer", "animated graphics", "motion design software; typography; storyboarding; timing"),
        ("Voice-over Artist", "voice performance", "voice control; script interpretation; recording technique; self-direction"),
        ("Actor", "performance", "acting technique; script analysis; voice and movement; collaboration"),
        ("Dancer and Choreographer", "dance", "dance technique; choreography; rehearsal direction; physical conditioning"),
        ("Curator", "galleries and exhibitions", "art knowledge; exhibition planning; research; writing"),
        ("Translator and Interpreter", "language services", "translation; interpreting; subject research; cultural awareness"),
        ("Influencer Marketing Manager", "creator partnerships", "creator sourcing; campaign management; negotiation; performance analytics"),
    ],
    "Tourism and Hospitality": [
        ("Bartender and Mixologist", "beverage service", "drink preparation; product knowledge; customer service; stock control"),
        ("Airline Reservations Agent", "airline ticketing", "reservation systems; fare rules; customer service; problem resolution"),
        ("Spa and Wellness Manager", "wellness services", "spa operations; staff supervision; customer care; retail sales"),
        ("Ecotourism Officer", "sustainable tourism", "conservation knowledge; community partnerships; visitor management; interpretation"),
        ("Hotel Sales Manager", "hospitality sales", "account management; negotiation; proposal writing; market analysis"),
        ("Concierge", "guest services", "local knowledge; problem solving; guest relations; booking coordination"),
        ("Banqueting Manager", "banquets and functions", "event setup; staff coordination; menu knowledge; client liaison"),
        ("Wedding Planner", "weddings", "event design; vendor management; budgeting; client relations"),
        ("Sports and Recreation Officer", "leisure and recreation", "activity planning; safety management; coaching; facility coordination"),
        ("Catering Manager", "catering operations", "menu planning; food safety; cost control; team supervision"),
        ("Tourism Product Developer", "tourism experiences", "product design; market research; supplier partnerships; pricing"),
    ],
    "Science and Research": [
        ("Astronomer", "astronomy and space science", "astrophysics; data analysis; programming; scientific writing"),
        ("Environmental Scientist", "environmental science", "field sampling; laboratory analysis; data interpretation; reporting"),
        ("Toxicologist", "toxicology", "toxicity testing; laboratory techniques; risk assessment; documentation"),
        ("Geneticist", "genetics", "molecular techniques; genetic analysis; bioinformatics basics; research ethics"),
        ("Entomologist", "insect science", "insect identification; field surveys; laboratory rearing; data analysis"),
        ("Hydrologist", "water science", "hydrological modelling; field measurement; data analysis; GIS"),
        ("Pharmacologist", "drug science", "pharmacology; experimental design; laboratory techniques; data analysis"),
        ("Radiation Protection Officer", "radiation safety", "radiation monitoring; safety regulations; risk assessment; record keeping"),
        ("Laboratory Manager", "laboratory management", "laboratory quality systems; staff supervision; procurement; safety compliance"),
        ("Zoologist", "animal science", "animal behaviour; field surveys; specimen handling; data analysis"),
        ("Botanist", "plant science", "plant identification; field collection; herbarium methods; data analysis"),
        ("Research Data Manager", "research data", "data management; metadata standards; data privacy; database tools"),
    ],
    "Logistics and Operations": [
        ("Flight Dispatcher*", "flight operations planning", "flight planning; weather interpretation; regulations; communication"),
        ("Ship Agent", "vessel agency", "port documentation; vessel coordination; client communication; maritime procedures"),
        ("Cold Chain Specialist", "temperature-controlled logistics", "temperature monitoring; handling standards; route planning; quality checks"),
        ("Import and Export Officer", "cross-border trade", "trade documentation; customs procedures; shipping terms; supplier liaison"),
        ("Humanitarian Logistics Officer", "relief supply chains", "relief planning; warehouse management; transport coordination; reporting"),
        ("Stores Clerk", "stores and stock", "stock records; receiving and issuing; stock taking; filing"),
        ("Category Manager", "category procurement", "spend analysis; supplier strategy; negotiation; market intelligence"),
        ("Supplier Quality Engineer", "supplier quality", "supplier audits; quality standards; root cause analysis; corrective actions"),
        ("Drone Operations Pilot*", "unmanned aircraft operations", "drone piloting; flight planning; airspace rules; data capture"),
        ("Public Transport Operations Manager", "passenger transport", "route scheduling; fleet coordination; safety compliance; customer service"),
        ("Locomotive Driver", "train operation", "train handling; signalling knowledge; safety procedures; alertness"),
    ],
    "Social and Community Services": [
        ("Addiction Counsellor*", "substance use recovery", "counselling techniques; relapse prevention; group facilitation; referral"),
        ("Marriage and Family Therapist*", "family therapy", "family systems; counselling techniques; conflict resolution; confidentiality"),
        ("Geriatric Care Worker", "care for older people", "personal care; patience; health monitoring; family communication"),
        ("Rehabilitation Officer", "rehabilitation services", "needs assessment; rehabilitation planning; vocational support; case notes"),
        ("Safeguarding Adviser", "safeguarding", "safeguarding policy; risk assessment; training facilitation; incident management"),
        ("Chaplain", "pastoral care", "pastoral counselling; active listening; ethics; group facilitation"),
        ("Advocacy Officer", "policy advocacy", "campaign planning; policy analysis; coalition building; public speaking"),
        ("Livelihoods Officer", "economic empowerment", "livelihood assessment; savings groups; business skills training; monitoring"),
        ("Cash Transfer Programme Officer", "social protection", "beneficiary targeting; payment systems; grievance handling; data management"),
        ("Research and Learning Officer", "programme learning", "qualitative research; data analysis; documentation; knowledge sharing"),
        ("Children's Home Manager", "residential child care", "child care standards; staff supervision; safeguarding; budgeting"),
    ],
    "Public Service and Development": [
        ("Police Officer", "law enforcement", "law enforcement procedures; investigation basics; community policing; physical fitness"),
        ("Military Officer", "defence service", "leadership; discipline; tactical planning; physical fitness"),
        ("Intelligence Analyst", "security analysis", "information analysis; research; report writing; discretion"),
        ("Prisons Officer", "correctional services", "custodial procedures; rehabilitation support; security awareness; record keeping"),
        ("Fire and Rescue Officer", "emergency response", "firefighting; rescue techniques; first aid; equipment handling"),
        ("National Government Administration Officer", "local administration", "public administration; conflict resolution; community coordination; reporting"),
        ("Public Auditor", "public sector audit", "public sector auditing; financial regulations; evidence gathering; report writing"),
        ("Public Procurement Officer", "government procurement", "procurement law; tender management; evaluation; records management"),
        ("Lands Officer", "land administration", "land administration; valuation basics; records management; dispute handling"),
        ("Labour Officer", "labour administration", "labour law; workplace inspection; dispute conciliation; reporting"),
        ("Consular Officer", "consular services", "consular procedures; document processing; citizen assistance; communication"),
        ("Records and Archives Officer", "public records", "records classification; archiving; digitisation; access procedures"),
    ],
    "Energy, Manufacturing and Skilled Trades": [
        ("Mason", "masonry and concrete work", "bricklaying; concrete work; measurement; blueprint reading"),
        ("Painter and Decorator", "painting and finishing", "surface preparation; paint application; colour matching; estimating"),
        ("Tailor and Dressmaker", "garment making", "pattern cutting; sewing; fitting; fabric knowledge"),
        ("Hairdresser and Beauty Therapist", "hair and beauty services", "hair styling; skin care; hygiene standards; customer care"),
        ("Electrical Lines Technician", "power line construction", "line construction; climbing safety; electrical safety; fault repair"),
        ("Wind Turbine Technician", "wind energy", "turbine maintenance; mechanical repair; electrical basics; working at height"),
        ("Biogas Technician", "biogas systems", "digester construction; gas piping; maintenance; user training"),
        ("Boiler Operator", "steam systems", "boiler operation; pressure monitoring; water treatment; safety procedures"),
        ("Process Plant Operator", "process plants", "plant monitoring; control room operation; sampling; safety procedures"),
        ("Leather Technologist", "leather and footwear", "tanning processes; quality control; product development; chemical handling"),
        ("Motorcycle Mechanic", "motorcycle repair", "engine repair; electrical diagnosis; servicing; customer service"),
        ("Mobile Phone Repair Technician", "device repair", "fault diagnosis; soldering; software flashing; customer service"),
        ("Lift Technician", "lifts and escalators", "lift installation; electrical testing; preventive maintenance; safety procedures"),
        ("Crane and Plant Operator", "heavy plant operation", "equipment operation; load handling; daily inspection; site safety"),
        ("Electric Vehicle and Battery Technician", "electric mobility", "battery systems; high-voltage safety; diagnostics; charging equipment"),
    ],
}

CATALOG_COLUMNS = [
    "career_id", "category", "role_title", "specialisation", "description",
    "commonly_regulated", "market_scope", "opportunity_types", "description_status",
    "data_origin", "is_synthetic", "evidence_status",
]
SKILL_COLUMNS = ["career_id", "skill", "skill_type", "importance", "data_origin", "is_synthetic"]


def _clean_title(raw: str) -> tuple[str, bool]:
    regulated = raw.endswith("*")
    return raw.rstrip("*").strip(), regulated


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def build_rows() -> tuple[list[dict], list[dict]]:
    catalog: list[dict] = []
    skills: list[dict] = []
    counter = 0
    # Base roles first, then the extended wave, so earlier career_id values stay stable.
    ordered_roles = [
        (category, role)
        for wave in (CATALOGUE, EXTENDED_CATALOGUE)
        for category in CATEGORIES
        for role in wave.get(category, [])
    ]
    for category, (raw_title, focus, skill_text) in ordered_roles:
        phrase, preferred = CATEGORIES[category]
        if True:  # keeps the role block at one indentation level
            counter += 1
            career_id = f"CAREER-{counter:03d}"
            title, regulated = _clean_title(raw_title)
            core = [s.strip() for s in skill_text.split(";") if s.strip()]
            description = (
                f"{title} is a role in {phrase}, focused on {focus}. "
                f"Day-to-day work typically draws on {_join(core[:3])}. "
                "This draft description is illustrative; confirm current duties and entry requirements "
                "with employers and the relevant professional bodies."
            )
            catalog.append({
                "career_id": career_id,
                "category": category,
                "role_title": title,
                "specialisation": focus,
                "description": description,
                "commonly_regulated": "yes" if regulated else "no",
                "market_scope": MARKET_SCOPE,
                "opportunity_types": OPPORTUNITY_TYPES,
                "description_status": DESCRIPTION_STATUS,
                "data_origin": DATA_ORIGIN,
                "is_synthetic": "true",
                "evidence_status": EVIDENCE_STATUS,
            })
            seen: set[str] = set()

            def add(skill: str, skill_type: str, importance: int) -> None:
                key = skill.casefold()
                if key in seen:
                    return
                seen.add(key)
                skills.append({
                    "career_id": career_id, "skill": skill, "skill_type": skill_type,
                    "importance": importance, "data_origin": DATA_ORIGIN, "is_synthetic": "true",
                })

            for position, skill in enumerate(core):
                add(skill, "core", 5 if position < 2 else 4)
            for skill in preferred:
                add(skill, "preferred", 3)
            for skill in TRANSFERABLE_SKILLS:
                add(skill, "transferable", 2)
    return catalog, skills


def validate(catalog: list[dict], skills: list[dict]) -> None:
    ids = [row["career_id"] for row in catalog]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate career_id values")
    titles = Counter((row["category"], row["role_title"].casefold()) for row in catalog)
    duplicates = [key for key, count in titles.items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate role titles within a category: {duplicates}")
    unknown = {row["career_id"] for row in skills} - set(ids)
    if unknown:
        raise ValueError(f"Skills reference unknown career_id values: {sorted(unknown)[:5]}")
    for row in catalog:
        if row["category"] not in CATEGORIES:
            raise ValueError(f"Unknown category: {row['category']}")
    core_counts = Counter(row["career_id"] for row in skills if row["skill_type"] == "core")
    missing_core = [career_id for career_id in ids if core_counts[career_id] < 3]
    if missing_core:
        raise ValueError(f"Roles with fewer than three core skills: {missing_core[:5]}")


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--check", action="store_true", help="Validate the generated tables without writing files.")
    args = parser.parse_args()

    catalog, skills = build_rows()
    validate(catalog, skills)
    by_category = Counter(row["category"] for row in catalog)
    summary = {
        "career_roles": len(catalog),
        "skill_rows": len(skills),
        "categories": len(by_category),
        "roles_per_category": dict(by_category),
        "commonly_regulated_roles": sum(row["commonly_regulated"] == "yes" for row in catalog),
        "data_origin": DATA_ORIGIN,
        "evidence_status": EVIDENCE_STATUS,
    }
    if args.check:
        print(json.dumps(summary, indent=2))
        print("Validation passed; no files written.")
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "career_catalog.csv", CATALOG_COLUMNS, catalog)
    write_csv(args.output_dir / "career_skills.csv", SKILL_COLUMNS, skills)
    (args.output_dir / "catalogue_manifest.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(catalog)} roles and {len(skills)} skill rows to {args.output_dir}")


if __name__ == "__main__":
    main()
