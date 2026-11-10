package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.BluePrimary
import com.aicareercoach.mobile.ui.theme.BluePrimaryDark
import com.aicareercoach.mobile.ui.theme.BorderLight
import com.aicareercoach.mobile.ui.theme.SuccessGreen
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextMuted
import com.aicareercoach.mobile.ui.theme.TextSecondary
import com.aicareercoach.mobile.ui.theme.WarningAmber

private val DashboardViolet = Color(0xFF7C3AED)

@Composable
fun StudentDashboardScreen(
    session: UserSession = UserSession("John Mwiti", "john.mwiti@strathmore.edu"),
    onOpenChat: () -> Unit = {},
    onOpenResources: () -> Unit = {},
    onOpenProfile: () -> Unit = {},
    onExploreCareers: () -> Unit = {},
    onBuildCv: () -> Unit = {},
    onMockInterview: () -> Unit = {},
    onOpenAssessment: () -> Unit = {}
) {
    val profileLine = listOf(session.course, session.careerGoal)
        .filter { it.isNotBlank() }
        .joinToString(" · ")
        .ifBlank { "Add your course and career goal so advice fits you." }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
    ) {
        AppTopBar(
            title = "Hi, ${session.firstName}",
            subtitle = "Let's get you ready for what's next",
            onProfileClick = onOpenProfile
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            // The one main action: talk to the coach.
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(20.dp))
                    .background(Brush.linearGradient(listOf(BluePrimary, BluePrimaryDark)))
                    .clickable(onClick = onOpenChat)
                    .padding(20.dp)
            ) {
                Text(
                    "What would you like to work on?",
                    style = MaterialTheme.typography.titleLarge,
                    color = Color.White
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    "Ask about a career, your CV or an interview coming up.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White.copy(alpha = 0.85f)
                )
                Spacer(Modifier.height(16.dp))
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color.White)
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Default.Chat,
                        contentDescription = null,
                        tint = BluePrimary,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(Modifier.width(8.dp))
                    Text("Ask the coach", style = MaterialTheme.typography.labelLarge, color = BluePrimary)
                }
            }

            Text("Get ready", style = MaterialTheme.typography.titleLarge)

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(IntrinsicSize.Min),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                ActionTile(
                    Icons.Default.Explore, BluePrimary, "Explore careers", "Roles, skills and routes in",
                    onExploreCareers, Modifier.weight(1f).fillMaxHeight()
                )
                ActionTile(
                    Icons.Default.Description, SuccessGreen, "Build my CV", "Shaped for the role you want",
                    onBuildCv, Modifier.weight(1f).fillMaxHeight()
                )
            }
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(IntrinsicSize.Min),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                ActionTile(
                    Icons.Default.RecordVoiceOver, WarningAmber, "Practise interview", "Questions with feedback",
                    onMockInterview, Modifier.weight(1f).fillMaxHeight()
                )
                ActionTile(
                    Icons.Default.Insights, DashboardViolet, "Find my fit", "A short career assessment",
                    onOpenAssessment, Modifier.weight(1f).fillMaxHeight()
                )
            }

            SectionCard(onClick = onOpenProfile) {
                DashboardRow(Icons.Default.Person, "Your profile", profileLine)
            }
            SectionCard(onClick = onOpenResources) {
                DashboardRow(Icons.Default.MenuBook, "Guides and templates", "CV, cover letter and interview guides")
            }

            Spacer(Modifier.height(8.dp))
        }
    }
}

@Composable
private fun ActionTile(
    icon: ImageVector,
    accent: Color,
    title: String,
    caption: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .border(1.dp, BorderLight, RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
            .padding(16.dp)
    ) {
        Box(
            modifier = Modifier
                .size(40.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(accent.copy(alpha = 0.12f)),
            contentAlignment = Alignment.Center
        ) {
            Icon(icon, contentDescription = null, tint = accent)
        }
        Spacer(Modifier.height(12.dp))
        Text(title, style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(2.dp))
        Text(caption, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
    }
}

@Composable
private fun DashboardRow(icon: ImageVector, title: String, subtitle: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.width(12.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
        }
        Icon(Icons.Default.ChevronRight, contentDescription = null, tint = TextMuted)
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
private fun StudentDashboardScreenPreview() {
    AICareerCoachTheme {
        StudentDashboardScreen()
    }
}
