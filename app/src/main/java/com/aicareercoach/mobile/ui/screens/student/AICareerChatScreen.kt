package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material.icons.filled.SmartToy
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.BlueLight
import com.aicareercoach.mobile.ui.theme.TextSecondary
import kotlinx.coroutines.launch

private data class ChatMessage(
    val text: String,
    val fromUser: Boolean,
    val sources: List<String> = emptyList()
)

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
    val suggestions = listOf("How do I improve my CV?", "Interview preparation", "Careers in AI")

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
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(BlueLight),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.SmartToy, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
            }
            Spacer(Modifier.width(10.dp))
            Column {
                Text("AI Career Coach", style = MaterialTheme.typography.titleMedium)
                Text("Answers cite your knowledge base", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
            }
        }
        HorizontalDivider()

        LazyRow(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(suggestions) { chip ->
                AssistChip(onClick = { send(chip) }, label = { Text(chip) })
            }
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
                ChatBubble(message)
            }
            if (typing) {
                item {
                    Text("Coach is typing…", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
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
                placeholder = { Text("Ask about careers, CVs, interviews...") },
                shape = RoundedCornerShape(24.dp),
                modifier = Modifier.weight(1f),
                singleLine = true
            )
            Spacer(Modifier.width(8.dp))
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(RoundedCornerShape(24.dp))
                    .background(MaterialTheme.colorScheme.primary)
                    .clickable(onClick = { send(input) }),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.ArrowUpward, contentDescription = "Send", tint = Color.White)
            }
        }
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
                .widthIn(max = 280.dp)
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
                "Sources: ${message.sources.joinToString(" · ")}",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
                modifier = Modifier.widthIn(max = 280.dp)
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
