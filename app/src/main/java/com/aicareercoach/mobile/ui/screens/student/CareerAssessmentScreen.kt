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
    var result by remember { mutableStateOf<CareerAssessmentResult?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(title = "Explore career paths", subtitle = "Based on the evidence you share", onBack = onBack, showProfile = false)
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Text("Add skills, interests, and activities separated by commas. Share only what you are comfortable sharing.", color = TextSecondary)
            OutlinedTextField(skills, { skills = it }, label = { Text("Skills") }, placeholder = { Text("Python, writing, teamwork") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
            OutlinedTextField(interests, { interests = it }, label = { Text("Interests") }, placeholder = { Text("Data, design, helping people") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
            OutlinedTextField(activities, { activities = it }, label = { Text("Activities you enjoy") }, placeholder = { Text("Solving problems, presenting ideas") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            PrimaryButton(text = if (loading) "Assessing…" else "Show career matches", enabled = !loading) {
                val skillList = splitAnswers(skills)
                val interestList = splitAnswers(interests)
                val activityList = splitAnswers(activities)
                if (skillList.isEmpty() && interestList.isEmpty() && activityList.isEmpty()) {
                    error = "Add at least one skill, interest, or activity."
                } else {
                    loading = true
                    error = null
                    scope.launch {
                        result = ApiClient.assessCareer(session.token, skillList, interestList, activityList)
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
                        Text("Relative fit: ${match.fitScore}/100", style = MaterialTheme.typography.labelLarge)
                        if (match.matchingEvidence.isNotEmpty()) {
                            Spacer(Modifier.height(8.dp))
                            Text("Evidence", style = MaterialTheme.typography.titleSmall)
                            match.matchingEvidence.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
                        }
                        if (match.skillsToExplore.isNotEmpty()) {
                            Spacer(Modifier.height(8.dp))
                            Text("Skills to explore", style = MaterialTheme.typography.titleSmall)
                            Text(match.skillsToExplore.joinToString(", "), style = MaterialTheme.typography.bodySmall)
                        }
                        if (match.nextSteps.isNotEmpty()) {
                            Spacer(Modifier.height(8.dp))
                            Text("Next steps", style = MaterialTheme.typography.titleSmall)
                            match.nextSteps.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
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
