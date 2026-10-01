"""
Extract and balance a curated tech career dataset from Kaggle job_descriptions.csv
with realistic student skill profile augmentation to prevent artificial data memorization
and ensure robust generalization (preventing both overfitting and underfitting).
"""

import os
import random
import re
from pathlib import Path
import pandas as pd

SOURCE_CSV = Path(r"C:\Users\Mwiti\Downloads\Datasets\job_descriptions.csv")
OUTPUT_CSV = Path("ml/data/tech_career_dataset.csv")

ROLE_MAP = {
    "Backend Developer": "Backend Developer",
    "Backend Web Developer": "Backend Developer",
    "Java Backend Developer": "Backend Developer",
    "Server Developer": "Backend Developer",
    "Frontend Developer": "Frontend Developer",
    "Front-End Developer": "Frontend Developer",
    "Frontend Web Developer": "Frontend Developer",
    "Frontend Web Designer": "Frontend Developer",
    "JavaScript Developer": "Frontend Developer",
    "Full-Stack Developer": "Full-Stack Developer",
    "Mobile App Developer": "Mobile App Developer",
    "DevOps Engineer": "DevOps / Cloud Engineer",
    "Cloud Systems Engineer": "DevOps / Cloud Engineer",
    "Cloud Architect": "DevOps / Cloud Engineer",
    "Data Scientist": "Data Scientist / ML Engineer",
    "Machine Learning Engineer": "Data Scientist / ML Engineer",
    "Data Analyst": "Data Analyst / BI Specialist",
    "Data Analyst Researcher": "Data Analyst / BI Specialist",
    "Business Intelligence Analyst": "Data Analyst / BI Specialist",
    "Data Quality Analyst": "Data Analyst / BI Specialist",
    "Data Engineer": "Data Engineer",
    "Big Data Engineer": "Data Engineer",
    "ETL Developer": "Data Engineer",
    "Data Architect": "Data Engineer",
    "NoSQL Database Engineer": "Data Engineer",
    "Database Developer": "Data Engineer",
    "SQL Database Developer": "Data Engineer",
    "Cybersecurity Analyst": "Cybersecurity Analyst",
    "Security Operations Center (SOC) Analyst": "Cybersecurity Analyst",
    "Security Consultant": "Cybersecurity Analyst",
    "Database Security Specialist": "Cybersecurity Analyst",
    "Quality Assurance Analyst": "QA / Test Engineer",
    "QA Tester": "QA / Test Engineer",
    "Software QA Tester": "QA / Test Engineer",
    "Test Automation Engineer": "QA / Test Engineer",
    "Automation Test Engineer": "QA / Test Engineer",
    "Network Engineer": "Network & Systems Engineer",
    "Network Administrator": "Network & Systems Engineer",
    "Network Security Engineer": "Network & Systems Engineer",
    "Systems Administrator": "Network & Systems Engineer",
    "System Administrator": "Network & Systems Engineer",
    "IT Systems Administrator": "Network & Systems Engineer",
    "UX/UI Designer": "UI/UX Designer",
    "UI/UX Designer": "UI/UX Designer",
    "User Experience Designer": "UI/UX Designer",
    "User Interface Designer": "UI/UX Designer",
    "Interaction Designer": "UI/UX Designer",
    "Database Administrator": "Database Administrator",
    "Database Analyst": "Database Administrator",
}

