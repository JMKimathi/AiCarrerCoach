package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.*

@Composable
fun StudentProfileScreen(
    session: UserSession = UserSession("John Mwiti", "john.mwiti@strathmore.edu"),
    onEditProfile: () -> Unit = {},
    onOpenChat: () -> Unit = {},
    onOpenResources: () -> Unit = {},
    onOpenFeedback: () -> Unit = {},
    onOpenHelp: () -> Unit = {},
    onOpenPrivacy: () -> Unit = {},
    onLogOut: () -> Unit = {}
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
            .verticalScroll(rememberScrollState())
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(BluePrimary)
                .padding(top = 36.dp, bottom = 28.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(84.dp)
                    .clip(CircleShape)
                    .background(Color.White),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    session.initials,
                    style = MaterialTheme.typography.headlineMedium,
                    color = BluePrimary,
                    fontWeight = FontWeight.Bold
                )
            }
            Spacer(Modifier.height(12.dp))
            Text(session.name, style = MaterialTheme.typography.titleLarge, color = Color.White)
            Text(session.email, style = MaterialTheme.typography.bodyMedium, color = Color.White.copy(alpha = 0.85f))
            Spacer(Modifier.height(6.dp))
            Text(session.course, style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.9f))
            Text(session.careerGoal, style = MaterialTheme.typography.bodySmall, color = Color.White.copy(alpha = 0.9f))
        }

        Column(modifier = Modifier.padding(20.dp)) {
            SectionCard {
                ProfileRow(Icons.Default.Person, "Edit Profile", onEditProfile)
                HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                ProfileRow(Icons.Default.Description, "Career Resources", onOpenResources)
                HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                ProfileRow(Icons.Default.Chat, "Open Career Coach", onOpenChat)
            }

            Spacer(Modifier.height(16.dp))

            SectionCard {
                ProfileRow(Icons.Default.Feedback, "Send Feedback", onOpenFeedback)
                HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                ProfileRow(Icons.Default.HelpOutline, "Help & Support", onOpenHelp)
                HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp))
                ProfileRow(Icons.Default.PrivacyTip, "Privacy Policy", onOpenPrivacy)
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
            Spacer(Modifier.height(12.dp))
        }
    }
}

@Composable
private fun ProfileRow(icon: ImageVector, label: String, onClick: (() -> Unit)? = null) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(icon, contentDescription = null, tint = BluePrimary)
        Spacer(Modifier.width(14.dp))
        Text(label, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.weight(1f))
        Icon(Icons.Default.ChevronRight, contentDescription = null, tint = TextMuted)
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
private fun StudentProfileScreenPreview() {
    AICareerCoachTheme {
        StudentProfileScreen()
    }
}
