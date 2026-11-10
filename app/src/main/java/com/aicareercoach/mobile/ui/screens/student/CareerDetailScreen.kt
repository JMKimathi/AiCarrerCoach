package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.CareerDetail
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.components.SecondaryButton
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.components.Tag
import com.aicareercoach.mobile.ui.theme.*

/** Everything the catalogue holds about one career: skills, study routes, pathway, opportunities and sources. */
@Composable
fun CareerDetailScreen(
    session: UserSession,
    careerId: String,
    onBack: () -> Unit = {},
    onAskCoach: (String) -> Unit = {},
    onBuildCv: (String) -> Unit = {},
    onPractiseInterview: (String) -> Unit = {}
) {
    var detail by remember { mutableStateOf<CareerDetail?>(null) }
    var loading by remember { mutableStateOf(true) }
    val uriHandler = LocalUriHandler.current

    LaunchedEffect(session.token, careerId) {
        loading = true
        detail = ApiClient.getCareerDetail(session.token, careerId)
        loading = false
    }

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        val current = detail
        AppTopBar(
            title = current?.roleTitle ?: "Career",
            subtitle = current?.category,
            onBack = onBack,
            showProfile = false
        )

        if (current == null) {
            Text(
                if (loading) "Loading career…"
                else "This career could not be loaded. Check that the backend is running and try again.",
                modifier = Modifier.padding(horizontal = 20.dp),
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary
            )
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                SectionCard {
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        Tag(current.specialisation, BluePrimary)
                        if (current.commonlyRegulated) Tag("Regulated profession", WarningAmber)
                    }
                    Spacer(Modifier.height(10.dp))
                    Text(current.description, style = MaterialTheme.typography.bodyMedium)
                }

                DetailSection("Skills") {
                    LabeledText("Core", current.coreSkills.joinToString(", "))
                    LabeledText("Helpful", current.preferredSkills.joinToString(", "))
                    LabeledText("Transferable", current.transferableSkills.joinToString(", "))
                }

                DetailSection("Education and qualifications") {
                    LabeledText("Typical study areas", current.studyAreas)
                    LabeledText("Qualification levels", current.qualificationLevels)
                    LabeledText("Certifications to explore", current.certifications)
                    LabeledText("Confirm requirements with", current.verifyWith)
                    if (current.verificationNote.isNotBlank()) {
                        Spacer(Modifier.height(6.dp))
                        Text(current.verificationNote, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                    }
                }

                DetailSection("Pathway") {
                    current.pathway.forEach { stage ->
                        Text(
                            "${stage.stageNumber}. ${stage.stageName}",
                            style = MaterialTheme.typography.titleSmall
                        )
                        Text(
                            "${stage.exampleTitle} · ${stage.opportunityType}",
                            style = MaterialTheme.typography.bodySmall,
                            color = BluePrimary
                        )
                        Text(stage.typicalTiming, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                        Text(stage.whatToBuild, style = MaterialTheme.typography.bodySmall)
                        Spacer(Modifier.height(10.dp))
                    }
                }

                DetailSection("Typical opportunities") {
                    Text(
                        "These describe what such openings usually look like. They are not live vacancies.",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary
                    )
                    Spacer(Modifier.height(8.dp))
                    current.opportunities.forEach { opportunity ->
                        Text(
                            "${opportunity.opportunityType.replaceFirstChar { it.uppercase() }} · ${opportunity.market}",
                            style = MaterialTheme.typography.titleSmall
                        )
                        LabeledText("Example title", opportunity.exampleTitle)
                        LabeledText("Kind of employer", opportunity.employerType)
                        LabeledText("Who applies", opportunity.eligibility)
                        LabeledText("Length", opportunity.typicalDuration)
                        LabeledText("Timing", opportunity.typicalTiming)
                        LabeledText("Applicants usually show", opportunity.applicantsUsuallyShow)
                        LabeledText("Documents", opportunity.documentsUsuallyRequested)
                        LabeledText("Where advertised", opportunity.whereAdvertised)
                        LabeledText("Note", opportunity.notes)
                        Spacer(Modifier.height(12.dp))
                    }
                }

                DetailSection("Official sources to check") {
                    current.officialSources.forEach { source ->
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { runCatching { uriHandler.openUri(source.url) } }
                                .padding(vertical = 6.dp)
                        ) {
                            Text(
                                source.name,
                                style = MaterialTheme.typography.titleSmall,
                                color = BluePrimary
                            )
                            Text(source.whatToCheck, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                        }
                    }
                }

                PrimaryButton(
                    text = "Build my CV for this career",
                    onClick = { onBuildCv(current.careerId) }
                )
                SecondaryButton(
                    text = "Practise a mock interview",
                    onClick = { onPractiseInterview(current.careerId) }
                )
                SecondaryButton(
                    text = "Ask the coach about this career",
                    onClick = { onAskCoach("Tell me about a career as ${current.roleTitle}") }
                )

                if (current.informationNote.isNotBlank()) {
                    Text(current.informationNote, style = MaterialTheme.typography.bodySmall, color = TextMuted)
                }
                Spacer(Modifier.height(20.dp))
            }
        }
    }
}

@Composable
private fun DetailSection(title: String, content: @Composable ColumnScope.() -> Unit) {
    SectionCard {
        Text(title, style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(8.dp))
        content()
    }
}

@Composable
private fun LabeledText(label: String, value: String) {
    if (value.isBlank()) return
    Text(label, style = MaterialTheme.typography.labelMedium, color = TextSecondary)
    Text(value, style = MaterialTheme.typography.bodyMedium)
    Spacer(Modifier.height(6.dp))
}
