package com.aicareercoach.mobile.ui.screens

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

private data class AdminStat(val label: String, val value: String, val icon: ImageVector, val color: Color)
private data class FlaggedResponse(val query: String, val reason: String)

@Composable
fun AdminDashboardScreen(
    onLogOut: () -> Unit = {}
) {
    val stats = listOf(
        AdminStat("Active Students", "1,248", Icons.Default.Group, BluePrimary),
        AdminStat("Career Resources", "312", Icons.Default.Description, SuccessGreen),
        AdminStat("Chats This Week", "3,904", Icons.Default.Chat, WarningAmber),
        AdminStat("Flagged Responses", "6", Icons.Default.Flag, DangerRed),
    )

    var flagged by remember {
        mutableStateOf(
            listOf(
                FlaggedResponse("Is a master's degree necessary for a data analyst role?", "Low retrieval confidence"),
                FlaggedResponse("What is the average salary for a UX designer in Nairobi?", "Unverified figure"),
            )
        )
    }

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(title = "Admin Dashboard", subtitle = "Platform overview and moderation", showProfile = false)

        LazyColumn(
            modifier = Modifier.padding(horizontal = 20.dp),
            contentPadding = PaddingValues(bottom = 24.dp)
        ) {
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

                Spacer(Modifier.height(20.dp))
                Text("Responses awaiting review", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(10.dp))
            }

            items(flagged, key = { it.query }) { response ->
                SectionCard(modifier = Modifier.padding(bottom = 10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Warning, contentDescription = null, tint = WarningAmber)
                        Spacer(Modifier.width(10.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(response.query, style = MaterialTheme.typography.bodyMedium)
                            Spacer(Modifier.height(4.dp))
                            Text(response.reason, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                        }
                    }
                    Spacer(Modifier.height(10.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(
                            onClick = { flagged = flagged.filterNot { it.query == response.query } },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(10.dp)
                        ) {
                            Text("Reject")
                        }
                        Button(
                            onClick = { flagged = flagged.filterNot { it.query == response.query } },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(10.dp)
                        ) {
                            Text("Approve")
                        }
                    }
                }
            }

            item {
                Spacer(Modifier.height(10.dp))
                Text("Manage", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(10.dp))
                SectionCard {
                    AdminManageRow(Icons.Default.LibraryAdd, "Upload Career Resource")
                    HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                    AdminManageRow(Icons.Default.ManageAccounts, "Manage User Accounts")
                    HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                    AdminManageRow(Icons.Default.Insights, "View Usage Analytics")
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
private fun StatCard(stat: AdminStat, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .padding(14.dp)
    ) {
        Icon(stat.icon, contentDescription = null, tint = stat.color)
        Spacer(Modifier.height(10.dp))
        Text(stat.value, style = MaterialTheme.typography.headlineMedium)
        Text(stat.label, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
    }
}

@Composable
private fun AdminManageRow(icon: ImageVector, label: String) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .clickable { }
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
