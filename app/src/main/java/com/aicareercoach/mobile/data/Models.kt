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
    val status: String,
    val userId: String = ""
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
    val relatedResources: List<String>,
    val roleSummary: String = "",
    val entryLevelRoles: List<String> = emptyList(),
    val applicationChannelTypes: List<String> = emptyList(),
    val sampleInterviewQuestions: List<String> = emptyList(),
    val cvTailoringGuidance: String = "",
    val progressionOptions: List<String> = emptyList(),
    val requirementsAndQualificationNotes: String = ""
)

data class CareerAssessmentResult(
    val profileCompleteness: String,
    val summary: String,
    val recommendations: List<CareerPathMatch>,
    val informationNote: String
)

data class CareerCategory(val name: String, val careerCount: Int)

data class CareerSummary(
    val careerId: String,
    val roleTitle: String,
    val category: String,
    val specialisation: String,
    val coreSkills: List<String>,
    val commonlyRegulated: Boolean
)

data class CareerPage(val total: Int, val items: List<CareerSummary>)

data class PathwayStage(
    val stageNumber: Int,
    val stageName: String,
    val exampleTitle: String,
    val opportunityType: String,
    val typicalTiming: String,
    val whatToBuild: String
)

data class OpportunityTemplate(
    val opportunityType: String,
    val market: String,
    val exampleTitle: String,
    val employerType: String,
    val eligibility: String,
    val typicalDuration: String,
    val typicalTiming: String,
    val applicantsUsuallyShow: String,
    val documentsUsuallyRequested: String,
    val whereAdvertised: String,
    val notes: String
)

data class OfficialSource(
    val name: String,
    val url: String,
    val whatToCheck: String,
    val roleSpecific: Boolean
)

data class CareerDetail(
    val careerId: String,
    val roleTitle: String,
    val category: String,
    val specialisation: String,
    val description: String,
    val commonlyRegulated: Boolean,
    val coreSkills: List<String>,
    val preferredSkills: List<String>,
    val transferableSkills: List<String>,
    val studyAreas: String,
    val qualificationLevels: String,
    val certifications: String,
    val verifyWith: String,
    val verificationNote: String,
    val pathway: List<PathwayStage>,
    val opportunities: List<OpportunityTemplate>,
    val officialSources: List<OfficialSource>,
    val informationNote: String,
    val jobTitles: Map<String, List<String>> = emptyMap(),
    val tasks: List<String> = emptyList(),
    val tools: List<String> = emptyList(),
    val relatedCareers: List<RelatedCareer> = emptyList(),
    val employers: List<String> = emptyList(),
    val workingPatterns: List<String> = emptyList()
)

data class RelatedCareer(
    val careerId: String,
    val roleTitle: String,
    val category: String,
    val commonGround: String
)

data class CvProject(val title: String, val description: String)

data class CvExperience(
    val title: String,
    val organisation: String,
    val period: String,
    val highlights: List<String>
)

data class CvRequest(
    val phone: String = "",
    val location: String = "",
    val institution: String = "",
    val graduationYear: String = "",
    val targetOpportunity: String = "",
    val skills: List<String> = emptyList(),
    val projects: List<CvProject> = emptyList(),
    val experience: List<CvExperience> = emptyList(),
    val certifications: List<String> = emptyList(),
    val activities: List<String> = emptyList()
)

data class CvResult(
    val roleTitle: String,
    val markdown: String,
    val matchedSkills: List<String>,
    val skillsToBuild: List<String>,
    val tips: List<String>,
    val note: String
)

data class InterviewTurn(val speaker: String, val kind: String, val text: String)

data class InterviewState(
    val interviewId: String,
    val roleTitle: String,
    val status: String,
    val questionNumber: Int,
    val totalQuestions: Int,
    val interviewerMessage: String,
    val transcript: List<InterviewTurn>,
    val feedback: String
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
