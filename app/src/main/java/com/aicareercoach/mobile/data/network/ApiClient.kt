package com.aicareercoach.mobile.data.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import android.util.Log
import com.aicareercoach.mobile.data.AuthResult
import com.aicareercoach.mobile.data.AdminOverview
import com.aicareercoach.mobile.data.CareerResource
import com.aicareercoach.mobile.data.CareerAssessmentResult
import com.aicareercoach.mobile.data.CareerCategory
import com.aicareercoach.mobile.data.CareerDetail
import com.aicareercoach.mobile.data.CareerPage
import com.aicareercoach.mobile.data.CareerSummary
import com.aicareercoach.mobile.data.CvRequest
import com.aicareercoach.mobile.data.CvResult
import com.aicareercoach.mobile.data.InterviewState
import com.aicareercoach.mobile.data.InterviewTurn
import com.aicareercoach.mobile.data.OfficialSource
import com.aicareercoach.mobile.data.OpportunityTemplate
import com.aicareercoach.mobile.data.PathwayStage
import com.aicareercoach.mobile.data.RelatedCareer
import com.aicareercoach.mobile.data.CareerPathMatch
import com.aicareercoach.mobile.data.StudentAccount
import com.aicareercoach.mobile.data.UserSession
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

data class NetworkChatResponse(
    val sessionId: String,
    val response: String,
    val sources: List<String>
)

object ApiClient {
    // Confirmed laptop address on the current home Wi-Fi. The hotspot address is saved from the settings screen.
    private const val DEFAULT_BASE_URL = "http://192.168.100.3:8000/api"
    private const val PREFS_NAME = "backend_connection"
    private const val ENDPOINTS_KEY = "saved_endpoints"
    private const val HEALTH_CACHE_MS = 5_000L

    @Volatile private var baseUrl: String = DEFAULT_BASE_URL
    @Volatile private var candidateBaseUrls: List<String> = listOf(DEFAULT_BASE_URL)
    @Volatile private var checkedAt: Long = 0L
    @Volatile private var appContext: Context? = null

    fun initialize(context: Context) {
        val applicationContext = context.applicationContext
        appContext = applicationContext
        val saved = runCatching {
            val raw = applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .getString(ENDPOINTS_KEY, null)
            if (raw == null) emptyList() else {
                val values = JSONArray(raw)
                (0 until values.length()).mapNotNull { normalizeEndpoint(values.optString(it)) }.distinct()
            }
        }.getOrDefault(emptyList())
        candidateBaseUrls = saved.ifEmpty { listOf(DEFAULT_BASE_URL) }

        val connectivity = applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
        runCatching {
            connectivity?.registerDefaultNetworkCallback(object : ConnectivityManager.NetworkCallback() {
                override fun onAvailable(network: Network) { checkedAt = 0L }
                override fun onLost(network: Network) { checkedAt = 0L }
                override fun onCapabilitiesChanged(network: Network, networkCapabilities: android.net.NetworkCapabilities) {
                    checkedAt = 0L
                }
            })
        }
    }

    fun configuredEndpoints(): List<String> = candidateBaseUrls

    fun saveEndpoints(endpoints: List<String>) {
        val normalized = endpoints.mapNotNull(::normalizeEndpoint).distinct()
        candidateBaseUrls = normalized.ifEmpty { listOf(DEFAULT_BASE_URL) }
        appContext?.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            ?.edit()
            ?.putString(ENDPOINTS_KEY, JSONArray(candidateBaseUrls).toString())
            ?.apply()
        checkedAt = 0L
    }

    private fun normalizeEndpoint(value: String): String? {
        var endpoint = value.trim().trimEnd('/')
        if (endpoint.isBlank()) return null
        if (!endpoint.startsWith("http://") && !endpoint.startsWith("https://")) endpoint = "http://$endpoint"
        if (!endpoint.contains(":8000")) endpoint = "$endpoint:8000"
        // Accept a health-check URL pasted from a browser, including the accidental
        // /api/health/api suffix produced when /api is appended to it.
        endpoint = endpoint.replace(Regex("/api/health/api$"), "/api")
        if (endpoint.endsWith("/health")) endpoint = endpoint.removeSuffix("/health")
        while (endpoint.endsWith("/api/api")) endpoint = endpoint.removeSuffix("/api")
        if (!endpoint.endsWith("/api")) endpoint = "$endpoint/api"
        return endpoint
    }

