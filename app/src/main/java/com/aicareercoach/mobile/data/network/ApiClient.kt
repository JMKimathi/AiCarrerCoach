package com.aicareercoach.mobile.data.network

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import android.util.Log
import com.aicareercoach.mobile.data.AuthResult
import com.aicareercoach.mobile.data.AdminOverview
import com.aicareercoach.mobile.data.CareerResource
import com.aicareercoach.mobile.data.CareerAssessmentResult
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

data class NetworkChatResponse(
    val sessionId: String,
    val response: String,
    val sources: List<String>
)

object ApiClient {
    // Physical-device development: use the PC's Wi-Fi IPv4 address. For an Android emulator,
    // switch this to 10.0.2.2, which routes to the host machine.
    var baseUrl: String = "http://192.168.100.3:8000/api"

    suspend fun authenticate(
        register: Boolean, name: String, email: String, password: String, course: String = "", careerGoal: String = ""
    ): AuthResult = withContext(Dispatchers.IO) {
        try {
            val path = if (register) "register" else "login"
            val conn = (URL("$baseUrl/auth/$path").openConnection() as HttpURLConnection).apply {
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
            val conn = (URL("$baseUrl/auth/me").openConnection() as HttpURLConnection).apply {
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
            val conn = (URL("$baseUrl/resources").openConnection() as HttpURLConnection).apply {
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
            val conn = (URL("$baseUrl/admin/overview").openConnection() as HttpURLConnection).apply {
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
            val conn = (URL("$baseUrl/admin/students").openConnection() as HttpURLConnection).apply {
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
                        if (user.optBoolean("is_active")) "Active" else "Inactive"
                    ))
                }
            }
        } catch (_: Exception) { null }
    }

    suspend fun assessCareer(
        token: String, skills: List<String>, interests: List<String>, activities: List<String>
    ): CareerAssessmentResult? = withContext(Dispatchers.IO) {
        try {
            val conn = (URL("$baseUrl/career/assess").openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 5000
                readTimeout = 15000
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Authorization", "Bearer $token")
            }
            val body = JSONObject()
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
                        strings("next_steps"), strings("related_resources")
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
            val conn = (URL("$baseUrl/resources").openConnection() as HttpURLConnection).apply {
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

    suspend fun checkHealth(): Boolean = withContext(Dispatchers.IO) {
        try {
            val url = URL("$baseUrl/health")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 3000
                readTimeout = 3000
            }
            conn.responseCode == 200
        } catch (e: Exception) {
            false
        }
    }

    suspend fun sendChatMessage(query: String, token: String, sessionId: String? = null): NetworkChatResponse? = withContext(Dispatchers.IO) {
        try {
            val url = URL("$baseUrl/chat")
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
            val url = URL("$baseUrl/feedback")
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
