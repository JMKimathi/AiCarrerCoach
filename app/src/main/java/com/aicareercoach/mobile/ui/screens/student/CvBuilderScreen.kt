package com.aicareercoach.mobile.ui.screens.student

import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.CvExperience
import com.aicareercoach.mobile.data.CvPdfWriter
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

private const val DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

private val cvOpportunityChoices = listOf(
    "" to "Any",
    "industrial attachment" to "Attachment",
    "internship" to "Internship",
    "graduate programme" to "Graduate programme",
    "full-time job" to "Full-time job"
)

// What the student is typing for one role or one project, before it is sent.
private data class ExperienceDraft(
    val title: String = "",
    val organisation: String = "",
    val period: String = "",
    val achievements: String = ""
)

private data class ProjectDraft(val title: String = "", val description: String = "")

private fun splitList(text: String): List<String> =
    text.split(",", "\n").map { it.trim() }.filter { it.isNotEmpty() }

private fun splitLines(text: String): List<String> =
    text.lines().map { it.trim().removePrefix("-").trim() }.filter { it.isNotEmpty() }

/**
 * Collects a student's details section by section and returns a CV that is ready to send:
 * one column, standard headings and plain text, which applicant tracking systems read reliably.
 */
@Composable
fun CvBuilderScreen(
    session: UserSession,
    careerId: String,
    onBack: () -> Unit = {}
) {
    var roleTitle by remember { mutableStateOf("") }
    var summary by rememberSaveable { mutableStateOf("") }
    var phone by rememberSaveable { mutableStateOf("") }
    var location by rememberSaveable { mutableStateOf("") }
    var link by rememberSaveable { mutableStateOf("") }
    var institution by rememberSaveable { mutableStateOf("") }
    var graduationYear by rememberSaveable { mutableStateOf("") }
    var grade by rememberSaveable { mutableStateOf("") }
    var opportunity by rememberSaveable { mutableStateOf("") }
    var skillsText by rememberSaveable { mutableStateOf("") }
    var certificationsText by rememberSaveable { mutableStateOf("") }
    var activitiesText by rememberSaveable { mutableStateOf("") }
    var refereesText by rememberSaveable { mutableStateOf("") }
    val experiences = remember { mutableStateListOf(ExperienceDraft()) }
    val projects = remember { mutableStateListOf(ProjectDraft()) }

    var building by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var result by remember { mutableStateOf<CvResult?>(null) }
    var lastRequest by remember { mutableStateOf<CvRequest?>(null) }
    var saveMessage by remember { mutableStateOf<String?>(null) }
    var savingWord by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val clipboard = LocalClipboardManager.current
    val context = LocalContext.current

    LaunchedEffect(session.token, careerId) {
        ApiClient.getCareerDetail(session.token, careerId)?.let { roleTitle = it.roleTitle }
    }

    fun currentRequest(): CvRequest = CvRequest(
        phone = phone,
        location = location,
        institution = institution,
        graduationYear = graduationYear,
        targetOpportunity = opportunity,
        skills = splitList(skillsText),
        projects = projects.filter { it.title.isNotBlank() }
            .map { CvProject(it.title.trim(), it.description.trim()) },
        experience = experiences.filter { it.title.isNotBlank() }.map {
            CvExperience(it.title.trim(), it.organisation.trim(), it.period.trim(), splitLines(it.achievements))
        },
        certifications = splitList(certificationsText),
        activities = splitLines(activitiesText),
        summary = summary,
        grade = grade,
        links = splitList(link),
        referees = splitLines(refereesText)
    )

    fun build() {
        if (building) return
        building = true
        error = null
        saveMessage = null
        val request = currentRequest()
        scope.launch {
            val built = ApiClient.buildCv(session.token, careerId, request)
            if (built == null) {
                error = "The CV could not be built. Check that the backend is running and try again."
            } else {
                lastRequest = request
                result = built
            }
            building = false
        }
    }

    // Both downloads open the phone's own "save file" screen, so no storage permission is needed.
    val savePdf = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/pdf")
    ) { uri ->
        val cv = result
        if (uri != null && cv != null) {
            saveMessage = runCatching {
                val stream = context.contentResolver.openOutputStream(uri)
                    ?: throw IllegalStateException("The chosen location could not be opened.")
                stream.use { CvPdfWriter.write(cv.markdown, it) }
            }.fold(
                onSuccess = { "Your CV was saved as a PDF." },
                onFailure = { "The PDF could not be saved. Try again or choose another folder." }
            )
        }
    }
    val saveWord = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument(DOCX_MIME)
    ) { uri ->
        val request = lastRequest
        if (uri != null && request != null) {
            savingWord = true
            scope.launch {
                val bytes = ApiClient.downloadCvDocx(session.token, careerId, request)
                saveMessage = if (bytes == null) {
                    "The Word file could not be fetched. Check that the backend is running and try again."
                } else {
                    runCatching {
                        val stream = context.contentResolver.openOutputStream(uri)
                            ?: throw IllegalStateException("The chosen location could not be opened.")
                        stream.use { it.write(bytes) }
                    }.fold(
                        onSuccess = { "Your CV was saved as a Word document." },
                        onFailure = { "The Word file could not be saved. Try again or choose another folder." }
                    )
                }
                savingWord = false
            }
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
                    "Fill in each section. Your name, email and course come from your profile. " +
                        "Sections you leave empty are left out of the CV.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary
                )

                FormSection("Applying for") {
                    Row(
                        modifier = Modifier.horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        cvOpportunityChoices.forEach { (value, label) ->
                            CvChoiceChip(label, selected = opportunity == value) { opportunity = value }
                        }
                    }
                }

                FormSection("Professional summary") {
                    CvField(
                        "Summary", summary, { summary = it.take(800) },
                        "Two or three sentences: who you are, what you are good at, what you are looking for",
                        lines = 4
                    )
                }

                FormSection("Contact") {
                    CvField("Phone", phone, { phone = it }, "e.g. 07XX XXX XXX")
                    CvField("Location", location, { location = it }, "e.g. Nairobi, Kenya")
                    CvField("LinkedIn, GitHub or portfolio link", link, { link = it }, "Optional")
                }

                FormSection("Education") {
                    CvField("Institution", institution, { institution = it }, "e.g. Strathmore University")
                    CvField("Graduation year", graduationYear, { graduationYear = it }, "e.g. 2027")
                    CvField("Grade or class", grade, { grade = it }, "Optional, e.g. Second Class Upper")
                }

                FormSection("Skills") {
                    CvField("Skills", skillsText, { skillsText = it }, "Separate with commas", lines = 2)
                }

                FormSection("Work experience and attachments") {
                    experiences.forEachIndexed { index, item ->
                        EntryHeader("Role ${index + 1}", canRemove = experiences.size > 1) {
                            experiences.removeAt(index)
                        }
                        CvField("Job title", item.title, { experiences[index] = item.copy(title = it) }, "e.g. Attachment student")
                        CvField("Organisation", item.organisation, { experiences[index] = item.copy(organisation = it) }, "Where you worked")
                        CvField("Period", item.period, { experiences[index] = item.copy(period = it) }, "e.g. May - Aug 2026")
                        CvField(
                            "What you did and achieved", item.achievements,
                            { experiences[index] = item.copy(achievements = it) },
                            "One achievement per line, with numbers where you can", lines = 3
                        )
                    }
                    TextButton(onClick = { if (experiences.size < 8) experiences.add(ExperienceDraft()) }) {
                        Text("+ Add another role")
                    }
                }

                FormSection("Projects") {
                    projects.forEachIndexed { index, item ->
                        EntryHeader("Project ${index + 1}", canRemove = projects.size > 1) {
                            projects.removeAt(index)
                        }
                        CvField("Project name", item.title, { projects[index] = item.copy(title = it) }, "e.g. Campus Events App")
                        CvField(
                            "What you built and the result", item.description,
                            { projects[index] = item.copy(description = it) },
                            "One or two sentences", lines = 2
                        )
                    }
                    TextButton(onClick = { if (projects.size < 8) projects.add(ProjectDraft()) }) {
                        Text("+ Add another project")
                    }
                }

                FormSection("Certifications") {
                    CvField("Certifications", certificationsText, { certificationsText = it }, "Separate with commas", lines = 2)
                }

                FormSection("Leadership and activities") {
                    CvField("Activities", activitiesText, { activitiesText = it }, "One per line: clubs, volunteering, awards", lines = 3)
                }

                FormSection("Referees") {
                    CvField(
                        "Referees", refereesText, { refereesText = it },
                        "One per line: name, title, organisation, contact. Leave empty for \"Available on request\"",
                        lines = 2
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
                if (current.checklist.isNotEmpty()) {
                    SectionCard {
                        Text("Before you send it", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(6.dp))
                        current.checklist.forEach { item ->
                            Text("•  $item", style = MaterialTheme.typography.bodyMedium)
                        }
                        Spacer(Modifier.height(8.dp))
                        TextButton(onClick = { result = null }) { Text("Go back and add these") }
                    }
                }

                SectionCard {
                    CvMarkdown(current.markdown)
                }

                PrimaryButton(
                    text = if (savingWord) "Saving…" else "Download as Word",
                    enabled = !savingWord,
                    onClick = {
                        saveMessage = null
                        saveWord.launch(current.roleTitle.replace("/", "-").ifBlank { "My" } + " CV.docx")
                    }
                )
                SecondaryButton(
                    text = "Download as PDF",
                    onClick = {
                        saveMessage = null
                        savePdf.launch(current.roleTitle.replace("/", "-").ifBlank { "My" } + " CV.pdf")
                    }
                )
                val saved = saveMessage
                if (saved != null) {
                    Text(saved, style = MaterialTheme.typography.bodyMedium, color = TextSecondary)
                }
                Text(
                    "Word is the safest format for online application systems. Use PDF when an employer asks for it.",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextMuted
                )

                if (current.skillsToBuild.isNotEmpty()) {
                    SectionCard {
                        Text("Skills this role often asks for that are not on your CV", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(6.dp))
                        Text(current.skillsToBuild.joinToString(", "), style = MaterialTheme.typography.bodyMedium)
                        Spacer(Modifier.height(4.dp))
                        Text(
                            "Only add a skill you can show evidence for.",
                            style = MaterialTheme.typography.bodySmall,
                            color = TextSecondary
                        )
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

                SecondaryButton(
                    text = "Copy CV text",
                    onClick = { clipboard.setText(AnnotatedString(current.markdown.replace("**", "").replace("#", "").trim())) }
                )
                SecondaryButton(
                    text = "Share CV text",
                    onClick = {
                        val send = Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_TEXT, current.markdown.replace("**", "").replace("#", "").trim())
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
private fun FormSection(title: String, content: @Composable ColumnScope.() -> Unit) {
    SectionCard {
        Text(title, style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(10.dp))
        content()
    }
}

@Composable
private fun EntryHeader(label: String, canRemove: Boolean, onRemove: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            label,
            style = MaterialTheme.typography.labelLarge,
            color = BluePrimary,
            modifier = Modifier.weight(1f)
        )
        if (canRemove) {
            TextButton(onClick = onRemove) { Text("Remove", color = DangerRed) }
        }
    }
    Spacer(Modifier.height(4.dp))
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

/** Shows the CV's simple Markdown (name, headings, bold entry lines, bullets) as formatted text. */
@Composable
private fun CvMarkdown(markdown: String) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        markdown.lines().forEach { raw ->
            val line = raw.replace("**", "")
            when {
                line.isBlank() -> Spacer(Modifier.height(4.dp))
                line.startsWith("## ") -> {
                    Text(
                        line.removePrefix("## ").uppercase(),
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = FontWeight.Bold
                    )
                    HorizontalDivider()
                }
                line.startsWith("# ") -> Text(line.removePrefix("# "), style = MaterialTheme.typography.headlineSmall)
                line.startsWith("- ") -> Text("•  " + line.removePrefix("- "), style = MaterialTheme.typography.bodyMedium)
                raw.trimStart().startsWith("**") -> Text(
                    line,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold
                )
                else -> Text(line, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
