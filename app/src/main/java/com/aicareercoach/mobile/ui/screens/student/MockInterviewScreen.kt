package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.InterviewState
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.components.SecondaryButton
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.*
import kotlinx.coroutines.launch

private data class InterviewMessage(val text: String, val fromCandidate: Boolean)

private val interviewOpportunityChoices = listOf(
    "" to "Any",
    "industrial attachment" to "Attachment",
    "internship" to "Internship",
    "graduate programme" to "Graduate programme",
    "full-time job" to "Full-time job"
)
private val interviewLengthChoices = listOf(4, 6, 8)
private const val CONNECTION_ERROR = "The interviewer could not be reached. Check that the backend is running and try again."

/** A practice interview for one career: the interviewer asks, the student answers, feedback comes at the end. */
@Composable
fun MockInterviewScreen(
    session: UserSession,
    careerId: String,
    onBack: () -> Unit = {}
) {
    var roleTitle by remember { mutableStateOf("") }
    var questionCount by rememberSaveable { mutableStateOf(6) }
    var opportunity by rememberSaveable { mutableStateOf("") }
    var interviewId by remember { mutableStateOf<String?>(null) }
    var status by remember { mutableStateOf("") }
    var progress by remember { mutableStateOf("") }
    val messages = remember { mutableStateListOf<InterviewMessage>() }
    var input by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var feedback by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()

    LaunchedEffect(session.token, careerId) {
        ApiClient.getCareerDetail(session.token, careerId)?.let { roleTitle = it.roleTitle }
    }

    // Keep the newest message, or the feedback once it arrives, in view.
    LaunchedEffect(messages.size, busy, feedback) {
        val extra = (if (busy) 1 else 0) + (if (feedback.isNotBlank()) 1 else 0)
        val last = messages.size + extra - 1
        if (last >= 0) listState.animateScrollToItem(last)
    }

    fun applyState(state: InterviewState) {
        interviewId = state.interviewId
        status = state.status
        progress = "Question ${state.questionNumber} of ${state.totalQuestions}"
        if (state.roleTitle.isNotBlank()) roleTitle = state.roleTitle
        if (state.interviewerMessage.isNotBlank()) {
            messages.add(InterviewMessage(state.interviewerMessage, fromCandidate = false))
        }
        if (state.feedback.isNotBlank()) feedback = state.feedback
    }

    fun start() {
        if (busy) return
        busy = true
        error = null
        scope.launch {
            val state = ApiClient.startInterview(session.token, careerId, opportunity, questionCount)
            if (state == null) error = CONNECTION_ERROR else applyState(state)
            busy = false
        }
    }

    fun sendAnswer() {
        val id = interviewId ?: return
        val answer = input.trim()
        if (answer.isEmpty() || busy || status != "in_progress") return
        messages.add(InterviewMessage(answer, fromCandidate = true))
        input = ""
        busy = true
        error = null
        scope.launch {
            val state = ApiClient.answerInterview(session.token, id, answer)
            if (state == null) error = CONNECTION_ERROR else applyState(state)
            busy = false
        }
    }

    fun finish() {
        val id = interviewId ?: return
        if (busy) return
        busy = true
        error = null
        scope.launch {
            val state = ApiClient.finishInterview(session.token, id)
            if (state == null) error = CONNECTION_ERROR else applyState(state)
            busy = false
        }
    }

    fun reset() {
        interviewId = null
        status = ""
        progress = ""
        feedback = ""
        error = null
        input = ""
        messages.clear()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
            .imePadding()
    ) {
        AppTopBar(
            title = "Mock Interview",
            subtitle = if (roleTitle.isBlank()) null else roleTitle,
            onBack = onBack,
            showProfile = false
        )
        HorizontalDivider()

        if (interviewId == null) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 20.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    "The interviewer asks one question at a time and may follow up on what you say. " +
                        "This is practice: it does not represent any employer, and the feedback at the end is " +
                        "coaching, not a hiring decision.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary
                )
                SectionCard {
                    Text("Interviewing for", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        interviewOpportunityChoices.forEach { (value, label) ->
                            InterviewChoiceChip(label, selected = opportunity == value) { opportunity = value }
                        }
                    }
                    Spacer(Modifier.height(14.dp))
                    Text("Number of questions", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        interviewLengthChoices.forEach { count ->
                            InterviewChoiceChip("$count", selected = questionCount == count) { questionCount = count }
                        }
                    }
                }
                val message = error
                if (message != null) {
                    Text(message, style = MaterialTheme.typography.bodyMedium, color = DangerRed)
                }
                PrimaryButton(
                    text = if (busy) "Starting…" else "Start interview",
                    enabled = !busy,
                    onClick = { start() }
                )
            }
        } else {
            if (progress.isNotBlank()) {
                Text(
                    if (status == "in_progress") progress else "Interview finished",
                    modifier = Modifier.padding(horizontal = 20.dp, vertical = 8.dp),
                    style = MaterialTheme.typography.labelLarge,
                    color = TextSecondary
                )
            }

            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(vertical = 8.dp)
            ) {
                items(messages) { message ->
                    InterviewBubble(message)
                }
                if (busy) {
                    item {
                        Text(
                            "Interviewer is thinking…",
                            style = MaterialTheme.typography.bodySmall,
                            color = TextSecondary
                        )
                    }
                }
                if (feedback.isNotBlank()) {
                    item {
                        SectionCard {
                            Text("Your feedback", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            Text(feedback, style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            }

            val message = error
            if (message != null) {
                Text(
                    message,
                    modifier = Modifier.padding(horizontal = 20.dp),
                    style = MaterialTheme.typography.bodySmall,
                    color = DangerRed
                )
            }

            Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp)) {
                when {
                    status == "in_progress" -> {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            OutlinedTextField(
                                value = input,
                                onValueChange = { input = it.take(4000) },
                                placeholder = { Text("Type your answer") },
                                shape = RoundedCornerShape(24.dp),
                                modifier = Modifier.weight(1f),
                                maxLines = 4
                            )
                            Spacer(Modifier.width(8.dp))
                            Box(
                                modifier = Modifier
                                    .size(48.dp)
                                    .clip(RoundedCornerShape(24.dp))
                                    .background(MaterialTheme.colorScheme.primary)
                                    .clickable(onClick = { sendAnswer() }),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(Icons.Default.ArrowUpward, contentDescription = "Send answer", tint = Color.White)
                            }
                        }
                        TextButton(
                            onClick = { finish() },
                            enabled = !busy,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("End interview and get feedback")
                        }
                    }
                    feedback.isBlank() -> PrimaryButton(
                        text = if (busy) "Preparing feedback…" else "Get feedback",
                        enabled = !busy,
                        onClick = { finish() }
                    )
                    else -> SecondaryButton(text = "Start a new interview", onClick = { reset() })
                }
            }
        }
    }
}

@Composable
private fun InterviewBubble(message: InterviewMessage) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = if (message.fromCandidate) Alignment.End else Alignment.Start
    ) {
        Box(
            modifier = Modifier
                .widthIn(max = 300.dp)
                .clip(
                    RoundedCornerShape(
                        topStart = 16.dp, topEnd = 16.dp,
                        bottomStart = if (message.fromCandidate) 16.dp else 4.dp,
                        bottomEnd = if (message.fromCandidate) 4.dp else 16.dp
                    )
                )
                .background(if (message.fromCandidate) MaterialTheme.colorScheme.primary else BlueLight)
                .padding(12.dp)
        ) {
            Text(
                message.text,
                color = if (message.fromCandidate) Color.White else TextPrimary,
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Composable
private fun InterviewChoiceChip(label: String, selected: Boolean, onClick: () -> Unit) {
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
