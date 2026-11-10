package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.CareerAssessmentResult
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary
import kotlinx.coroutines.launch

@Composable
fun CareerAssessmentScreen(session: UserSession, onBack: () -> Unit = {}) {
    var skills by remember { mutableStateOf("") }
    var interests by remember { mutableStateOf("") }
    var activities by remember { mutableStateOf("") }
    var course by remember { mutableStateOf(session.course) }
    var careerGoal by remember { mutableStateOf(session.careerGoal) }
    var result by remember { mutableStateOf<CareerAssessmentResult?>(null) }
    val expandedPathRoles = remember { mutableStateListOf<String>() }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(title = "Explore career paths", subtitle = "Based on the evidence you share", onBack = onBack, showProfile = false)
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Text("Start with your course or a career you are considering. Add skills, interests, and activities for more useful matches.", color = TextSecondary)
            OutlinedTextField(course, { course = it }, label = { Text("What course are you studying or have you completed?") }, placeholder = { Text("e.g. Law, Nursing, Business, Computer Science") }, modifier = Modifier.fillMaxWidth(), minLines = 1)
            OutlinedTextField(careerGoal, { careerGoal = it }, label = { Text("Career you want to explore (optional)") }, placeholder = { Text("e.g. Banking, teaching, medicine, software") }, modifier = Modifier.fillMaxWidth(), minLines = 1)
            OutlinedTextField(skills, { skills = it }, label = { Text("Skills") }, placeholder = { Text("Python, writing, teamwork") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
            OutlinedTextField(interests, { interests = it }, label = { Text("Interests") }, placeholder = { Text("Data, design, helping people") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
            OutlinedTextField(activities, { activities = it }, label = { Text("Activities you enjoy") }, placeholder = { Text("Solving problems, presenting ideas") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            PrimaryButton(text = if (loading) "Assessing…" else "Show career matches", enabled = !loading) {
                val skillList = splitAnswers(skills)
                val interestList = splitAnswers(interests)
                val activityList = splitAnswers(activities)
                if (course.isBlank() && careerGoal.isBlank() && skillList.isEmpty() && interestList.isEmpty() && activityList.isEmpty()) {
                    error = "Add your course, a career goal, a skill, an interest, or an activity."
                } else {
                    loading = true
                    error = null
                    scope.launch {
                        result = ApiClient.assessCareer(session.token, skillList, interestList, activityList, course.trim(), careerGoal.trim())
                        loading = false
                        if (result == null) error = "The assessment could not be saved. Check that the backend is running and try again."
                    }
                }
            }
            result?.let { assessment ->
                Text(assessment.summary, style = MaterialTheme.typography.titleMedium)
                Text("Profile detail: ${assessment.profileCompleteness}", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                assessment.recommendations.forEach { match ->
                    SectionCard {
                        Text(match.role, style = MaterialTheme.typography.titleLarge)
                        Text("Answer overlap: ${match.fitScore}/100", style = MaterialTheme.typography.labelLarge)
                        match.roleSummary.takeIf { it.isNotBlank() }?.let {
                            Text(it, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                        }
                        if (match.matchingEvidence.isNotEmpty()) {
                            GuidanceListSection("Your matching answers", match.matchingEvidence)
                        }
                        if (match.skillsToExplore.isNotEmpty()) {
                            GuidanceListSection("Skills to explore", match.skillsToExplore)
                        }
                        if (match.nextSteps.isNotEmpty()) {
                            GuidanceListSection("Preparation and project ideas", match.nextSteps)
                        }
                        TextButton(onClick = {
                            if (match.role in expandedPathRoles) expandedPathRoles.remove(match.role)
                            else expandedPathRoles.add(match.role)
                        }) {
                            Text(if (match.role in expandedPathRoles) "Hide pathway details" else "Explore pathway details")
                        }
                        if (match.role in expandedPathRoles) {
                            if (match.entryLevelRoles.isNotEmpty()) {
                                GuidanceListSection("Example entry-level roles", match.entryLevelRoles)
                            }
                            match.requirementsAndQualificationNotes.takeIf { it.isNotBlank() }?.let {
                                GuidanceTextSection("Study and requirements to verify", it)
                            }
                            if (match.applicationChannelTypes.isNotEmpty()) {
                                GuidanceListSection("Application channel ideas (not live listings)", match.applicationChannelTypes)
                            }
                            if (match.sampleInterviewQuestions.isNotEmpty()) {
                                GuidanceListSection("Interview practice", match.sampleInterviewQuestions)
                            }
                            match.cvTailoringGuidance.takeIf { it.isNotBlank() }?.let {
                                GuidanceTextSection("CV tailoring", it)
                            }
                            if (match.progressionOptions.isNotEmpty()) {
                                GuidanceListSection("Possible progression", match.progressionOptions)
                            }
                        }
                        if (match.relatedResources.isNotEmpty()) {
                            Spacer(Modifier.height(8.dp))
                            Text("Related resources: ${match.relatedResources.joinToString()}", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                        }
                    }
                }
                Text(assessment.informationNote, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
            }
            Spacer(Modifier.height(18.dp))
        }
    }
}

@Composable
private fun GuidanceListSection(title: String, items: List<String>) {
    Spacer(Modifier.height(8.dp))
    Text(title, style = MaterialTheme.typography.titleSmall)
    items.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
}

@Composable
private fun GuidanceTextSection(title: String, content: String) {
    Spacer(Modifier.height(8.dp))
    Text(title, style = MaterialTheme.typography.titleSmall)
    Text(content, style = MaterialTheme.typography.bodySmall)
}

private fun splitAnswers(value: String): List<String> = value.split(",")
    .map { it.trim() }
    .filter { it.isNotEmpty() }
    .distinctBy { it.lowercase() }
    .take(20)

@Preview(showBackground = true)
@Composable
private fun CareerAssessmentPreview() {
    AICareerCoachTheme { CareerAssessmentScreen(UserSession("Student", "student@example.edu")) }
}
