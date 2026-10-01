package com.aicareercoach.mobile.ui.screens.student

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
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.BlueLight
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary

private data class QuickAction(val label: String, val icon: ImageVector, val onClick: () -> Unit)

@Composable
fun StudentDashboardScreen(
    session: UserSession = UserSession("John Mwiti", "john.mwiti@strathmore.edu"),
    onOpenChat: () -> Unit = {},
    onOpenResources: () -> Unit = {},
    onOpenProfile: () -> Unit = {},
    onReviewCv: () -> Unit = {},
    onInterviewPrep: () -> Unit = {},
    onExploreCareers: () -> Unit = onOpenResources
) {
    val quickActions = listOf(
        QuickAction("Ask Career\nQuestion", Icons.Default.Chat, onOpenChat),
        QuickAction("Review My\nCV", Icons.Default.Description, onReviewCv),
        QuickAction("Interview\nPrep", Icons.Default.RecordVoiceOver, onInterviewPrep),
        QuickAction("Explore\nCareers", Icons.Default.Explore, onExploreCareers),
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
    ) {
        AppTopBar(
            title = "Hi, ${session.firstName} 👋",
            subtitle = session.course,
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

            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                MiniStat("Course", session.course.ifBlank { "Not provided" }, Modifier.weight(1f))
                MiniStat("Career goal", session.careerGoal.ifBlank { "Not provided" }, Modifier.weight(1f))
            }

            Spacer(Modifier.height(16.dp))

            SectionCard(onClick = onOpenChat) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.width(8.dp))
                    Text("Ask the career coach", style = MaterialTheme.typography.titleMedium)
                }
                Spacer(Modifier.height(8.dp))
                Text(
                    "Get guidance based on your profile: ${session.course.ifBlank { "your course" }} and ${session.careerGoal.ifBlank { "your interests" }}.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary
                )
                Spacer(Modifier.height(12.dp))
                Text("Start a conversation →", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.labelLarge)
            }

            Spacer(Modifier.height(16.dp))

            Text("Recommended for you", style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(10.dp))

            SectionCard(onClick = onOpenResources) {
                DashboardRow(Icons.Default.Description, "CV Templates", "Match your CV to internship language")
            }
            Spacer(Modifier.height(10.dp))
            SectionCard(onClick = onExploreCareers) {
                DashboardRow(Icons.Default.Explore, "Explore career paths", "Compare roles and the skills they require")
            }
            Spacer(Modifier.height(10.dp))
            SectionCard(onClick = onInterviewPrep) {
                DashboardRow(Icons.Default.School, "Interview preparation", "Use the interview resources to practise")
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
private fun MiniStat(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(BlueLight)
            .padding(14.dp)
    ) {
        Text(label, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
        Spacer(Modifier.height(4.dp))
        Text(value, style = MaterialTheme.typography.titleMedium)
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
