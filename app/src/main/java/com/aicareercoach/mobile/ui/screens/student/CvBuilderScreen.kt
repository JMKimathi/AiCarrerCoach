package com.aicareercoach.mobile.ui.screens.student

import android.content.Intent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.CvExperience
import com.aicareercoach.mobile.data.CvProject
import com.aicareercoach.mobile.data.CvRequest
import com.aicareercoach.mobile.data.CvResult
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.components.SecondaryButton
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.*
import kotlinx.coroutines.launch

private val cvOpportunityChoices = listOf(
    "" to "Any",
    "industrial attachment" to "Attachment",
    "internship" to "Internship",
    "graduate programme" to "Graduate programme",
    "full-time job" to "Full-time job"
)

private fun splitList(text: String): List<String> =
    text.split(",", "\n").map { it.trim() }.filter { it.isNotEmpty() }

private fun parseProjects(text: String): List<CvProject> =
    text.lines().map { it.trim() }.filter { it.isNotEmpty() }.map { line ->
        val parts = line.split(" - ", limit = 2)
        CvProject(parts[0].trim(), parts.getOrElse(1) { "" }.trim())
    }

private fun parseExperience(text: String): List<CvExperience> =
    text.lines().map { it.trim() }.filter { it.isNotEmpty() }.map { line ->
        val parts = line.split(" - ", limit = 4).map { it.trim() }
        CvExperience(
            title = parts[0],
            organisation = parts.getOrElse(1) { "" },
            period = parts.getOrElse(2) { "" },
            highlights = listOfNotNull(parts.getOrNull(3)?.takeIf { it.isNotEmpty() })
        )
    }

