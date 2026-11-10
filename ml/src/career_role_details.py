"""Hand-written detail for individual career roles.

ROLE_DETAILS maps a catalogue role title to four semicolon-separated lists:

  (alternative job titles, specialisms within the role, day-to-day tasks, tools and technologies)

Roles not listed here still get titles, tasks and tools from their category's
defaults in build_career_details.py, and are marked `category_default` there so
authored and templated detail can always be told apart.

Like the rest of the catalogue this is illustrative guidance. Job titles and
tools vary between employers and countries.
"""

ROLE_DETAILS = {
    # ---- Technology and Data ----
    "Software Developer": (
        "Software Engineer; Programmer; Application Developer; Backend Developer; Full-Stack Developer; Systems Developer",
        "backend services; frontend applications; full-stack development; API development; desktop applications; payments and fintech systems",
        "write and review code; design features with teammates; fix defects reported by users; write automated tests; deploy releases; document how the system works; estimate and plan work in sprints",
        "Git; an IDE such as IntelliJ or VS Code; issue trackers; CI pipelines; relational databases; REST APIs",
    ),
    "Mobile Application Developer": (
        "Android Developer; iOS Developer; Mobile Engineer; App Developer; Cross-Platform Developer; Flutter Developer",
        "native Android; native iOS; cross-platform apps; mobile payments integration; offline-first apps; mobile games",
        "build screens and navigation; connect the app to backend APIs; handle offline storage and sync; test on real devices; publish releases to app stores; fix crashes from user reports; optimise for low-end phones and slow networks",
        "Android Studio; Kotlin; Jetpack Compose; Xcode and Swift; Flutter; Firebase; Git",
    ),
    "Web Developer": (
        "Frontend Developer; Web Engineer; Full-Stack Web Developer; WordPress Developer; UI Developer; JavaScript Developer",
        "frontend interfaces; content management sites; e-commerce sites; web applications; web accessibility; performance optimisation",
        "build responsive pages; turn designs into working interfaces; connect pages to APIs; fix cross-browser problems; improve page speed; maintain and update live sites; apply basic security practices",
        "HTML and CSS; JavaScript and TypeScript; React or Vue; Node.js; browser developer tools; Git; WordPress",
    ),
    "Data Analyst": (
        "Business Data Analyst; Reporting Analyst; Insights Analyst; Analytics Associate; Operations Analyst; Research Analyst",
        "sales and marketing analytics; financial reporting; operations analytics; survey analysis; customer analytics; public-sector data",
        "clean and combine data; write queries to answer business questions; build dashboards and reports; spot trends and anomalies; present findings to non-technical colleagues; check data quality; document definitions",
        "SQL; Excel; Power BI or Tableau; Python or R; Google Sheets; survey tools",
    ),
    "Data Scientist": (
        "Machine Learning Scientist; Applied Scientist; Quantitative Analyst; Research Data Scientist; Decision Scientist; Predictive Modeller",
        "predictive modelling; credit scoring; recommendation systems; forecasting; experimentation and A/B testing; natural language data",
        "frame business problems as modelling problems; explore and prepare data; train and evaluate models; explain results and limits to stakeholders; design experiments; monitor model performance; write up methods",
        "Python; pandas and scikit-learn; Jupyter notebooks; SQL; statistical methods; Git; cloud notebooks",
    ),
    "Machine Learning Engineer": (
        "ML Engineer; AI Engineer; MLOps Engineer; Deep Learning Engineer; Applied ML Engineer; Model Deployment Engineer",
        "model serving; MLOps and pipelines; recommendation systems; speech and language models; computer vision systems; on-device models",
        "turn prototypes into production services; build training and evaluation pipelines; deploy and monitor models; optimise speed and cost; manage datasets and versions; work with data scientists on features; handle model failures",
        "Python; PyTorch or TensorFlow; Docker; cloud ML services; experiment trackers; Git; REST APIs",
    ),
    "Data Engineer": (
        "ETL Developer; Analytics Engineer; Data Platform Engineer; Big Data Engineer; Data Pipeline Engineer; Data Warehouse Developer",
        "batch pipelines; streaming data; data warehousing; data quality; analytics engineering; data platform operations",
        "build pipelines that move and clean data; design warehouse tables; schedule and monitor jobs; fix failed loads; manage access and data quality checks; support analysts with reliable datasets; document data sources",
        "SQL; Python; Airflow or similar schedulers; cloud data warehouses; Spark; dbt; Git",
    ),
    "Cloud Engineer": (
        "Cloud Infrastructure Engineer; Cloud Administrator; Cloud Operations Engineer; Platform Engineer; Cloud Support Engineer; Infrastructure Engineer",
        "cloud migration; infrastructure automation; cloud networking; cost optimisation; cloud security; platform operations",
        "provision servers, networks and storage; automate infrastructure with code; monitor availability and cost; set up access controls; support developers with environments; plan backups and recovery; respond to outages",
        "AWS, Azure or Google Cloud; Terraform; Linux; Docker and Kubernetes; monitoring tools; scripting in Bash or Python",
    ),
    "DevOps Engineer": (
        "Build and Release Engineer; Platform Engineer; Automation Engineer; Infrastructure Engineer; Release Manager; DevSecOps Engineer",
        "CI/CD pipelines; container platforms; release management; infrastructure as code; observability; DevSecOps",
        "build and maintain deployment pipelines; automate environment setup; manage containers and clusters; monitor systems and alerts; reduce release failures; work with developers on reliability; run post-incident reviews",
        "Git; Jenkins or GitHub Actions; Docker; Kubernetes; Terraform or Ansible; Linux; Prometheus and Grafana",
    ),
    "Cybersecurity Analyst": (
        "Information Security Analyst; SOC Analyst; Security Operations Analyst; IT Security Officer; Cyber Defence Analyst; Security Analyst",
        "security monitoring; incident response; vulnerability management; governance, risk and compliance; identity and access management; security awareness",
        "monitor alerts and logs; investigate suspicious activity; run vulnerability scans; recommend fixes to system owners; write incident reports; review access rights; train staff on safe practices",
        "SIEM platforms; vulnerability scanners; Wireshark; endpoint protection tools; Linux; ticketing systems",
    ),
    "Network Engineer": (
        "Network Administrator; Network Technician; NOC Engineer; Network Support Engineer; Infrastructure Engineer; Telecom Network Engineer",
        "enterprise networks; wireless networks; data centre networking; network security; internet service provider networks; network operations",
        "configure routers, switches and firewalls; design and document networks; troubleshoot connectivity faults; monitor performance; install and test links; plan upgrades; apply security policies",
        "Cisco IOS; routers and switches; firewalls; Wireshark; network monitoring tools; cabling testers",
    ),
    "Database Administrator": (
        "DBA; Database Engineer; Database Analyst; SQL Server Administrator; Oracle DBA; Data Platform Administrator",
        "performance tuning; backup and recovery; database security; cloud databases; replication and high availability; data migration",
        "install and patch databases; back up and restore data; tune slow queries; manage users and permissions; monitor capacity; plan migrations; support developers with schema changes",
        "PostgreSQL; MySQL; SQL Server or Oracle; backup tools; monitoring dashboards; SQL; shell scripting",
    ),
    "UI/UX Designer": (
        "Product Designer; UX Designer; UI Designer; Interaction Designer; Experience Designer; Digital Designer",
        "user research; interface design; interaction design; design systems; mobile app design; service design",
        "interview and observe users; map user journeys; sketch and wireframe ideas; build clickable prototypes; test designs with users; hand designs over to developers; maintain a design system",
        "Figma; prototyping tools; user testing tools; whiteboarding tools; design systems; basic HTML and CSS",
    ),
    "Quality Assurance Engineer": (
        "QA Engineer; Software Tester; Test Engineer; Test Analyst; Automation Tester; QA Analyst",
        "manual testing; test automation; mobile testing; performance testing; API testing; user acceptance testing",
        "read requirements and write test cases; test new features before release; report and track bugs; automate repeat tests; check fixes; run regression tests; advise the team on quality risks",
        "test management tools; Selenium or Playwright; Postman; issue trackers; Git; device emulators",
    ),
    "IT Support Specialist": (
        "Help Desk Technician; IT Support Officer; Desktop Support Technician; Service Desk Analyst; IT Technician; Technical Support Officer",
        "help desk; desktop and hardware support; user account administration; office network support; field support; applications support",
        "answer user requests and log tickets; set up computers and accounts; fix hardware, software and printer problems; install updates; maintain equipment records; guide users on tools; escalate complex faults",
        "ticketing systems; Windows and Microsoft 365; remote support tools; Active Directory; basic networking tools; hardware toolkits",
    ),
    "Systems Analyst": (
        "Business Systems Analyst; IT Business Analyst; Requirements Analyst; Functional Analyst; Solutions Analyst; Process Analyst",
        "requirements analysis; process improvement; system integration; ERP systems; public-sector systems; banking systems",
        "interview users about their needs; document requirements and processes; model how a system should work; compare solution options; support testing and rollout; write user guides; liaise between business and developers",
        "process modelling tools; UML; spreadsheets; SQL; requirements trackers; presentation tools",
    ),
    "Embedded Systems Engineer": (
        "Firmware Engineer; Embedded Software Engineer; IoT Engineer; Hardware Engineer; Embedded Developer; Electronics Design Engineer",
        "firmware development; Internet of Things devices; automotive systems; consumer electronics; industrial controllers; low-power devices",
        "write firmware for microcontrollers; read schematics and datasheets; test and debug on hardware; interface sensors and communication modules; optimise memory and power; document designs; support manufacturing tests",
        "C and C++; microcontrollers such as STM32 or ESP32; oscilloscopes and multimeters; debuggers; Arduino and Raspberry Pi; Git",
    ),
    "Technology Product Manager": (
        "Product Manager; Product Owner; Digital Product Manager; Technical Product Manager; Associate Product Manager; Product Lead",
        "consumer apps; fintech products; platform products; growth; data products; internal tools",
        "talk to users and study usage data; decide what to build next; write clear requirements; work daily with designers and engineers; track product metrics; align stakeholders; plan launches",
        "roadmapping tools; analytics dashboards; issue trackers; prototyping tools; spreadsheets; user research tools",
    ),
    "Site Reliability Engineer": (
        "SRE; Reliability Engineer; Production Engineer; Platform Reliability Engineer; Systems Reliability Engineer; Infrastructure Reliability Engineer",
        "incident response; observability; capacity planning; reliability automation; performance engineering; disaster recovery",
        "monitor production systems; respond to and lead incidents; automate manual operations; set reliability targets; plan capacity; review designs for failure risks; write post-incident reports",
        "Linux; Kubernetes; Prometheus and Grafana; scripting languages; cloud platforms; on-call tools",
    ),
    "Solutions Architect": (
        "Technical Architect; Systems Architect; Cloud Architect; Enterprise Architect; Software Architect; Integration Architect",
        "cloud architecture; integration architecture; enterprise architecture; security architecture; data architecture; pre-sales architecture",
        "gather technical and business requirements; design system structure; choose technologies and justify trade-offs; produce architecture diagrams; guide delivery teams; review designs; estimate costs",
        "architecture diagramming tools; cloud platforms; API design tools; modelling notations; cost calculators; documentation tools",
    ),
    "Business Intelligence Developer": (
        "BI Developer; BI Analyst; Reporting Developer; Dashboard Developer; Data Visualisation Developer; BI Engineer",
        "dashboards; data modelling; self-service reporting; financial BI; sales BI; embedded analytics",
        "gather reporting needs; model data for reporting; build dashboards and scheduled reports; optimise slow reports; train users; maintain definitions of metrics; check numbers against source systems",
        "Power BI or Tableau; SQL; data warehouses; DAX; Excel; ETL tools",
    ),
    "Penetration Tester": (
        "Ethical Hacker; Security Tester; Offensive Security Engineer; Red Team Operator; Vulnerability Assessor; Application Security Tester",
        "web application testing; network testing; mobile app testing; red teaming; social engineering assessments; cloud security testing",
        "agree the scope and rules with the client; scan and map targets; attempt to exploit weaknesses safely; document findings with evidence; rate risks; recommend fixes; retest after remediation",
        "Kali Linux; Burp Suite; Nmap; Metasploit; scripting in Python; reporting templates",
    ),
    "Blockchain Developer": (
        "Smart Contract Developer; Web3 Developer; Distributed Ledger Engineer; Solidity Developer; Blockchain Engineer; DApp Developer",
        "smart contracts; decentralised applications; digital payments; tokenisation; supply-chain traceability; protocol development",
        "write and test smart contracts; build applications that talk to a blockchain; review code for security flaws; deploy to test and main networks; integrate wallets; document contracts; monitor deployed contracts",
        "Solidity; Ethereum tooling; JavaScript or TypeScript; test networks; wallets; Git",
    ),
    "Natural Language Processing Engineer": (
        "NLP Engineer; Language AI Engineer; Conversational AI Engineer; Computational Linguist; Speech and Language Engineer; LLM Engineer",
        "chatbots and assistants; search and retrieval; text classification; machine translation; speech recognition; African-language NLP",
        "prepare and label text data; fine-tune and evaluate language models; build retrieval and chatbot pipelines; measure quality and bias; deploy models behind APIs; handle multiple languages; write up evaluations",
        "Python; Hugging Face Transformers; PyTorch; vector databases; evaluation toolkits; Git",
    ),
    "Computer Vision Engineer": (
        "Vision Engineer; Image Processing Engineer; Perception Engineer; Vision AI Engineer; Imaging Scientist; Video Analytics Engineer",
        "object detection; medical imaging; satellite and drone imagery; document and ID recognition; video analytics; quality inspection",
        "collect and annotate images; train detection and classification models; evaluate accuracy on real conditions; optimise models for devices; build image pipelines; integrate cameras; report limitations",
        "Python; OpenCV; PyTorch or TensorFlow; annotation tools; GPUs; Git",
    ),
    "IT Project Manager": (
        "Technical Project Manager; Software Project Manager; Delivery Manager; Scrum Master; Programme Coordinator; Implementation Manager",
        "software delivery; infrastructure projects; system implementations; agile delivery; vendor-led projects; digital transformation",
        "plan scope, schedule and budget; run stand-ups and reviews; track risks and issues; coordinate vendors and teams; report progress to sponsors; manage change requests; close and hand over projects",
        "project scheduling tools; Jira or Trello; spreadsheets; reporting dashboards; collaboration tools; risk registers",
    ),
    "ERP Consultant": (
        "ERP Functional Consultant; SAP Consultant; Odoo Consultant; Microsoft Dynamics Consultant; ERP Implementation Specialist; Business Systems Consultant",
        "finance modules; supply chain modules; human resource modules; ERP implementation; ERP support; system integration",
        "map business processes to the system; configure modules; migrate data; test with users; train staff; support go-live; resolve post-implementation issues",
        "SAP, Odoo or Microsoft Dynamics; SQL; process mapping tools; spreadsheets; ticketing systems; training materials",
    ),
    "Data Protection Officer": (
        "DPO; Privacy Officer; Data Privacy Analyst; Privacy Compliance Officer; Information Governance Officer; Data Governance Officer",
        "privacy compliance; data protection impact assessments; data subject requests; breach response; privacy training; vendor privacy reviews",
        "advise teams on data protection law; review how personal data is collected and used; run impact assessments; handle access and deletion requests; keep records of processing; respond to breaches; train staff",
        "privacy management tools; data inventories; policy templates; risk registers; spreadsheets; e-learning tools",
    ),
    "IT Auditor": (
        "Information Systems Auditor; Technology Auditor; IT Risk Analyst; IT Controls Analyst; Systems Auditor; IT Compliance Analyst",
        "IT general controls; application controls; cybersecurity audits; data analytics in audit; regulatory technology audits; third-party risk",
        "plan audits of systems and controls; test access, change and backup controls; analyse system data; document evidence; report findings and risks; follow up on fixes; advise on control improvements",
        "audit management tools; data analysis tools such as ACL or IDEA; SQL; spreadsheets; control frameworks; reporting templates",
    ),
    "Technical Writer": (
        "Documentation Specialist; API Writer; Content Developer; Documentation Engineer; Information Developer; Technical Communicator",
        "API documentation; user guides; developer documentation; knowledge bases; release notes; training content",
        "interview engineers and try the product; write and update guides; document APIs with examples; organise a documentation site; edit for clarity; keep content in step with releases; gather reader feedback",
        "Markdown; docs-as-code tools; Git; API tools such as Postman; screenshot and diagram tools; style guides",
    ),
    # ---- Engineering and Built Environment ----
    "Civil Engineer": (
        "Site Engineer; Project Engineer; Resident Engineer; Design Engineer; Infrastructure Engineer; Municipal Engineer",
        "roads and highways; water and sanitation; structures; construction supervision; drainage; geotechnics",
        "prepare and check designs and drawings; supervise works on site; inspect quality and safety; measure and certify work done; coordinate contractors and consultants; solve site problems; write progress reports",
        "AutoCAD; Civil 3D; surveying equipment; structural analysis software; project scheduling tools; spreadsheets",
    ),
    "Structural Engineer": (
        "Structural Design Engineer; Building Engineer; Bridge Engineer; Structural Analyst; Design Engineer; Structures Engineer",
        "reinforced concrete design; steel structures; bridges; building assessment and retrofitting; foundations; timber and masonry",
        "calculate loads and design structural members; produce drawings and schedules; check designs against codes; inspect reinforcement and concrete on site; assess existing structures; advise architects on feasibility; review contractor proposals",
        "structural analysis software such as ETABS or Prokon; AutoCAD; Revit; spreadsheets; design codes; site testing equipment",
    ),
    "Mechanical Engineer": (
        "Plant Engineer; Maintenance Engineer; Design Engineer; Project Engineer; Service Engineer; Production Engineer",
        "plant maintenance; machine design; heating, ventilation and air conditioning; automotive; manufacturing; energy systems",
        "design or select machines and components; plan and supervise maintenance; diagnose breakdowns; prepare drawings and specifications; test and commission equipment; improve efficiency; manage spare parts and contractors",
        "SolidWorks or AutoCAD; maintenance management systems; measuring instruments; simulation tools; spreadsheets; workshop tools",
    ),
    "Electrical Engineer": (
        "Electrical Design Engineer; Power Engineer; Maintenance Engineer; Project Engineer; Protection Engineer; Building Services Electrical Engineer",
        "power distribution; building electrical services; industrial control; renewable energy systems; protection and switchgear; electrical maintenance",
        "design electrical installations; size cables and protective devices; prepare drawings and specifications; supervise installation; test and commission systems; diagnose faults; ensure compliance with safety rules",
        "AutoCAD Electrical; power system software such as ETAP; multimeters and testers; PLC software; spreadsheets; wiring regulations",
    ),
    "Electronics and Telecommunications Engineer": (
        "Telecom Engineer; RF Engineer; Transmission Engineer; Network Engineer; Electronics Engineer; Field Engineer",
        "mobile networks; fibre and transmission; radio frequency planning; satellite communication; electronics design; broadcast systems",
        "install and maintain telecom equipment; plan and optimise network coverage; test signals and links; design and test circuits; troubleshoot faults at sites; document configurations; coordinate site works",
        "spectrum analysers; network planning tools; oscilloscopes; fibre testers; circuit design software; vendor management systems",
    ),
    "Mechatronics Engineer": (
        "Automation Engineer; Controls Engineer; Robotics Engineer; Instrumentation and Control Engineer; Systems Integration Engineer; PLC Engineer",
        "industrial automation; robotics; control systems; packaging and production lines; embedded control; smart machines",
        "design automated systems; program controllers and robots; integrate sensors, motors and software; commission production lines; troubleshoot control faults; improve machine performance; document systems",
        "PLC programming software; SCADA; SolidWorks; microcontrollers; sensors and actuators; MATLAB",
    ),
    "Chemical Engineer": (
        "Process Engineer; Production Engineer; Plant Engineer; Process Safety Engineer; Quality Engineer; Operations Engineer",
        "process design; food and beverage processing; petrochemicals; water treatment; pharmaceuticals; process safety",
        "monitor and optimise plant processes; design and scale up processes; carry out mass and energy balances; investigate quality or yield problems; ensure safe operation; supervise operators; prepare technical reports",
        "process simulation software such as Aspen; control systems; laboratory instruments; spreadsheets; P&ID drawings; safety analysis methods",
    ),
    "Architect": (
        "Design Architect; Project Architect; Architectural Designer; Landscape and Urban Designer; Conservation Architect; Architectural Technologist",
        "residential design; commercial buildings; institutional buildings; sustainable design; interior architecture; heritage conservation",
        "meet clients and develop a brief; produce concept and detailed designs; prepare drawings and models; obtain approvals; coordinate engineers and consultants; inspect construction; administer the building contract",
        "AutoCAD; Revit or ArchiCAD; SketchUp; rendering software; Adobe tools; building regulations",
    ),
    "Quantity Surveyor": (
        "Cost Consultant; Cost Engineer; Estimator; Contracts Surveyor; Commercial Manager; Project Quantity Surveyor",
        "cost planning; bills of quantities; contract administration; valuations and final accounts; claims; procurement advice",
        "estimate project costs; measure quantities from drawings; prepare bills of quantities and tenders; value work done for payment; manage variations and claims; advise on contracts; prepare final accounts",
        "measurement software; spreadsheets; AutoCAD; cost databases; contract forms; project management tools",
    ),
    "Land Surveyor": (
        "Geomatics Engineer; Cadastral Surveyor; Engineering Surveyor; Topographic Surveyor; Hydrographic Surveyor; Survey Technician",
        "cadastral surveys; engineering and construction surveys; topographic mapping; hydrographic surveys; GIS and mapping; aerial and drone surveys",
        "measure land and set out boundaries; set out construction works; process survey data; produce maps and plans; research land records; prepare survey reports; resolve boundary queries",
        "total stations; GNSS receivers; levels; drones; AutoCAD Civil 3D; GIS software",
    ),
    "Urban and Regional Planner": (
        "Physical Planner; Town Planner; City Planner; Development Control Officer; Planning Consultant; Spatial Planner",
        "development control; master planning; transport planning; housing and informal settlements; environmental planning; county spatial planning",
        "prepare spatial and development plans; assess planning applications; analyse land use and population data; consult communities and stakeholders; advise on policy and regulations; produce maps and reports; monitor compliance",
        "GIS software; AutoCAD; planning regulations; survey and census data; presentation tools; consultation methods",
    ),
    "Construction Project Manager": (
        "Construction Manager; Site Manager; Project Manager; Contracts Manager; Clerk of Works; Project Coordinator",
        "building projects; infrastructure projects; contract administration; site management; programme and cost control; health and safety management",
        "plan the works programme; coordinate contractors and suppliers; monitor cost, quality and progress; chair site meetings; manage risks and changes; enforce safety on site; report to the client",
        "MS Project or Primavera; spreadsheets; drawings and BIM viewers; contract forms; site reporting tools; safety management systems",
    ),
    "Geospatial and GIS Specialist": (
        "GIS Analyst; GIS Officer; Remote Sensing Analyst; Cartographer; Geospatial Analyst; GIS Developer",
        "spatial analysis; remote sensing; web mapping; cartography; spatial databases; drone mapping",
        "collect and clean spatial data; analyse patterns on maps; process satellite and drone imagery; build maps and dashboards; maintain spatial databases; support field data collection; present results to decision makers",
        "QGIS; ArcGIS; Google Earth Engine; PostGIS; GPS devices; Python",
    ),
    "Water and Sanitation Engineer": (
        "Water Engineer; WASH Engineer; Water Supply Engineer; Wastewater Engineer; Hydraulic Engineer; Public Health Engineer",
        "water supply systems; wastewater treatment; rural water and sanitation; hydraulic design; borehole and pumping systems; water utility operations",
        "design water supply and sewer networks; size pipes, pumps and tanks; supervise construction; test and commission systems; monitor water quality; plan operation and maintenance; advise communities and utilities",
        "EPANET; AutoCAD; Civil 3D; water quality testing kits; GIS software; spreadsheets",
    ),
    "Biomedical Engineer": (
        "Clinical Engineer; Medical Equipment Engineer; Biomedical Equipment Technologist; Medical Device Engineer; Hospital Engineer; Field Service Engineer",
        "medical equipment maintenance; imaging equipment; laboratory equipment; life-support equipment; device design; hospital equipment planning",
        "install and commission medical equipment; carry out planned maintenance; repair faulty devices; test safety and calibration; train clinical staff; keep equipment records; advise on procurement",
        "electrical safety analysers; multimeters and oscilloscopes; calibration equipment; maintenance management systems; service manuals; hand tools",
    ),
    "Industrial Engineer": (
        "Process Improvement Engineer; Operations Engineer; Production Engineer; Methods Engineer; Continuous Improvement Engineer; Quality Engineer",
        "lean manufacturing; work study; production planning; quality engineering; supply chain optimisation; facility layout",
        "study how work is done; measure and remove waste; design layouts and workflows; plan production and capacity; analyse quality data; lead improvement projects; train teams on new methods",
        "process mapping tools; spreadsheets; simulation software; statistical tools such as Minitab; ERP systems; time study tools",
    ),
    "Building Services Engineer": (
        "MEP Engineer; Mechanical and Electrical Services Engineer; HVAC Engineer; Facilities Engineer; Services Design Engineer; Building Systems Engineer",
        "heating, ventilation and air conditioning; electrical services; plumbing and drainage; fire protection; lifts; energy efficiency",
        "design mechanical, electrical and plumbing systems; coordinate services with the architect; prepare drawings and specifications; inspect installation; test and commission systems; advise on energy use; plan maintenance",
        "AutoCAD MEP; Revit; load calculation software; lighting design software; spreadsheets; building codes",
    ),
    "Environmental Engineer": (
        "Environmental Consultant; Environmental Officer; Pollution Control Engineer; Waste Management Engineer; Sustainability Engineer; Environmental Compliance Engineer",
        "wastewater treatment; solid waste management; air quality; environmental impact assessment; site remediation; sustainability",
        "assess environmental impacts of projects; design treatment and waste systems; sample and monitor water, air and soil; check compliance with regulations; prepare assessment and audit reports; advise on mitigation; engage communities",
        "sampling and monitoring equipment; GIS software; AutoCAD; modelling tools; environmental regulations; spreadsheets",
    ),
    "Aerospace Engineer": (
        "Aeronautical Engineer; Aircraft Design Engineer; Flight Systems Engineer; Avionics Engineer; Structures Engineer; Space Systems Engineer",
        "aerodynamics; aircraft structures; propulsion; avionics; maintenance engineering; small satellites",
        "analyse aerodynamic and structural performance; design and test components; run simulations; support aircraft maintenance planning; review technical documentation; investigate defects; ensure airworthiness requirements are met",
        "CAD software such as CATIA; simulation tools; MATLAB; wind tunnel and test rigs; technical manuals; airworthiness regulations",
    ),
    "Agricultural Engineer": (
        "Irrigation Engineer; Farm Mechanisation Engineer; Soil and Water Engineer; Post-Harvest Engineer; Agricultural Machinery Engineer; Rural Infrastructure Engineer",
        "irrigation and drainage; farm machinery; post-harvest technology; soil and water conservation; farm structures; agro-processing",
        "design irrigation and drainage systems; select and test farm machinery; plan soil and water conservation works; design storage and processing facilities; supervise installation; train farmers and operators; prepare technical reports",
        "AutoCAD; irrigation design software; surveying equipment; GIS software; farm machinery; spreadsheets",
    ),
    "Marine Engineer": (
        "Ship Engineer; Marine Engineering Officer; Naval Engineer; Marine Superintendent; Shipyard Engineer; Offshore Engineer",
        "ship propulsion; auxiliary machinery; ship repair and dry docking; port and harbour equipment; offshore systems; marine surveying",
        "operate and maintain engines and machinery; carry out inspections and repairs; manage fuel and spare parts; keep engine room records; respond to breakdowns at sea; ensure safety and pollution rules are met; supervise engine crew",
        "marine diesel engines; engine room systems; diagnostic instruments; maintenance management systems; safety equipment; technical manuals",
    ),
    "Geotechnical Engineer": (
        "Soils Engineer; Foundation Engineer; Ground Engineer; Materials Engineer; Geotechnical Consultant; Site Investigation Engineer",
        "site investigation; foundation design; slope stability; earthworks; road pavement materials; dams and embankments",
        "plan and supervise site investigations; log boreholes and trial pits; test soil and rock samples; analyse ground conditions; design foundations and earthworks; advise on ground risks; write geotechnical reports",
        "drilling and sampling equipment; soil laboratory equipment; slope and foundation software such as PLAXIS; AutoCAD; spreadsheets; field testing kits",
    ),
    "Highway and Transport Engineer": (
        "Roads Engineer; Highway Engineer; Traffic Engineer; Transport Engineer; Pavement Engineer; Road Maintenance Engineer",
        "road geometric design; pavement design; traffic engineering; road maintenance; road safety; public transport infrastructure",
        "design road alignments and junctions; design pavements; carry out traffic counts and studies; supervise road construction; inspect road condition; plan maintenance; carry out road safety audits",
        "Civil 3D; pavement design software; traffic modelling tools; surveying equipment; materials testing equipment; spreadsheets",
    ),
    "Telecommunications Network Planner": (
        "RF Planner; Network Planning Engineer; Transmission Planner; Radio Network Planner; Fibre Planner; Core Network Planner",
        "radio network planning; fibre network planning; capacity planning; site acquisition support; network optimisation; rural coverage planning",
        "forecast demand and capacity; plan sites and coverage; design fibre routes; run coverage simulations; prepare site and link designs; analyse network performance data; coordinate rollout teams",
        "radio planning tools such as Atoll; GIS software; link budget calculators; drive-test tools; spreadsheets; network performance systems",
    ),
    "Robotics Engineer": (
        "Robotics Software Engineer; Automation Engineer; Controls Engineer; Robot Programmer; Mechatronics Engineer; Autonomous Systems Engineer",
        "industrial robots; mobile robots; drones; robot perception; motion planning; agricultural robotics",
        "design robot mechanisms and control software; program robot motion; integrate sensors and cameras; test in simulation and on hardware; tune controllers; troubleshoot failures; document designs",
        "ROS; Python and C++; simulation tools such as Gazebo; CAD software; microcontrollers; sensors and actuators",
    ),
    "Fire Safety Engineer": (
        "Fire Protection Engineer; Fire Engineer; Fire Safety Officer; Fire Systems Designer; Life Safety Engineer; Fire Risk Assessor",
        "fire detection and alarm; sprinkler and suppression systems; fire risk assessment; evacuation design; building code compliance; industrial fire safety",
        "assess fire risks in buildings; design detection and suppression systems; review building plans for compliance; inspect installations; test and commission systems; advise on evacuation; train occupants",
        "fire system design software; AutoCAD; hydraulic calculation tools; building codes; testing instruments; risk assessment templates",
    ),
    "Materials Engineer": (
        "Metallurgist; Materials Testing Engineer; Quality Engineer; Corrosion Engineer; Materials Scientist; Construction Materials Engineer",
        "metals and alloys; concrete and construction materials; polymers and composites; corrosion; failure analysis; materials testing",
        "test materials for strength and durability; select materials for a design; investigate failures; check supplier quality; develop or improve materials; write test reports; advise on standards",
        "universal testing machines; microscopes; hardness testers; laboratory equipment; standards such as ISO and ASTM; spreadsheets",
    ),
    "Landscape Architect": (
        "Landscape Designer; Urban Designer; Environmental Designer; Site Planner; Parks Planner; Landscape Consultant",
        "parks and public spaces; residential landscapes; urban design; ecological restoration; site planning; campus and institutional grounds",
        "analyse sites and client needs; design planting and outdoor spaces; prepare drawings and specifications; choose plants and materials; coordinate with architects and engineers; inspect works; advise on maintenance",
        "AutoCAD; SketchUp; rendering tools; plant databases; GIS software; Adobe tools",
    ),
    "Facilities Manager": (
        "Facilities Officer; Building Manager; Property and Facilities Manager; Estates Manager; Maintenance Manager; Operations Manager",
        "building maintenance; workplace services; health and safety; energy management; security and cleaning contracts; space planning",
        "plan and schedule maintenance; manage contractors and service providers; control facilities budgets; inspect buildings; handle occupant requests; ensure safety compliance; plan moves and space use",
        "maintenance management systems; building management systems; spreadsheets; contract management tools; inspection checklists; budgeting tools",
    ),
}
