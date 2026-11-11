package com.aicareercoach.mobile.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.AdminOverview
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.*

private data class AdminStat(
    val label: String,
    val value: String,
    val icon: ImageVector,
    val color: Color,
    val onClick: () -> Unit
)

/** The administrator's home: this week at a glance, what needs attention, and shortcuts. */
@Composable
fun AdminDashboardScreen(
    adminName: String = "",
    overview: AdminOverview? = null,
    onOpenResources: () -> Unit = {},
    onOpenUsers: () -> Unit = {},
    onOpenAnalytics: () -> Unit = {},
    onUploadResource: () -> Unit = {},
    onRefresh: () -> Unit = {},
    onLogOut: () -> Unit = {}
) {
    var confirmLogOut by remember { mutableStateOf(false) }
    fun shown(value: Int?): String = value?.toString() ?: "—"

    val stats = listOf(
        AdminStat("Active students", shown(overview?.activeStudents), Icons.Default.Group, BluePrimary, onOpenUsers),
        AdminStat("Chats this week", shown(overview?.chatsThisWeek), Icons.Default.Chat, WarningAmber, onOpenAnalytics),
        AdminStat("Interviews this week", shown(overview?.interviewsThisWeek), Icons.Default.RecordVoiceOver, SuccessGreen, onOpenAnalytics),
        AdminStat("Knowledge resources", shown(overview?.careerResources), Icons.Default.MenuBook, BluePrimaryDark, onOpenResources),
    )

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(title = "Admin", subtitle = "Accounts, knowledge base and usage", showProfile = false)

        LazyColumn(
            modifier = Modifier.padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
            contentPadding = PaddingValues(bottom = 24.dp)
        ) {
            item {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(20.dp))
                        .background(Brush.linearGradient(listOf(BluePrimary, BluePrimaryDark)))
                        .padding(20.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                if (adminName.isBlank()) "Welcome back" else "Welcome back, $adminName",
                                style = MaterialTheme.typography.titleLarge,
                                color = Color.White
                            )
                            Spacer(Modifier.height(4.dp))
                            Text(
                                when {
                                    overview == null -> "Could not load the latest figures. Tap refresh to try again."
                                    overview.newStudentsThisWeek == 1 -> "1 new student joined this week."
                                    else -> "${overview.newStudentsThisWeek} new students joined this week."
                                },
                                style = MaterialTheme.typography.bodyMedium,
                                color = Color.White.copy(alpha = 0.9f)
                            )
                        }
                        IconButton(onClick = onRefresh) {
                            Icon(Icons.Default.Refresh, contentDescription = "Refresh figures", tint = Color.White)
                        }
                    }
                    Spacer(Modifier.height(16.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        HeroFigure("Students", shown(overview?.totalStudents), Modifier.weight(1f))
                        HeroFigure("Assessments", shown(overview?.assessmentsTotal), Modifier.weight(1f))
                        HeroFigure(
                            "Avg rating",
                            overview?.averageRating?.let { String.format("%.1f", it) } ?: "—",
                            Modifier.weight(1f)
                        )
                    }
                }
            }

            item {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    StatCard(stats[0], Modifier.weight(1f))
                    StatCard(stats[1], Modifier.weight(1f))
                }
                Spacer(Modifier.height(10.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    StatCard(stats[2], Modifier.weight(1f))
                    StatCard(stats[3], Modifier.weight(1f))
                }
            }

            val flagged = overview?.flaggedResponses ?: 0
            val inactive = overview?.inactiveStudents ?: 0
            if (flagged > 0 || inactive > 0) item {
                Text("Needs your attention", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(10.dp))
                SectionCard {
                    if (flagged > 0) {
                        AttentionRow(
                            Icons.Default.Flag, DangerRed,
                            if (flagged == 1) "1 answer was marked inaccurate" else "$flagged answers were marked inaccurate",
                            "Read the comments and correct the knowledge base",
                            onOpenAnalytics
                        )
                    }
                    if (flagged > 0 && inactive > 0) HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                    if (inactive > 0) {
                        AttentionRow(
                            Icons.Default.PersonOff, WarningAmber,
                            if (inactive == 1) "1 account is deactivated" else "$inactive accounts are deactivated",
                            "Reactivate or remove them from the Students tab",
                            onOpenUsers
                        )
                    }
                }
            }

            item {
                Text("Quick actions", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(10.dp))
                SectionCard {
                    AdminManageRow(Icons.Default.LibraryAdd, "Add a career resource", "Write or paste new guidance for the coach", onUploadResource)
                    HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                    AdminManageRow(Icons.Default.MenuBook, "Edit the knowledge base", "Update or remove existing resources", onOpenResources)
                    HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                    AdminManageRow(Icons.Default.ManageAccounts, "Manage student accounts", "Search, deactivate, reset passwords", onOpenUsers)
                    HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                    AdminManageRow(Icons.Default.Insights, "See usage and feedback", "Daily activity and what students said", onOpenAnalytics)
                }
            }

            item {
                Text("Most used resources", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(10.dp))
                SectionCard {
                    val names = overview?.topResources.orEmpty()
                    if (names.isEmpty()) {
                        Text("No answers have cited a resource yet.", color = TextSecondary)
                    } else names.forEachIndexed { index, name ->
                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(vertical = 5.dp)) {
                            Box(
                                modifier = Modifier.size(26.dp).clip(CircleShape).background(BlueLight),
                                contentAlignment = Alignment.Center
                            ) {
                                Text("${index + 1}", style = MaterialTheme.typography.labelMedium, color = BluePrimary)
                            }
                            Spacer(Modifier.width(12.dp))
                            Text(name, style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            }

            item {
                OutlinedButton(
                    onClick = { confirmLogOut = true },
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = DangerRed)
                ) {
                    Icon(Icons.Default.Logout, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Log out")
                }
            }
        }
    }

    if (confirmLogOut) {
        AlertDialog(
            onDismissRequest = { confirmLogOut = false },
            title = { Text("Log out?") },
            text = { Text("You will need your email and password to sign in again.") },
            confirmButton = { TextButton(onClick = { confirmLogOut = false; onLogOut() }) { Text("Log out") } },
            dismissButton = { TextButton(onClick = { confirmLogOut = false }) { Text("Stay") } }
        )
    }
}

