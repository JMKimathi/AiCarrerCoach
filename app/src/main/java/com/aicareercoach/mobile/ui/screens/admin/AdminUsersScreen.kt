package com.aicareercoach.mobile.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.StudentAccount
import com.aicareercoach.mobile.ui.components.AppTextField
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.components.Tag
import com.aicareercoach.mobile.ui.theme.*

private enum class StudentFilter(val label: String) { All("All"), Active("Active"), Inactive("Deactivated") }

/**
 * The administrator's list of student accounts: search, filter, and the account actions
 * (deactivate or reactivate, set a temporary password, delete). Every action asks first.
 */
@Composable
fun AdminUsersScreen(
    students: List<StudentAccount> = emptyList(),
    message: String? = null,
    busy: Boolean = false,
    onRefresh: () -> Unit = {},
    onToggleActive: (StudentAccount) -> Unit = {},
    onResetPassword: (StudentAccount, String) -> Unit = { _, _ -> },
    onDelete: (StudentAccount) -> Unit = {}
) {
    var query by rememberSaveable { mutableStateOf("") }
    var filter by rememberSaveable { mutableStateOf(StudentFilter.All) }
    var confirmToggle by remember { mutableStateOf<StudentAccount?>(null) }
    var confirmDelete by remember { mutableStateOf<StudentAccount?>(null) }
    var passwordFor by remember { mutableStateOf<StudentAccount?>(null) }

    val activeCount = students.count { it.isActive }
    val shown = students.filter { student ->
        val matchesFilter = when (filter) {
            StudentFilter.All -> true
            StudentFilter.Active -> student.isActive
            StudentFilter.Inactive -> !student.isActive
        }
        val text = query.trim()
        matchesFilter && (text.isEmpty() ||
            student.name.contains(text, ignoreCase = true) ||
            student.email.contains(text, ignoreCase = true) ||
            student.course.contains(text, ignoreCase = true))
    }

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(
            title = "Students",
            subtitle = "$activeCount active, ${students.size - activeCount} deactivated",
            showProfile = false
        )

        Column(modifier = Modifier.padding(horizontal = 20.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(
                    value = query,
                    onValueChange = { query = it },
                    placeholder = { Text("Search by name, email or course") },
                    leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                    trailingIcon = if (query.isNotEmpty()) {
                        { IconButton(onClick = { query = "" }) { Icon(Icons.Default.Close, contentDescription = "Clear search") } }
                    } else null,
                    singleLine = true,
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.weight(1f)
                )
                Spacer(Modifier.width(4.dp))
                IconButton(onClick = onRefresh, enabled = !busy) {
                    Icon(Icons.Default.Refresh, contentDescription = "Refresh the list", tint = BluePrimary)
                }
            }
            Spacer(Modifier.height(10.dp))
            Row(
                modifier = Modifier.horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                StudentFilter.values().forEach { option ->
                    val count = when (option) {
                        StudentFilter.All -> students.size
                        StudentFilter.Active -> activeCount
                        StudentFilter.Inactive -> students.size - activeCount
                    }
                    FilterPill("${option.label} ($count)", selected = filter == option) { filter = option }
                }
            }
            if (busy) {
                Spacer(Modifier.height(10.dp))
                LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
            }
            if (message != null) {
                Spacer(Modifier.height(10.dp))
                Text(message, style = MaterialTheme.typography.bodyMedium, color = TextSecondary)
            }
            Spacer(Modifier.height(10.dp))
        }

        LazyColumn(
            modifier = Modifier.padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(bottom = 24.dp)
        ) {
            if (shown.isEmpty()) item {
                Text(
                    if (students.isEmpty()) "No student accounts were returned. Check the connection, then tap refresh."
                    else "No student matches this search.",
                    color = TextSecondary
                )
            }
            items(shown, key = { it.userId.ifBlank { it.email } }) { student ->
                StudentCard(
                    student = student,
                    enabled = !busy,
                    onToggle = { confirmToggle = student },
                    onPassword = { passwordFor = student },
                    onDelete = { confirmDelete = student }
                )
            }
        }
    }

    confirmToggle?.let { student ->
        AlertDialog(
            onDismissRequest = { confirmToggle = null },
            title = { Text(if (student.isActive) "Deactivate this account?" else "Reactivate this account?") },
            text = {
                Text(
                    if (student.isActive)
                        "${student.name} will be signed out and will not be able to sign in until you reactivate the account. Nothing is deleted."
                    else "${student.name} will be able to sign in again with their existing password."
                )
            },
            confirmButton = {
                TextButton(onClick = { confirmToggle = null; onToggleActive(student) }) {
                    Text(if (student.isActive) "Deactivate" else "Reactivate")
                }
            },
            dismissButton = { TextButton(onClick = { confirmToggle = null }) { Text("Cancel") } }
        )
    }

    confirmDelete?.let { student ->
        AlertDialog(
            onDismissRequest = { confirmDelete = null },
            title = { Text("Delete this account?") },
            text = {
                Text(
                    "This permanently removes ${student.name} and their chats, feedback, assessments and practice interviews. " +
                        "It cannot be undone. To block sign-in without losing anything, deactivate the account instead."
                )
            },
            confirmButton = {
                TextButton(onClick = { confirmDelete = null; onDelete(student) }) {
                    Text("Delete", color = DangerRed)
                }
            },
            dismissButton = { TextButton(onClick = { confirmDelete = null }) { Text("Cancel") } }
        )
    }

    passwordFor?.let { student ->
        var newPassword by remember(student.userId) { mutableStateOf("") }
        AlertDialog(
            onDismissRequest = { passwordFor = null },
            title = { Text("Set a temporary password") },
            text = {
                Column {
                    Text("Give ${student.name} this password and ask them to keep it private. It replaces their current one.")
                    Spacer(Modifier.height(12.dp))
                    AppTextField(
                        label = "New password",
                        value = newPassword,
                        onValueChange = { newPassword = it },
                        isPassword = true,
                        placeholder = "At least 8 characters"
                    )
                }
            },
            confirmButton = {
                TextButton(
                    enabled = newPassword.length >= 8,
                    onClick = { passwordFor = null; onResetPassword(student, newPassword) }
                ) { Text("Set password") }
            },
            dismissButton = { TextButton(onClick = { passwordFor = null }) { Text("Cancel") } }
        )
    }
}