/** Collects a student's details and shows a CV laid out for the chosen career. */
@Composable
fun CvBuilderScreen(
    session: UserSession,
    careerId: String,
    onBack: () -> Unit = {}
) {
    var roleTitle by remember { mutableStateOf("") }
    var phone by rememberSaveable { mutableStateOf("") }
    var location by rememberSaveable { mutableStateOf("") }
    var institution by rememberSaveable { mutableStateOf("") }
    var graduationYear by rememberSaveable { mutableStateOf("") }
    var opportunity by rememberSaveable { mutableStateOf("") }
    var skillsText by rememberSaveable { mutableStateOf("") }
    var projectsText by rememberSaveable { mutableStateOf("") }
    var experienceText by rememberSaveable { mutableStateOf("") }
    var certificationsText by rememberSaveable { mutableStateOf("") }
    var building by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var result by remember { mutableStateOf<CvResult?>(null) }
    val scope = rememberCoroutineScope()
    val clipboard = LocalClipboardManager.current
    val context = LocalContext.current

    LaunchedEffect(session.token, careerId) {
        ApiClient.getCareerDetail(session.token, careerId)?.let { roleTitle = it.roleTitle }
    }

    fun build() {
        if (building) return
        building = true
        error = null
        scope.launch {
            val built = ApiClient.buildCv(
                session.token, careerId,
                CvRequest(
                    phone = phone,
                    location = location,
                    institution = institution,
                    graduationYear = graduationYear,
                    targetOpportunity = opportunity,
                    skills = splitList(skillsText),
                    projects = parseProjects(projectsText),
                    experience = parseExperience(experienceText),
                    certifications = splitList(certificationsText)
                )
            )
            if (built == null) {
                error = "The CV could not be built. Check that the backend is running and try again."
            } else {
                result = built
            }
            building = false
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
            .imePadding()
    ) {
        AppTopBar(
            title = "CV Builder",
            subtitle = if (roleTitle.isBlank()) null else roleTitle,
            onBack = onBack,
            showProfile = false
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            val current = result
            if (current == null) {
                Text(
                    "Your name, email and course come from your profile. Add what you can below; anything you " +
                        "leave out becomes a prompt on the CV telling you what to add.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary
                )

                SectionCard {
                    Text("Applying for", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        cvOpportunityChoices.forEach { (value, label) ->
                            CvChoiceChip(label, selected = opportunity == value) { opportunity = value }
                        }
                    }
                }

                SectionCard {
                    Text("Contact and education", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    CvField("Phone", phone, { phone = it }, "e.g. 07XX XXX XXX")
                    CvField("Location", location, { location = it }, "e.g. Nairobi, Kenya")
                    CvField("Institution", institution, { institution = it }, "e.g. Strathmore University")
                    CvField("Graduation year", graduationYear, { graduationYear = it }, "e.g. 2027")
                }

                SectionCard {
                    Text("Skills and experience", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    CvField("Skills", skillsText, { skillsText = it }, "Separate with commas", lines = 2)
                    CvField(
                        "Projects", projectsText, { projectsText = it },
                        "One per line: Title - what you built and the result", lines = 3
                    )
                    CvField(
                        "Experience and attachments", experienceText, { experienceText = it },
                        "One per line: Role - Organisation - Period - what you did", lines = 3
                    )
                    CvField(
                        "Certifications", certificationsText, { certificationsText = it },
                        "Separate with commas", lines = 2
                    )
                }

                val message = error
                if (message != null) {
                    Text(message, style = MaterialTheme.typography.bodyMedium, color = DangerRed)
                }
                PrimaryButton(
                    text = if (building) "Building…" else "Build my CV",
                    enabled = !building,
                    onClick = { build() }
                )
            } else {
                SectionCard {
                    CvMarkdown(current.markdown)
                }
                if (current.matchedSkills.isNotEmpty()) {
                    SectionCard {
                        Text("Skills you already have for this role", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(6.dp))
                        Text(current.matchedSkills.joinToString(", "), style = MaterialTheme.typography.bodyMedium)
                    }
                }
                if (current.skillsToBuild.isNotEmpty()) {
                    SectionCard {
                        Text("Skills to build next", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(6.dp))
                        Text(current.skillsToBuild.joinToString(", "), style = MaterialTheme.typography.bodyMedium)
                    }
                }
                if (current.tips.isNotEmpty()) {
                    SectionCard {
                        Text("CV tips", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(6.dp))
                        current.tips.forEach { tip ->
                            Text("•  $tip", style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
                if (current.note.isNotBlank()) {
                    Text(current.note, style = MaterialTheme.typography.bodySmall, color = TextMuted)
                }
                PrimaryButton(
                    text = "Copy CV text",
                    onClick = { clipboard.setText(AnnotatedString(current.markdown)) }
                )
                SecondaryButton(
                    text = "Share CV",
                    onClick = {
                        val send = Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_TEXT, current.markdown)
                        }
                        runCatching { context.startActivity(Intent.createChooser(send, "Share CV")) }
                    }
                )
                SecondaryButton(text = "Edit my details", onClick = { result = null })
            }
            Spacer(Modifier.height(20.dp))
        }
    }
}

@Composable
private fun CvField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    lines: Int = 1
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        placeholder = { Text(placeholder) },
        singleLine = lines == 1,
        minLines = lines,
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth()
    )
    Spacer(Modifier.height(8.dp))
}

@Composable
private fun CvChoiceChip(label: String, selected: Boolean, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(if (selected) BluePrimary else SurfaceAlt)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        Text(
            label,
            style = MaterialTheme.typography.labelLarge,
            color = if (selected) Color.White else TextSecondary
        )
    }
}

/** Shows the CV's simple Markdown (headings, bullets, notes) as formatted text. */
@Composable
private fun CvMarkdown(markdown: String) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        markdown.lines().forEach { raw ->
            val line = raw.replace("**", "")
            when {
                line.isBlank() -> Spacer(Modifier.height(4.dp))
                line.startsWith("## ") -> Text(
                    line.removePrefix("## "),
                    style = MaterialTheme.typography.titleMedium,
                    color = BluePrimary
                )
                line.startsWith("# ") -> Text(line.removePrefix("# "), style = MaterialTheme.typography.headlineSmall)
                line.startsWith("- ") -> Text("•  " + line.removePrefix("- "), style = MaterialTheme.typography.bodyMedium)
                line.startsWith("> ") -> Text(
                    line.removePrefix("> "),
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary
                )
                else -> Text(line, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
