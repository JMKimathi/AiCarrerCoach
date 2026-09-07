package com.aicareercoach.mobile.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
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
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.BlueLight
import com.aicareercoach.mobile.ui.theme.TextSecondary
import kotlinx.coroutines.launch

private data class ChatMessage(val text: String, val fromUser: Boolean)

@Composable
fun AICareerChatScreen() {
    val messages = remember {
        mutableStateListOf(
            ChatMessage("Hi! I'm your AI Career Coach. Ask me anything about careers, CVs, or interviews.", fromUser = false),
            ChatMessage("What roles suit a computer science graduate interested in AI?", fromUser = true),
            ChatMessage(
                "Based on your profile and current market resources, strong options include Machine Learning Engineer, " +
                    "AI Product Analyst, and Data Scientist. These typically require Python, familiarity with ML " +
                    "frameworks, and a portfolio of applied projects.",
                fromUser = false
            ),
        )
    }
    var input by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()

    fun send() {
        val text = input.trim()
        if (text.isEmpty()) return
        messages.add(ChatMessage(text, fromUser = true))
        input = ""
        messages.add(
            ChatMessage(
                "That's a great question. I'll ground this in the career knowledge base and share a practical next step once the backend is connected.",
                fromUser = false
            )
        )
        scope.launch {
            listState.animateScrollToItem(messages.lastIndex)
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
                Text("Grounded in your career knowledge base", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
            }
        }
        HorizontalDivider()

        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(vertical = 16.dp)
        ) {
            items(messages) { message ->
                ChatBubble(message)
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
                    .clickable(onClick = { send() }),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.ArrowUpward, contentDescription = "Send", tint = Color.White)
            }
        }
    }
}

@Composable
private fun ChatBubble(message: ChatMessage) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (message.fromUser) Arrangement.End else Arrangement.Start
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
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
private fun AICareerChatScreenPreview() {
    AICareerCoachTheme {
        AICareerChatScreen()
    }
}
