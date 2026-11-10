package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Explore
import androidx.compose.material.icons.filled.Forum
import androidx.compose.material.icons.filled.RecordVoiceOver
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.BlueLight
import com.aicareercoach.mobile.ui.theme.BluePrimary
import com.aicareercoach.mobile.ui.theme.SuccessGreen
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextMuted
import com.aicareercoach.mobile.ui.theme.TextSecondary
import com.aicareercoach.mobile.ui.theme.WarningAmber
import kotlinx.coroutines.launch

private data class ChatMessage(
    val text: String,
    val fromUser: Boolean,
    val sources: List<String> = emptyList()
)

private data class ChatStarter(
    val icon: ImageVector,
    val accent: Color,
    val title: String,
    val prompt: String
)

private val ChatViolet = Color(0xFF7C3AED)
private val followUpPrompts = listOf("Tell me more", "Give me an example", "What should I do first?")

@Composable
fun AICareerChatScreen(
    session: UserSession = UserSession("John Mwiti", "john.mwiti@strathmore.edu"),
    seedQuestion: String? = null,
    onSeedConsumed: () -> Unit = {}
) {
    val messages = remember {
        mutableStateListOf<ChatMessage>()
    }
    var input by remember { mutableStateOf("") }
    var typing by remember { mutableStateOf(false) }
    var currentSessionId by remember { mutableStateOf<String?>(null) }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()

    // Starting points shaped by what the student has told us about themselves.
    val starters = listOf(
        ChatStarter(
            Icons.Default.Explore, BluePrimary, "Find a direction",
            if (session.course.isBlank()) "Which careers could suit me? Ask me a few questions first."
            else "Which careers could suit someone studying ${session.course}?"
        ),
        ChatStarter(
            Icons.Default.Description, SuccessGreen, "Sharpen my CV",
            if (session.careerGoal.isBlank()) "What should a strong student CV include?"
            else "What should my CV show for this goal: ${session.careerGoal}?"
        ),
        ChatStarter(
            Icons.Default.RecordVoiceOver, WarningAmber, "Interview practice",
            "Ask me one interview question, then tell me how to improve my answer."
        ),
        ChatStarter(
            Icons.Default.TrendingUp, ChatViolet, "Plan my next step",
            "What should I do this semester to be ready for an internship?"
        ),
    )

    fun send(text: String) {
        val trimmed = text.trim()
        if (trimmed.isEmpty() || typing) return
        messages.add(ChatMessage(trimmed, fromUser = true))
        input = ""
        typing = true
        scope.launch {
            val netResp = ApiClient.sendChatMessage(trimmed, token = session.token, sessionId = currentSessionId)
            if (netResp != null && netResp.response.isNotBlank()) {
                currentSessionId = netResp.sessionId
                messages.add(
                    ChatMessage(
                        text = netResp.response,
                        fromUser = false,
                        sources = netResp.sources
                    )
                )
            } else {
                messages.add(ChatMessage("The coach could not reach the backend. Check that the API is running, then try again.", fromUser = false))
            }
            typing = false
            listState.animateScrollToItem(messages.lastIndex)
        }
    }

    fun startNewChat() {
        if (typing) return
        messages.clear()
        currentSessionId = null
        input = ""
    }

    LaunchedEffect(seedQuestion) {
        val question = seedQuestion
        if (!question.isNullOrBlank()) {
            send(question)
            onSeedConsumed()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
            .imePadding()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(BlueLight),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.Forum, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
            }
            Spacer(Modifier.width(10.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text("Career Coach", style = MaterialTheme.typography.titleMedium)
                Text("Ask about careers, CVs and interviews", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
            }
            if (messages.isNotEmpty()) {
                TextButton(onClick = { startNewChat() }, enabled = !typing) {
                    Text("New chat")
                }
            }
        }
        HorizontalDivider()

        if (messages.isEmpty() && !typing) {
            Column(
                modifier = Modifier
                    .weight(1f)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp, vertical = 24.dp)
            ) {
                Text("Hi ${session.firstName}.", style = MaterialTheme.typography.headlineMedium)
                Spacer(Modifier.height(4.dp))
                Text(
                    "What would you like to figure out today?",
                    style = MaterialTheme.typography.bodyLarge,
                    color = TextSecondary
                )
                Spacer(Modifier.height(20.dp))
                starters.chunked(2).forEach { pair ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(IntrinsicSize.Min),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        pair.forEach { starter ->
                            StarterCard(starter, Modifier.weight(1f).fillMaxHeight()) { send(starter.prompt) }
                        }
                    }
                    Spacer(Modifier.height(12.dp))
                }
                Spacer(Modifier.height(4.dp))
                Text(
                    "Tap a card to start, or type your own question below.",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextMuted
                )
            }
        } else {
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(vertical = 12.dp)
            ) {
                items(messages) { message ->
                    ChatBubble(message)
                }
                if (typing) {
                    item {
                        Text("Coach is thinking…", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                    }
                }
                // Quick replies under the coach's latest answer keep the conversation moving.
                if (!typing && messages.lastOrNull()?.fromUser == false) {
                    item {
                        Row(
                            modifier = Modifier.horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            followUpPrompts.forEach { prompt ->
                                FollowUpChip(prompt) { send(prompt) }
                            }
                        }
                    }
                }
            }
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = input,
                onValueChange = { input = it },
                placeholder = { Text("Ask anything about your career") },
                shape = RoundedCornerShape(24.dp),
                modifier = Modifier.weight(1f),
                maxLines = 4
            )
            Spacer(Modifier.width(8.dp))
            val canSend = input.isNotBlank() && !typing
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(RoundedCornerShape(24.dp))
                    .background(MaterialTheme.colorScheme.primary.copy(alpha = if (canSend) 1f else 0.4f))
                    .clickable(enabled = canSend, onClick = { send(input) }),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.ArrowUpward, contentDescription = "Send", tint = Color.White)
            }
        }
    }
}

