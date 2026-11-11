package com.aicareercoach.mobile.data

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.aicareercoach.mobile.data.network.ApiClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.util.UUID

/** One line in the conversation. A note is a short message from the app itself, not from the coach. */
data class ChatLine(
    val text: String,
    val fromUser: Boolean,
    val sources: List<String> = emptyList(),
    val note: Boolean = false
)

data class ChatSessionSummary(
    val id: String,
    val title: String,
    val startedAt: String,
    val messageCount: Int
)

/**
 * The open conversation with the coach.
 *
 * It lives outside the chat screen so the conversation is still there after the student
 * visits another tab, and a reply that arrives while they are away is not lost. The
 * conversation keeps one id from its first message, which is how the backend knows what
 * was said before.
 */
object ChatMemory {
    val messages = mutableStateListOf<ChatLine>()
    var sessionId by mutableStateOf<String?>(null)
        private set
    var waiting by mutableStateOf(false)
        private set
    var loading by mutableStateOf(false)
        private set

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var owner = ""
    private var triedRestore = false
    private var pendingRequestId: String? = null

    /** Makes sure the conversation in memory belongs to this student. */
    fun useFor(email: String) {
        if (owner == email) return
        clear()
        owner = email
        triedRestore = false
    }

    /** Forgets the conversation on this phone when the student logs out. It stays saved on the server. */
    fun signOut() {
        clear()
        owner = ""
        triedRestore = false
    }

    private fun clear() {
        messages.clear()
        sessionId = null
        waiting = false
        loading = false
        pendingRequestId = null
    }

    /** Brings back the student's most recent conversation the first time the chat opens. */
    fun restoreLatest(token: String) {
        if (triedRestore || messages.isNotEmpty() || waiting) return
        triedRestore = true
        val student = owner
        loading = true
        scope.launch {
            val latest = ApiClient.getChatSessions(token)?.firstOrNull { it.messageCount > 0 }
            val lines = latest?.let { ApiClient.getChatMessages(token, it.id) }
            // Only fill the screen if the student has not started typing or logged out meanwhile.
            if (latest != null && !lines.isNullOrEmpty() && owner == student && messages.isEmpty() && !waiting) {
                sessionId = latest.id
                messages.addAll(lines)
            }
            loading = false
        }
    }

    /** Opens one of the student's earlier conversations so they can carry it on. */
    fun open(session: ChatSessionSummary, token: String) {
        if (waiting || loading) return
        val student = owner
        loading = true
        scope.launch {
            val lines = ApiClient.getChatMessages(token, session.id)
            if (lines != null && owner == student && !waiting) {
                messages.clear()
                messages.addAll(lines)
                sessionId = session.id
            }
            loading = false
        }
    }

    fun startNew() {
        if (waiting) return
        messages.clear()
        sessionId = null
    }

    fun send(text: String, token: String) {
        val trimmed = text.trim()
        if (trimmed.isEmpty()) return
        // Sending while the coach is still writing replaces that reply with the new instruction.
        if (waiting) stop(token, explain = false)
        val conversation = sessionId ?: UUID.randomUUID().toString().also { sessionId = it }
        val requestId = UUID.randomUUID().toString()
        messages.add(ChatLine(trimmed, fromUser = true))
        waiting = true
        pendingRequestId = requestId
        scope.launch {
            val reply = ApiClient.sendChatMessage(trimmed, token, conversation, requestId)
            if (pendingRequestId != requestId) return@launch   // stopped, or replaced by a newer message
            pendingRequestId = null
            waiting = false
            when {
                reply == null -> messages.add(
                    ChatLine(
                        "The coach could not be reached. Check that the backend is running, then send your message again.",
                        fromUser = false, note = true
                    )
                )
                reply.stopped || reply.response.isBlank() -> Unit
                else -> messages.add(ChatLine(reply.response, fromUser = false, sources = reply.sources))
            }
        }
    }

    /** Stops the reply being written. The question stays, so the next message can add to it. */
    fun stop(token: String, explain: Boolean = true) {
        val requestId = pendingRequestId ?: return
        pendingRequestId = null
        waiting = false
        if (explain) {
            messages.add(ChatLine("You stopped this reply. Add more detail or ask something else.", fromUser = false, note = true))
        }
        scope.launch { ApiClient.stopChatReply(token, requestId) }
    }
}