@Composable
private fun StudentCard(
    student: StudentAccount,
    enabled: Boolean,
    onToggle: () -> Unit,
    onPassword: () -> Unit,
    onDelete: () -> Unit
) {
    var menuOpen by remember { mutableStateOf(false) }
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .clip(CircleShape)
                    .background(if (student.isActive) BlueLight else SurfaceAlt),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    student.initials,
                    style = MaterialTheme.typography.titleMedium,
                    color = if (student.isActive) BluePrimary else TextMuted,
                    fontWeight = FontWeight.SemiBold
                )
            }
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(student.name, style = MaterialTheme.typography.titleMedium)
                Text(student.email, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
            }
            Tag(if (student.isActive) "Active" else "Deactivated", if (student.isActive) SuccessGreen else WarningAmber)
            if (student.userId.isNotBlank()) {
                Box {
                    IconButton(onClick = { menuOpen = true }, enabled = enabled) {
                        Icon(Icons.Default.MoreVert, contentDescription = "Account actions for ${student.name}")
                    }
                    DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
                        DropdownMenuItem(
                            text = { Text(if (student.isActive) "Deactivate account" else "Reactivate account") },
                            onClick = { menuOpen = false; onToggle() }
                        )
                        DropdownMenuItem(
                            text = { Text("Set temporary password") },
                            onClick = { menuOpen = false; onPassword() }
                        )
                        DropdownMenuItem(
                            text = { Text("Delete account", color = DangerRed) },
                            onClick = { menuOpen = false; onDelete() }
                        )
                    }
                }
            }
        }
        if (student.course.isNotBlank()) {
            Spacer(Modifier.height(8.dp))
            Text(student.course, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
        }
        Spacer(Modifier.height(10.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            MiniStat("Chats", student.chatCount, Modifier.weight(1f))
            MiniStat("Interviews", student.interviewCount, Modifier.weight(1f))
            MiniStat("Assessments", student.assessmentCount, Modifier.weight(1f))
        }
        val joined = shortDate(student.joined)
        val active = daysAgo(student.lastActive)
        val footer = listOfNotNull(
            if (joined.isNotEmpty()) "Joined $joined" else null,
            if (active.isNotEmpty()) "Last active $active" else "No activity yet"
        ).joinToString("  •  ")
        Spacer(Modifier.height(8.dp))
        Text(footer, style = MaterialTheme.typography.bodySmall, color = TextMuted)
    }
}

@Composable
private fun MiniStat(label: String, value: Int, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(10.dp))
            .background(SurfaceAlt)
            .padding(vertical = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(value.toString(), style = MaterialTheme.typography.titleMedium)
        Text(label, style = MaterialTheme.typography.labelSmall, color = TextSecondary)
    }
}

@Composable
private fun FilterPill(label: String, selected: Boolean, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(if (selected) BluePrimary else Color.White)
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 8.dp)
    ) {
        Text(
            label,
            style = MaterialTheme.typography.labelLarge,
            color = if (selected) Color.White else TextSecondary
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun AdminUsersScreenPreview() {
    AICareerCoachTheme {
        AdminUsersScreen(
            students = listOf(
                StudentAccount("Amina Otieno", "amina@example.com", "BSc Informatics", "Active", "1", "2026-10-02T08:00:00", 12, 3, 1, "2026-11-09T10:00:00"),
                StudentAccount("Brian Kiptoo", "brian@example.com", "BCom Finance", "Inactive", "2", "2026-09-14T08:00:00")
            )
        )
    }
}