@Composable
private fun StarterCard(starter: ChatStarter, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(SurfaceAlt)
            .clickable(onClick = onClick)
            .padding(14.dp)
    ) {
        Box(
            modifier = Modifier
                .size(36.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(starter.accent.copy(alpha = 0.14f)),
            contentAlignment = Alignment.Center
        ) {
            Icon(starter.icon, contentDescription = null, tint = starter.accent, modifier = Modifier.size(20.dp))
        }
        Spacer(Modifier.height(10.dp))
        Text(starter.title, style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(4.dp))
        Text(
            starter.prompt,
            style = MaterialTheme.typography.bodySmall,
            color = TextSecondary,
            maxLines = 4,
            overflow = TextOverflow.Ellipsis
        )
    }
}

@Composable
private fun FollowUpChip(label: String, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .border(1.dp, BluePrimary.copy(alpha = 0.4f), RoundedCornerShape(20.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 8.dp)
    ) {
        Text(label, style = MaterialTheme.typography.labelLarge, color = BluePrimary)
    }
}

@Composable
private fun ChatBubble(message: ChatMessage) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = if (message.fromUser) Alignment.End else Alignment.Start
    ) {
        Box(
            modifier = Modifier
                .widthIn(max = 300.dp)
                .clip(
                    RoundedCornerShape(
                        topStart = 16.dp, topEnd = 16.dp,
                        bottomStart = if (message.fromUser) 16.dp else 4.dp,
                        bottomEnd = if (message.fromUser) 4.dp else 16.dp
                    )
                )
                .background(if (message.fromUser) MaterialTheme.colorScheme.primary else BlueLight)
                .padding(12.dp)
        ) {
            Text(
                message.text,
                color = if (message.fromUser) Color.White else Color(0xFF111827),
                style = MaterialTheme.typography.bodyMedium
            )
        }
        if (!message.fromUser && message.sources.isNotEmpty()) {
            Spacer(Modifier.height(6.dp))
            Text(
                "Based on: ${message.sources.joinToString(" · ")}",
                style = MaterialTheme.typography.bodySmall,
                color = TextMuted,
                modifier = Modifier.widthIn(max = 300.dp)
            )
        }
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
private fun AICareerChatScreenPreview() {
    AICareerCoachTheme {
        AICareerChatScreen()
    }
}