# Domain skill pools for realistic student profile simulation
SKILL_POOLS = {
    "Backend Developer": [
        "Python", "Django", "FastAPI", "Java", "Spring Boot", "Node.js", "Express",
        "Go", "C#", ".NET Core", "RESTful APIs", "GraphQL", "PostgreSQL", "MySQL",
        "MongoDB", "Redis", "Microservices", "Docker", "Git", "Database Optimization",
        "Celery", "Kafka", "Authentication (JWT)", "Server Architecture"
    ],
    "Frontend Developer": [
        "JavaScript", "TypeScript", "React", "Next.js", "Vue.js", "Angular", "HTML5",
        "CSS3", "Tailwind CSS", "Bootstrap", "Redux", "Zustand", "Responsive Web Design",
        "Webpack", "Vite", "REST API Consumption", "Web Accessibility (WCAG)",
        "Cross-Browser Compatibility", "Jest", "DOM Manipulation"
    ],
    "Full-Stack Developer": [
        "JavaScript", "TypeScript", "React", "Node.js", "Express", "Python", "Django",
        "PostgreSQL", "MongoDB", "REST APIs", "GraphQL", "Docker", "Git", "Tailwind CSS",
        "Next.js", "Authentication", "Cloud Deployment", "CI/CD Basics", "Agile"
    ],
    "Mobile App Developer": [
        "Kotlin", "Android SDK", "Jetpack Compose", "Java", "Swift", "SwiftUI",
        "iOS Development", "Flutter", "Dart", "React Native", "Firebase", "SQLite / Room",
        "Mobile UI Design", "REST APIs Integration", "App Store / Play Store Deployment",
        "MVVM Architecture", "Coroutines"
    ],
    "DevOps / Cloud Engineer": [
        "Linux Administration", "Bash Scripting", "Docker", "Kubernetes", "AWS (EC2, S3, RDS)",
        "Azure", "GCP", "Terraform", "Ansible", "CI/CD (GitHub Actions, Jenkins)",
        "Prometheus", "Grafana", "Nginx", "Helm", "Cloud Security", "Infrastructure as Code"
    ],
    "Data Scientist / ML Engineer": [
        "Python", "R", "pandas", "NumPy", "scikit-learn", "TensorFlow", "PyTorch",
        "Machine Learning", "Deep Learning", "Natural Language Processing (NLP)",
        "Computer Vision", "Statistical Modeling", "Exploratory Data Analysis (EDA)",
        "Jupyter Notebooks", "Feature Engineering", "MLflow", "Model Deployment"
    ],
    "Data Analyst / BI Specialist": [
        "SQL (Advanced Queries, CTEs)", "Power BI", "Tableau", "Excel (VLOOKUP, Pivot Tables)",
        "Python (pandas, matplotlib)", "Data Cleaning", "Data Visualization",
        "Business Intelligence", "KPI Dashboards", "Statistical Analysis", "Reporting",
        "Data Storytelling", "ETL Basics"
    ],
    "Data Engineer": [
        "Python", "SQL", "Apache Spark", "PySpark", "Apache Kafka", "Apache Airflow",
        "Data Warehousing (Snowflake, BigQuery)", "ETL Pipeline Design", "Hadoop",
        "PostgreSQL", "Data Modeling", "dbt", "Parquet", "Distributed Systems"
    ],
    "Cybersecurity Analyst": [
        "Network Security", "Wireshark", "Penetration Testing", "Vulnerability Assessment",
        "Kali Linux", "SIEM (Splunk, QRadar)", "OWASP Top 10", "Firewalls", "IDS/IPS",
        "Incident Response", "Ethical Hacking", "Cryptography", "Security Auditing", "CompTIA Security+"
    ],
    "QA / Test Engineer": [
        "Software Testing Methodologies", "Manual Testing", "Automated Testing",
        "Selenium WebDriver", "Cypress", "Playwright", "Postman (API Testing)",
        "PyTest", "JUnit", "Jira (Bug Tracking)", "Test Case Design", "Regression Testing",
        "Performance Testing (JMeter)", "CI/CD Test Integration"
    ],
    "Network & Systems Engineer": [
        "Cisco CCNA", "Routing and Switching", "TCP/IP Networking", "DNS / DHCP",
        "Linux Server Administration", "Windows Server / Active Directory", "Virtualization (VMware)",
        "Network Troubleshooting", "VPNs", "Firewall Configuration", "Network Monitoring"
    ],
    "UI/UX Designer": [
        "Figma", "Adobe XD", "Sketch", "Wireframing", "Interactive Prototyping",
        "User Research", "Usability Testing", "Information Architecture", "Design Systems",
        "User Journey Mapping", "Color Theory", "Typography", "Responsive Layouts", "Heuristic Evaluation"
    ],
    "Database Administrator": [
        "Database Administration", "MySQL", "PostgreSQL", "Oracle DB", "Microsoft SQL Server",
        "Database Tuning and Indexing", "Backup and Disaster Recovery", "Replication and Clustering",
        "High Availability", "Database Security", "Query Optimization", "Stored Procedures"
    ],
}

