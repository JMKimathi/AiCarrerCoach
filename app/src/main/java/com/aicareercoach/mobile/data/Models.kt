package com.aicareercoach.mobile.data

data class UserSession(
    val name: String,
    val email: String,
    val userId: String = "",
    val token: String = "",
    val course: String = "BSc Computer Science",
    val careerGoal: String = "Roles in AI and data",
    val isAdmin: Boolean = false
) {
    val firstName: String get() = name.trim().substringBefore(" ").ifBlank { "there" }
    val initials: String
        get() = name.split(" ")
            .mapNotNull { it.firstOrNull()?.uppercaseChar() }
            .take(2)
            .joinToString("")
            .ifBlank { "ST" }
}

data class CareerResource(
    val id: String,
    val title: String,
    val category: String,
    val summary: String
)

data class AuthResult(val session: UserSession?, val error: String? = null)

data class StudentAccount(
    val name: String,
    val email: String,
    val course: String,
    val status: String
)

data class AdminOverview(
    val activeStudents: Int,
    val careerResources: Int,
    val chatsThisWeek: Int,
    val flaggedResponses: Int,
    val topResources: List<String>
)

data class CareerPathMatch(
    val role: String,
    val fitScore: Int,
    val matchingEvidence: List<String>,
    val skillsToExplore: List<String>,
    val nextSteps: List<String>,
    val relatedResources: List<String>
)

data class CareerAssessmentResult(
    val profileCompleteness: String,
    val summary: String,
    val recommendations: List<CareerPathMatch>,
    val informationNote: String
)

object SampleData {
    val resources = listOf(
        CareerResource(
            "cv-swe",
            "Software Engineer CV Template",
            "CV Templates",
            "A one-page layout for internships and graduate roles, with sections for projects, skills, and impact statements."
        ),
        CareerResource(
            "interview-behavioural",
            "Behavioural Interview Question Bank",
            "Interview Prep",
            "STAR-format prompts covering teamwork, conflict, leadership, and failure stories commonly asked by Kenyan employers."
        ),
        CareerResource(
            "path-ds",
            "Careers in Data Science",
            "Career Paths",
            "How analyst, ML engineer, and research roles differ, plus the skills hiring managers look for in Nairobi and remote teams."
        ),
        CareerResource(
            "interview-algo",
            "Technical Interview Practice: Algorithms",
            "Interview Prep",
            "A focused set of array, graph, and complexity questions with hints you can practise before a coding screen."
        ),
        CareerResource(
            "skill-portfolio",
            "Building a Portfolio Website",
            "Skill Building",
            "A simple structure for showcasing two to three projects so recruiters can see your work in under two minutes."
        ),
        CareerResource(
            "cv-cover",
            "Cover Letter Writing Guide",
            "CV Templates",
            "A short template that maps your course projects to the job description without sounding generic."
        ),
    )

    val students = listOf(
        StudentAccount("John Mwiti", "john.mwiti@strathmore.edu", "BSc Computer Science", "Active"),
        StudentAccount("Amina Otieno", "amina.otieno@strathmore.edu", "BBIT", "Active"),
        StudentAccount("Brian Kimani", "brian.kimani@strathmore.edu", "BSc Informatics", "Needs CV review"),
        StudentAccount("Faith Wanjiku", "faith.wanjiku@strathmore.edu", "BSc Computer Science", "Active"),
    )
}
