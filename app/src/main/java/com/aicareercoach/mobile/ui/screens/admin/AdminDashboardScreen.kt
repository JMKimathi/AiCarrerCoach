package com.aicareercoach.mobile.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.*
import com.aicareercoach.mobile.data.AdminOverview

private data class AdminStat(val label: String, val value: String, val icon: ImageVector, val color: Color)
@Composable
fun AdminDashboardScreen(
    overview: AdminOverview? = null,
    onOpenResources: () -> Unit = {},
    onOpenUsers: () -> Unit = {},
    onOpenAnalytics: () -> Unit = {},
    onUploadResource: () -> Unit = {},
    onLogOut: () -> Unit = {}
) {
    val stats = listOf(
        AdminStat("Active Students", overview?.activeStudents?.toString() ?: "—", Icons.Default.Group, BluePrimary),
        AdminStat("Career Resources", overview?.careerResources?.toString() ?: "—", Icons.Default.Description, SuccessGreen),
        AdminStat("Chats This Week", overview?.chatsThisWeek?.toString() ?: "—", Icons.Default.Chat, WarningAmber),
        AdminStat("Inaccurate Feedback", overview?.flaggedResponses?.toString() ?: "—", Icons.Default.Feedback, DangerRed),
    )

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(title = "Admin overview", subtitle = "Accounts, feedback, and resources", showProfile = false)

        LazyColumn(
            modifier = Modifier.padding(horizontal = 20.dp),
            contentPadding = PaddingValues(bottom = 24.dp)
        ) {
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    StatCard(stats[0], Modifier.weight(1f), onOpenUsers)
                    StatCard(stats[1], Modifier.weight(1f), onOpenResources)
                }
                Spacer(Modifier.height(10.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    StatCard(stats[2], Modifier.weight(1f), onOpenAnalytics)
                    StatCard(stats[3], Modifier.weight(1f), onOpenAnalytics)
                }

                Spacer(Modifier.height(20.dp))
            }
            item {
                Text("Most referenced resources", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(10.dp))
                SectionCard {
                    val names = overview?.topResources.orEmpty()
                    if (names.isEmpty()) Text("No resource usage recorded yet.", color = TextSecondary)
                    else names.forEach { Text(it, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(vertical = 4.dp)) }
                }
                Spacer(Modifier.height(20.dp))
                Spacer(Modifier.height(10.dp))
                Text("Manage", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(10.dp))
                SectionCard {
                    AdminManageRow(Icons.Default.LibraryAdd, "Upload career resource", onUploadResource)
                    HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                    AdminManageRow(Icons.Default.MenuBook, "Browse knowledge base", onOpenResources)
                    HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                    AdminManageRow(Icons.Default.ManageAccounts, "Manage student accounts", onOpenUsers)
                    HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                    AdminManageRow(Icons.Default.Insights, "View usage analytics", onOpenAnalytics)
                }

                Spacer(Modifier.height(20.dp))
                OutlinedButton(
                    onClick = onLogOut,
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = DangerRed)
                ) {
                    Icon(Icons.Default.Logout, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Log Out")
                }
            }
        }
    }
}

@Composable
private fun StatCard(stat: AdminStat, modifier: Modifier = Modifier, onClick: () -> Unit = {}) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .clickable(onClick = onClick)
            .padding(14.dp)
    ) {
        Icon(stat.icon, contentDescription = null, tint = stat.color)
        Spacer(Modifier.height(10.dp))
        Text(stat.value, style = MaterialTheme.typography.headlineMedium)
        Text(stat.label, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
    }
}

@Composable
private fun AdminManageRow(icon: ImageVector, label: String, onClick: () -> Unit) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Icon(icon, contentDescription = null, tint = BluePrimary)
        Spacer(Modifier.width(14.dp))
        Text(label, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.weight(1f))
        Icon(Icons.Default.ChevronRight, contentDescription = null, tint = TextMuted)
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 800)
@Composable
private fun AdminDashboardScreenPreview() {
    AICareerCoachTheme {
        AdminDashboardScreen()
    }
}
