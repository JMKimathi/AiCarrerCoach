package com.aicareercoach.mobile.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary

private data class QuickAction(val label: String, val icon: ImageVector, val onClick: () -> Unit)

@Composable
fun StudentDashboardScreen(
    studentName: String = "Faith",
    onOpenChat: () -> Unit = {},
    onOpenResources: () -> Unit = {},
    onOpenProfile: () -> Unit = {},
    onReviewCv: () -> Unit = {},
    onInterviewPrep: () -> Unit = {}
) {
    val quickActions = listOf(
        QuickAction("Ask Career\nQuestion", Icons.Default.Chat, onOpenChat),
        QuickAction("Review My\nCV", Icons.Default.Description, onReviewCv),
        QuickAction("Interview\nPrep", Icons.Default.RecordVoiceOver, onInterviewPrep),
        QuickAction("Explore\nCareers", Icons.Default.Explore, onOpenResources),
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
    ) {
        AppTopBar(
            title = "Hi, $studentName 👋",
            subtitle = "Ready to plan your next career move?",
            onProfileClick = onOpenProfile
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp),
        ) {
            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                items(quickActions.size) { index ->
                    QuickActionChip(quickActions[index])
                }
            }

            Spacer(Modifier.height(20.dp))

            SectionCard(onClick = onOpenChat) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.width(8.dp))
                    Text("Continue your conversation", style = MaterialTheme.typography.titleMedium)
                }
                Spacer(Modifier.height(8.dp))
                Text(
                    "\"What roles suit a computer science graduate interested in AI?\"",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary
                )
                Spacer(Modifier.height(12.dp))
                Text("Resume chat →", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.labelLarge)
            }

            Spacer(Modifier.height(16.dp))

            Text("Recommended for you", style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(10.dp))

            SectionCard(onClick = onOpenResources) {
                DashboardRow(Icons.Default.Description, "CV Templates", "5 new templates added this week")
            }
            Spacer(Modifier.height(10.dp))
            SectionCard(onClick = onOpenResources) {
                DashboardRow(Icons.Default.Work, "Internship Openings", "12 opportunities matched to your profile")
            }
            Spacer(Modifier.height(10.dp))
            SectionCard(onClick = onOpenResources) {
                DashboardRow(Icons.Default.School, "Skill Building", "Recommended courses based on your goals")
            }

            Spacer(Modifier.height(16.dp))
            TextButton(onClick = onOpenResources, modifier = Modifier.fillMaxWidth()) {
                Text("Browse all career resources")
            }
            Spacer(Modifier.height(20.dp))
        }
    }
}

@Composable
private fun QuickActionChip(action: QuickAction) {
    Column(
        modifier = Modifier
            .width(88.dp)
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .clickable(onClick = action.onClick)
            .padding(vertical = 14.dp, horizontal = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(action.icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(8.dp))
        Text(
            action.label,
            style = MaterialTheme.typography.labelMedium,
            textAlign = TextAlign.Center
        )
    }
}

@Composable
private fun DashboardRow(icon: ImageVector, title: String, subtitle: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.width(12.dp))
        Column {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
        }
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
private fun StudentDashboardScreenPreview() {
    AICareerCoachTheme {
        StudentDashboardScreen()
    }
}