@Composable
private fun HeroFigure(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(Color.White.copy(alpha = 0.16f))
            .padding(vertical = 10.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(value, style = MaterialTheme.typography.titleLarge, color = Color.White)
        Text(label, style = MaterialTheme.typography.labelMedium, color = Color.White.copy(alpha = 0.9f))
    }
}

@Composable
private fun StatCard(stat: AdminStat, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .clickable(onClick = stat.onClick)
            .padding(14.dp)
    ) {
        Box(
            modifier = Modifier.size(36.dp).clip(RoundedCornerShape(10.dp)).background(stat.color.copy(alpha = 0.12f)),
            contentAlignment = Alignment.Center
        ) {
            Icon(stat.icon, contentDescription = null, tint = stat.color, modifier = Modifier.size(20.dp))
        }
        Spacer(Modifier.height(10.dp))
        Text(stat.value, style = MaterialTheme.typography.headlineMedium)
        Text(stat.label, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
    }
}

@Composable
private fun AttentionRow(icon: ImageVector, color: Color, title: String, hint: String, onClick: () -> Unit) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick)
    ) {
        Icon(icon, contentDescription = null, tint = color)
        Spacer(Modifier.width(14.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyLarge)
            Text(hint, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
        }
        Icon(Icons.Default.ChevronRight, contentDescription = null, tint = TextMuted)
    }
}

@Composable
private fun AdminManageRow(icon: ImageVector, label: String, hint: String, onClick: () -> Unit) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Icon(icon, contentDescription = null, tint = BluePrimary)
        Spacer(Modifier.width(14.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(label, style = MaterialTheme.typography.bodyLarge)
            Text(hint, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
        }
        Icon(Icons.Default.ChevronRight, contentDescription = null, tint = TextMuted)
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 800)
@Composable
private fun AdminDashboardScreenPreview() {
    AICareerCoachTheme {
        AdminDashboardScreen(
            adminName = "John",
            overview = AdminOverview(
                18, 42, 57, 2, listOf("CV writing guide", "Internship applications"),
                totalStudents = 20, inactiveStudents = 2, newStudentsThisWeek = 4,
                interviewsThisWeek = 9, assessmentsTotal = 31, averageRating = 4.3
            )
        )
    }
}