QUALIFICATIONS = [
    "BSc Computer Science",
    "BSc Informatics and Computer Science",
    "Bachelor of Business Information Technology (BBIT)",
    "BSc Software Engineering",
    "BSc Data Science",
    "Diploma in Information Technology",
    "BSc Information Technology",
    "Certificate in Computer Programming",
]

EXPERIENCE_LEVELS = [
    "Final Year University Student",
    "Recent Graduate (0 Years)",
    "0 to 1 Years (Entry Level)",
    "1 to 2 Years (Junior Developer)",
    "6 Months Internship Experience",
    "Freelance & Academic Projects",
]


def generate_curated_dataset():
    random.seed(42)
    print(f"Reading source Kaggle dataset: {SOURCE_CSV}")

    # Step 1: Collect up to 1,000 real job postings per category from Kaggle
    collected_real = {cat: [] for cat in SKILL_POOLS.keys()}
    target_cats = set(SKILL_POOLS.keys())

    chunk_size = 50000
    usecols = ["Job Id", "Role", "Job Title", "Experience", "Qualifications", "skills", "Job Description"]

    for chunk in pd.read_csv(SOURCE_CSV, usecols=usecols, chunksize=chunk_size):
        chunk["Category"] = chunk["Role"].map(ROLE_MAP)
        tech = chunk[chunk["Category"].isin(target_cats)]

        for _, row in tech.iterrows():
            cat = row["Category"]
            if len(collected_real[cat]) < 1000:
                skills = str(row.get("skills", "")).strip()
                quals = str(row.get("Qualifications", "")).strip()
                exp = str(row.get("Experience", "")).strip()
                desc = str(row.get("Job Description", ""))[:180].strip()

                composite = f"Qualifications: {quals}. Experience: {exp}. Skills: {skills}."
                collected_real[cat].append({
                    "target_category": cat,
                    "qualifications": quals,
                    "experience": exp,
                    "skills": skills,
                    "feature_text": composite,
                    "source": "kaggle_job_posting",
                })

        if all(len(recs) >= 1000 for recs in collected_real.values()):
            break

    # Step 2: Generate 1,000 diversified student profiles per category
    # to realistically model diverse skill combinations, varied degree backgrounds,
    # and realistic student phrasing.
    augmented_profiles = []
    for cat, skills_pool in SKILL_POOLS.items():
        for _ in range(1000):
            # Select 3 to 7 primary skills from this role's ecosystem
            num_skills = random.randint(3, 7)
            chosen_skills = random.sample(skills_pool, k=min(num_skills, len(skills_pool)))

            # 25% chance of knowing a general tool (Git, SQL, Linux)
            if random.random() < 0.25 and "Git" not in chosen_skills:
                chosen_skills.append("Git")
            if random.random() < 0.15 and "SQL" not in chosen_skills and cat != "UI/UX Designer":
                chosen_skills.append("SQL basics")

            random.shuffle(chosen_skills)
            skills_str = ", ".join(chosen_skills)

            qual = random.choice(QUALIFICATIONS)
            exp = random.choice(EXPERIENCE_LEVELS)
            composite = f"Qualifications: {qual}. Experience: {exp}. Skills: {skills_str}."

            augmented_profiles.append({
                "target_category": cat,
                "qualifications": qual,
                "experience": exp,
                "skills": skills_str,
                "feature_text": composite,
                "source": "student_skill_permutation",
            })

    # Combine real postings + realistic student permutations
    final_records = []
    for cat in SKILL_POOLS.keys():
        real_recs = collected_real[cat]
        final_records.extend(real_recs)

    final_records.extend(augmented_profiles)

    df_final = pd.DataFrame(final_records)
    # Shuffle dataset
    df_final = df_final.sample(frac=1.0, random_state=42).reset_index(drop=True)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print("\nDataset Generation Complete:")
    print(f"  Target File: {OUTPUT_CSV}")
    print(f"  Total records: {len(df_final):,}")
    print(f"  Categories: {df_final['target_category'].nunique()}")
    print("\nRecords per category:")
    for cat, count in df_final["target_category"].value_counts().items():
        print(f"  - {cat:<30}: {count:,}")


if __name__ == "__main__":
    generate_curated_dataset()