    private suspend fun resolveBaseUrl(): String {
        val now = System.currentTimeMillis()
        if (now - checkedAt < HEALTH_CACHE_MS) return baseUrl
        for (candidate in candidateBaseUrls) {
            if (checkHealthAt(candidate)) {
                baseUrl = candidate
                checkedAt = System.currentTimeMillis()
                return candidate
            }
        }
        checkedAt = System.currentTimeMillis()
        return baseUrl
    }

    private suspend fun checkHealthAt(endpoint: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val conn = (URL("$endpoint/health").openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 1200
                readTimeout = 1200
            }
            try { conn.responseCode == 200 } finally { conn.disconnect() }
        } catch (_: Exception) {
            false
        }
    }

    private suspend fun endpointUrl(path: String): URL = URL("${resolveBaseUrl()}$path")

    suspend fun authenticate(
        register: Boolean, name: String, email: String, password: String, course: String = "", careerGoal: String = ""
    ): AuthResult = withContext(Dispatchers.IO) {
        try {
            val path = if (register) "register" else "login"
            val conn = (endpointUrl("/auth/$path").openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 5000
                readTimeout = 10000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Accept", "application/json")
            }
            val body = JSONObject().apply {
                put("email", email.trim())
                put("password", password)
                if (register) {
                    put("full_name", name.trim())
                    put("course", course.trim().ifBlank { JSONObject.NULL })
                    put("career_goal", careerGoal.trim().ifBlank { JSONObject.NULL })
                }
            }
            OutputStreamWriter(conn.outputStream).use { it.write(body.toString()) }
            val successful = conn.responseCode in 200..299
            val stream = if (successful) conn.inputStream else conn.errorStream
            val response = BufferedReader(InputStreamReader(stream)).use { it.readText() }
            if (!successful) {
                val json = JSONObject(response)
                val detail = json.optString("detail", "Request failed (${conn.responseCode})")
                return@withContext AuthResult(null, detail)
            }
            val json = JSONObject(response)
            val user = json.getJSONObject("user")
            AuthResult(
                UserSession(
                    userId = user.getString("user_id"),
                    name = user.getString("full_name"),
                    email = user.getString("email"),
                    token = json.getString("token"),
                    course = user.optString("course").takeUnless { it == "null" }.orEmpty(),
                    careerGoal = user.optString("career_goal").takeUnless { it == "null" }.orEmpty(),
                    isAdmin = user.optString("role") == "admin"
                )
            )
        } catch (e: Exception) {
            AuthResult(null, "Could not reach the backend. Start the API and try again.")
        }
    }

    suspend fun updateProfile(session: UserSession, name: String, course: String, careerGoal: String): UserSession? = withContext(Dispatchers.IO) {
        try {
            val conn = (endpointUrl("/auth/me").openConnection() as HttpURLConnection).apply {
                requestMethod = "PUT"
                connectTimeout = 5000
                readTimeout = 10000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Authorization", "Bearer ${session.token}")
            }
            val body = JSONObject().put("full_name", name.trim())
                .put("course", course.trim().ifBlank { JSONObject.NULL })
                .put("career_goal", careerGoal.trim().ifBlank { JSONObject.NULL })
            OutputStreamWriter(conn.outputStream).use { it.write(body.toString()) }
            if (conn.responseCode !in 200..299) return@withContext null
            val user = JSONObject(BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() })
            session.copy(
                userId = user.getString("user_id"),
                name = user.getString("full_name"),
                email = user.getString("email"),
                course = user.optString("course").takeUnless { it == "null" }.orEmpty(),
                careerGoal = user.optString("career_goal").takeUnless { it == "null" }.orEmpty(),
                isAdmin = user.optString("role") == "admin"
            )
        } catch (_: Exception) { null }
    }

    suspend fun getResources(token: String): List<CareerResource>? = withContext(Dispatchers.IO) {
        try {
            val conn = (endpointUrl("/resources").openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 4000
                readTimeout = 7000
                setRequestProperty("Authorization", "Bearer $token")
            }
            if (conn.responseCode !in 200..299) return@withContext null
            val array = JSONArray(BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() })
            buildList {
                for (i in 0 until array.length()) {
                    val item = array.getJSONObject(i)
                    add(CareerResource(item.getString("resource_id"), item.getString("title"), item.getString("category"), item.getString("summary")))
                }
            }
        } catch (_: Exception) { null }
    }

    suspend fun getAdminOverview(token: String): AdminOverview? = withContext(Dispatchers.IO) {
        try {
            val conn = (endpointUrl("/admin/overview").openConnection() as HttpURLConnection).apply {
                setRequestProperty("Authorization", "Bearer $token")
                connectTimeout = 4000
                readTimeout = 7000
            }
            if (conn.responseCode !in 200..299) return@withContext null
            val json = JSONObject(BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() })
            val top = json.optJSONArray("top_resources") ?: JSONArray()
            AdminOverview(
                json.optInt("active_students"), json.optInt("career_resources"),
                json.optInt("chats_this_week"), json.optInt("flagged_responses"),
                (0 until top.length()).map { top.getString(it) }
            )
        } catch (_: Exception) { null }
    }

    suspend fun getAdminStudents(token: String): List<StudentAccount>? = withContext(Dispatchers.IO) {
        try {
            val conn = (endpointUrl("/admin/students").openConnection() as HttpURLConnection).apply {
                setRequestProperty("Authorization", "Bearer $token")
                connectTimeout = 4000
                readTimeout = 7000
            }
            if (conn.responseCode !in 200..299) return@withContext null
            val array = JSONArray(BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() })
            buildList {
                for (i in 0 until array.length()) {
                    val user = array.getJSONObject(i)
                    add(StudentAccount(
                        user.optString("full_name"), user.optString("email"),
                        user.optString("course").takeUnless { it == "null" }.orEmpty(),
                        if (user.optBoolean("is_active")) "Active" else "Inactive",
                        userId = user.optString("user_id")
                    ))
                }
            }
        } catch (_: Exception) { null }
    }

    suspend fun assessCareer(
        token: String, skills: List<String>, interests: List<String>, activities: List<String>,
        course: String = "", careerGoal: String = ""
    ): CareerAssessmentResult? = withContext(Dispatchers.IO) {
        try {
            val conn = (endpointUrl("/career/assess").openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 5000
                readTimeout = 15000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Authorization", "Bearer $token")
            }
            val body = JSONObject()
                .put("course", course)
                .put("career_goal", careerGoal)
                .put("skills", JSONArray(skills))
                .put("interests", JSONArray(interests))
                .put("preferred_activities", JSONArray(activities))
            OutputStreamWriter(conn.outputStream).use { it.write(body.toString()) }
            if (conn.responseCode !in 200..299) return@withContext null
            val json = JSONObject(BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() })
            val matches = json.getJSONArray("recommendations")
            val results = buildList {
                for (i in 0 until matches.length()) {
                    val match = matches.getJSONObject(i)
                    fun strings(key: String): List<String> {
                        val values = match.optJSONArray(key) ?: JSONArray()
                        return (0 until values.length()).map { values.getString(it) }
                    }
                    add(CareerPathMatch(
                        match.getString("role"), match.getInt("fit_score"),
                        strings("matching_evidence"), strings("skills_to_explore"),
                        strings("next_steps"), strings("related_resources"),
                        match.optString("role_summary"), strings("entry_level_roles"),
                        strings("application_channel_types"), strings("sample_interview_questions"),
                        match.optString("cv_tailoring_guidance"), strings("progression_options"),
                        match.optString("requirements_and_qualification_notes")
                    ))
                }
            }
            CareerAssessmentResult(
                json.optString("profile_completeness"), json.optString("summary"),
                results, json.optString("information_note")
            )
        } catch (_: Exception) { null }
    }

    suspend fun createResource(token: String, title: String, category: String, content: String): CareerResource? = withContext(Dispatchers.IO) {
        try {
            val conn = (endpointUrl("/resources").openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 4000
                readTimeout = 7000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Authorization", "Bearer $token")
            }
            val body = JSONObject().put("title", title).put("category", category).put("content", content)
            OutputStreamWriter(conn.outputStream).use { it.write(body.toString()) }
            if (conn.responseCode !in 200..299) return@withContext null
            val json = JSONObject(BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() })
            CareerResource(json.getString("resource_id"), json.getString("title"), json.getString("category"), json.getString("content"))
        } catch (_: Exception) { null }
    }

    // ---- Career catalogue ----

    private suspend fun getJsonText(path: String, token: String, readTimeoutMs: Int = 10000): String? = withContext(Dispatchers.IO) {
        try {
            val conn = (endpointUrl(path).openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 5000
                readTimeout = readTimeoutMs
                setRequestProperty("Accept", "application/json")
                setRequestProperty("Authorization", "Bearer $token")
            }
            try {
                if (conn.responseCode !in 200..299) null
                else BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() }
            } finally {
                conn.disconnect()
            }
        } catch (_: Exception) {
            null
        }
    }

    private fun jsonStrings(json: JSONObject, key: String): List<String> {
        val values = json.optJSONArray(key) ?: JSONArray()
        return (0 until values.length()).map { values.optString(it) }
    }

    suspend fun getCareerCategories(token: String): List<CareerCategory>? {
        val text = getJsonText("/careers/categories", token) ?: return null
        return runCatching {
            val array = JSONObject(text).getJSONArray("categories")
            (0 until array.length()).map { index ->
                val item = array.getJSONObject(index)
                CareerCategory(item.getString("category"), item.optInt("career_count"))
            }
        }.getOrNull()
    }

    suspend fun searchCareers(
        token: String, category: String?, query: String, offset: Int = 0, limit: Int = 50
    ): CareerPage? {
        val params = buildList {
            if (!category.isNullOrBlank()) add("category=" + URLEncoder.encode(category, "UTF-8"))
            if (query.isNotBlank()) add("q=" + URLEncoder.encode(query.trim().take(80), "UTF-8"))
            add("limit=$limit")
            add("offset=$offset")
        }.joinToString("&")
        val text = getJsonText("/careers?$params", token) ?: return null
        return runCatching {
            val json = JSONObject(text)
            val array = json.getJSONArray("items")
            CareerPage(
                total = json.optInt("total"),
                items = (0 until array.length()).map { index ->
                    val item = array.getJSONObject(index)
                    CareerSummary(
                        careerId = item.getString("career_id"),
                        roleTitle = item.getString("role_title"),
                        category = item.optString("category"),
                        specialisation = item.optString("specialisation"),
                        coreSkills = jsonStrings(item, "core_skills"),
                        commonlyRegulated = item.optBoolean("commonly_regulated")
                    )
                }
            )
        }.getOrNull()
    }

    suspend fun getCareerDetail(token: String, careerId: String): CareerDetail? {
        val text = getJsonText("/careers/" + URLEncoder.encode(careerId, "UTF-8"), token) ?: return null
        return runCatching {
            val json = JSONObject(text)
            val education = json.optJSONObject("education") ?: JSONObject()
            val pathway = json.optJSONArray("pathway") ?: JSONArray()
            val opportunities = json.optJSONArray("opportunities") ?: JSONArray()
            val sources = json.optJSONArray("official_sources") ?: JSONArray()
            CareerDetail(
                careerId = json.getString("career_id"),
                roleTitle = json.getString("role_title"),
                category = json.optString("category"),
                specialisation = json.optString("specialisation"),
                description = json.optString("description"),
                commonlyRegulated = json.optBoolean("commonly_regulated"),
                coreSkills = jsonStrings(json, "core_skills"),
                preferredSkills = jsonStrings(json, "preferred_skills"),
                transferableSkills = jsonStrings(json, "transferable_skills"),
                studyAreas = education.optString("typical_study_areas"),
                qualificationLevels = education.optString("typical_qualification_levels"),
                certifications = education.optString("example_certifications"),
                verifyWith = education.optString("verify_with"),
                verificationNote = education.optString("verification_note"),
                pathway = (0 until pathway.length()).map { index ->
                    val item = pathway.getJSONObject(index)
                    PathwayStage(
                        stageNumber = item.optInt("stage_number"),
                        stageName = item.optString("stage_name"),
                        exampleTitle = item.optString("example_title"),
                        opportunityType = item.optString("opportunity_type"),
                        typicalTiming = item.optString("typical_timing"),
                        whatToBuild = item.optString("what_to_build")
                    )
                },
                opportunities = (0 until opportunities.length()).map { index ->
                    val item = opportunities.getJSONObject(index)
                    OpportunityTemplate(
                        opportunityType = item.optString("opportunity_type"),
                        market = item.optString("market"),
                        exampleTitle = item.optString("example_title"),
                        employerType = item.optString("employer_type"),
                        eligibility = item.optString("eligibility"),
                        typicalDuration = item.optString("typical_duration"),
                        typicalTiming = item.optString("typical_timing"),
                        applicantsUsuallyShow = item.optString("applicants_usually_show"),
                        documentsUsuallyRequested = item.optString("documents_usually_requested"),
                        whereAdvertised = item.optString("where_advertised"),
                        notes = item.optString("notes")
                    )
                },
                officialSources = (0 until sources.length()).map { index ->
                    val item = sources.getJSONObject(index)
                    OfficialSource(
                        name = item.optString("source_name"),
                        url = item.optString("url"),
                        whatToCheck = item.optString("what_to_check"),
                        roleSpecific = item.optBoolean("role_specific")
                    )
                },
                informationNote = json.optString("information_note"),
                jobTitles = (json.optJSONObject("job_titles") ?: JSONObject()).let { titles ->
                    titles.keys().asSequence().associateWith { key -> jsonStrings(titles, key) }
                },
                tasks = jsonStrings(json, "day_to_day_tasks"),
                tools = jsonStrings(json, "tools"),
                relatedCareers = (json.optJSONArray("related_careers") ?: JSONArray()).let { items ->
                    (0 until items.length()).map { index ->
                        val item = items.getJSONObject(index)
                        RelatedCareer(
                            careerId = item.optString("career_id"),
                            roleTitle = item.optString("role_title"),
                            category = item.optString("category"),
                            commonGround = item.optString("common_ground")
                        )
                    }
                },
                employers = jsonStrings(json, "employers"),
                workingPatterns = jsonStrings(json, "working_patterns")
            )
        }.getOrNull()
    }

    // ---- CV builder and mock interviews ----

    private suspend fun postJsonText(
        path: String, token: String, body: JSONObject, readTimeoutMs: Int = 15000
    ): String? = withContext(Dispatchers.IO) {
        try {
            val conn = (endpointUrl(path).openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 8000
                readTimeout = readTimeoutMs
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Accept", "application/json")
                setRequestProperty("Authorization", "Bearer $token")
            }
            try {
                OutputStreamWriter(conn.outputStream).use { it.write(body.toString()) }
                if (conn.responseCode !in 200..299) null
                else BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() }
            } finally {
                conn.disconnect()
            }
        } catch (_: Exception) {
            null
        }
    }

    /** Returns the text for a key, or an empty string when it is missing or JSON null. */
    private fun jsonText(json: JSONObject, key: String): String =
        if (json.isNull(key)) "" else json.optString(key)

    private fun cvBody(request: CvRequest): JSONObject {
        val projects = JSONArray()
        request.projects.take(8).forEach { project ->
            projects.put(
                JSONObject()
                    .put("title", project.title.take(120))
                    .put("description", project.description.take(600))
            )
        }
        val experience = JSONArray()
        request.experience.take(8).forEach { entry ->
            experience.put(
                JSONObject()
                    .put("title", entry.title.take(120))
                    .put("organisation", entry.organisation.take(120))
                    .put("period", entry.period.take(60))
                    .put("highlights", JSONArray(entry.highlights.take(6)))
            )
        }
        val body = JSONObject()
            .put("final", true)
            .put("summary", request.summary.trim().take(800))
            .put("grade", request.grade.trim().take(60))
            .put("phone", request.phone.trim().take(40))
            .put("location", request.location.trim().take(120))
            .put("links", JSONArray(request.links.take(4)))
            .put("institution", request.institution.trim().take(150))
            .put("graduation_year", request.graduationYear.trim().take(10))
            .put("skills", JSONArray(request.skills.take(30)))
            .put("projects", projects)
            .put("experience", experience)
            .put("certifications", JSONArray(request.certifications.take(12)))
            .put("activities", JSONArray(request.activities.take(12)))
            .put("referees", JSONArray(request.referees.take(3)))
        if (request.targetOpportunity.isNotBlank()) body.put("target_opportunity", request.targetOpportunity)
        return body
    }

    /** Builds the send-ready, ATS-friendly CV from the student's details. */
    suspend fun buildCv(token: String, careerId: String, request: CvRequest): CvResult? {
        val text = postJsonText(
            "/careers/" + URLEncoder.encode(careerId, "UTF-8") + "/cv", token, cvBody(request)
        ) ?: return null
        return runCatching {
            val json = JSONObject(text)
            CvResult(
                roleTitle = json.optString("role_title"),
                markdown = json.getString("markdown"),
                matchedSkills = jsonStrings(json, "matched_skills"),
                skillsToBuild = jsonStrings(json, "skills_to_build"),
                tips = jsonStrings(json, "cv_tips"),
                note = jsonText(json, "note"),
                checklist = jsonStrings(json, "checklist")
            )
        }.getOrNull()
    }

    /** Fetches the same CV as a Word document. Returns null if the backend could not be reached. */
    suspend fun downloadCvDocx(token: String, careerId: String, request: CvRequest): ByteArray? =
        withContext(Dispatchers.IO) {
            try {
                val conn = (endpointUrl("/careers/" + URLEncoder.encode(careerId, "UTF-8") + "/cv/docx")
                    .openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 8000
                    readTimeout = 20000
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json")
                    setRequestProperty("Authorization", "Bearer $token")
                }
                try {
                    OutputStreamWriter(conn.outputStream).use { it.write(cvBody(request).toString()) }
                    if (conn.responseCode !in 200..299) null else conn.inputStream.use { it.readBytes() }
                } finally {
                    conn.disconnect()
                }
            } catch (_: Exception) {
                null
            }
        }

    private fun parseInterview(text: String): InterviewState? = runCatching {
        val json = JSONObject(text)
        val turns = json.optJSONArray("transcript") ?: JSONArray()
        InterviewState(
            interviewId = json.getString("interview_id"),
            roleTitle = json.optString("role_title"),
            status = json.optString("status"),
            questionNumber = json.optInt("question_number"),
            totalQuestions = json.optInt("total_questions"),
            interviewerMessage = jsonText(json, "interviewer_message"),
            transcript = (0 until turns.length()).map { index ->
                val turn = turns.getJSONObject(index)
                InterviewTurn(turn.optString("speaker"), turn.optString("kind"), turn.optString("text"))
            },
            feedback = jsonText(json, "feedback")
        )
    }.getOrNull()

    suspend fun startInterview(
        token: String, careerId: String, opportunityType: String, questionCount: Int
    ): InterviewState? {
        val body = JSONObject().put("career_id", careerId).put("question_count", questionCount)
        if (opportunityType.isNotBlank()) body.put("opportunity_type", opportunityType)
        return postJsonText("/interviews", token, body, readTimeoutMs = 20000)?.let(::parseInterview)
    }

    suspend fun answerInterview(token: String, interviewId: String, answer: String): InterviewState? {
        val body = JSONObject().put("answer", answer.trim().take(4000))
        // The interviewer's reply may wait on Gemini and its fallback model.
        return postJsonText("/interviews/$interviewId/answer", token, body, readTimeoutMs = 90000)?.let(::parseInterview)
    }

    suspend fun finishInterview(token: String, interviewId: String): InterviewState? =
        postJsonText("/interviews/$interviewId/finish", token, JSONObject(), readTimeoutMs = 90000)?.let(::parseInterview)

    // ---- Administrator actions ----

    private suspend fun sendJsonText(
        method: String, path: String, token: String, body: JSONObject?
    ): String? = withContext(Dispatchers.IO) {
        try {
            val conn = (endpointUrl(path).openConnection() as HttpURLConnection).apply {
                requestMethod = method
                connectTimeout = 5000
                readTimeout = 10000
                setRequestProperty("Accept", "application/json")
                setRequestProperty("Authorization", "Bearer $token")
                if (body != null) {
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json")
                }
            }
            try {
                if (body != null) OutputStreamWriter(conn.outputStream).use { it.write(body.toString()) }
                val code = conn.responseCode
                when {
                    code !in 200..299 -> null
                    code == 204 -> ""
                    else -> BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() }
                }
            } finally {
                conn.disconnect()
            }
        } catch (_: Exception) {
            null
        }
    }

    suspend fun getResourceContent(token: String, resourceId: String): String? {
        val text = getJsonText("/resources/" + URLEncoder.encode(resourceId, "UTF-8"), token) ?: return null
        return runCatching { JSONObject(text).getString("content") }.getOrNull()
    }

    suspend fun updateResource(
        token: String, resourceId: String, title: String, category: String, content: String
    ): CareerResource? {
        val body = JSONObject().put("title", title).put("category", category).put("content", content)
        val text = sendJsonText("PUT", "/resources/" + URLEncoder.encode(resourceId, "UTF-8"), token, body)
            ?: return null
        return runCatching {
            val json = JSONObject(text)
            val saved = json.getString("content")
            val summary = saved.lines().map { it.trim() }
                .firstOrNull { it.isNotEmpty() && !it.startsWith("#") }.orEmpty().take(160)
            CareerResource(json.getString("resource_id"), json.getString("title"), json.getString("category"), summary)
        }.getOrNull()
    }

    suspend fun deleteResource(token: String, resourceId: String): Boolean =
        sendJsonText("DELETE", "/resources/" + URLEncoder.encode(resourceId, "UTF-8"), token, null) != null

    suspend fun setStudentActive(token: String, userId: String, active: Boolean): Boolean =
        sendJsonText(
            "PUT", "/admin/students/" + URLEncoder.encode(userId, "UTF-8") + "/status", token,
            JSONObject().put("is_active", active)
        ) != null

    suspend fun checkHealth(): Boolean = withContext(Dispatchers.IO) {
        candidateBaseUrls.any { checkHealthAt(it) }
    }

    suspend fun checkHealth(endpoint: String): Boolean {
        val normalized = normalizeEndpoint(endpoint) ?: return false
        return checkHealthAt(normalized)
    }

    suspend fun sendChatMessage(query: String, token: String, sessionId: String? = null): NetworkChatResponse? = withContext(Dispatchers.IO) {
        try {
            val url = endpointUrl("/chat")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 8000
                // Gemini may retry a temporarily overloaded model before using the fallback model.
                readTimeout = 90000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Accept", "application/json")
                setRequestProperty("Authorization", "Bearer $token")
            }

            val body = JSONObject().apply {
                put("query", query)
                if (!sessionId.isNullOrBlank()) {
                    put("session_id", sessionId)
                }
            }

            OutputStreamWriter(conn.outputStream).use { writer ->
                writer.write(body.toString())
                writer.flush()
            }

            val statusCode = conn.responseCode
            if (statusCode in 200..299) {
                val responseText = BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() }
                val json = JSONObject(responseText)
                val resp = json.optString("response", "")
                val sessId = json.optString("session_id", "")
                val sourcesArray = json.optJSONArray("sources") ?: JSONArray()
                val sourcesList = mutableListOf<String>()
                for (i in 0 until sourcesArray.length()) {
                    sourcesList.add(sourcesArray.getString(i))
                }
                NetworkChatResponse(sessId, resp, sourcesList)
            } else {
                Log.w("ApiClient", "Chat endpoint returned HTTP $statusCode")
                null
            }
        } catch (e: Exception) {
            Log.e("ApiClient", "Chat request failed (${e.javaClass.simpleName})", e)
            null
        }
    }

    suspend fun submitFeedback(
        rating: Int,
        isAccurate: Boolean,
        comments: String,
        token: String,
        sessionId: String? = null
    ): Boolean = withContext(Dispatchers.IO) {
        try {
            val url = endpointUrl("/feedback")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 5000
                readTimeout = 5000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Authorization", "Bearer $token")
            }

            val body = JSONObject().apply {
                put("rating", rating)
                put("is_accurate", isAccurate)
                put("comments", comments)
                if (!sessionId.isNullOrBlank()) {
                    put("session_id", sessionId)
                }
            }

            OutputStreamWriter(conn.outputStream).use { writer ->
                writer.write(body.toString())
                writer.flush()
            }

            conn.responseCode in 200..299
        } catch (e: Exception) {
            false
        }
    }
}
