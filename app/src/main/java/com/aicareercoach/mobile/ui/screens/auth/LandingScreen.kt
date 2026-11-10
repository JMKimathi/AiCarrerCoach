package com.aicareercoach.mobile.ui.screens.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Explore
import androidx.compose.material.icons.filled.Forum
import androidx.compose.material.icons.filled.RecordVoiceOver
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
import androidx.compose.ui.unit.sp
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.components.SecondaryButton
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.BlueLight
import com.aicareercoach.mobile.ui.theme.BluePrimary
import com.aicareercoach.mobile.ui.theme.SuccessGreen
import com.aicareercoach.mobile.ui.theme.TextMuted
import com.aicareercoach.mobile.ui.theme.TextSecondary
import com.aicareercoach.mobile.ui.theme.WarningAmber

private val AccentViolet = Color(0xFF7C3AED)

@Composable
fun LandingScreen(
    onGetStarted: () -> Unit = {},
    onLogIn: () -> Unit = {},
    onBackendSettings: () -> Unit = {}
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Brush.verticalGradient(listOf(BlueLight, Color.White, Color.White)))
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 24.dp)
    ) {
        Spacer(Modifier.height(32.dp))

        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(BluePrimary),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.Explore, contentDescription = null, tint = Color.White)
            }
            Spacer(Modifier.width(10.dp))
            Text("Career Coach", style = MaterialTheme.typography.titleLarge)
        }

        Spacer(Modifier.height(36.dp))

        Text(
            "From campus\nto your first role.",
            style = MaterialTheme.typography.headlineLarge.copy(fontSize = 34.sp, lineHeight = 40.sp)
        )

        Spacer(Modifier.height(12.dp))

        Text(
            "Explore careers, shape a CV for the job you want, and practise the interview before it counts.",
            style = MaterialTheme.typography.bodyLarge,
            color = TextSecondary
        )

        Spacer(Modifier.height(28.dp))

        LandingFeature(
            Icons.Default.Explore, BluePrimary, "Explore 450+ careers",
            "See what a role involves, the skills it needs and how people get in."
        )
        Spacer(Modifier.height(10.dp))
        LandingFeature(
            Icons.Default.Description, SuccessGreen, "Build your CV",
            "Turn your projects and experience into a CV shaped for the role."
        )
        Spacer(Modifier.height(10.dp))
        LandingFeature(
            Icons.Default.RecordVoiceOver, WarningAmber, "Practise interviews",
            "Answer realistic questions and see what to sharpen."
        )
        Spacer(Modifier.height(10.dp))
        LandingFeature(
            Icons.Default.Forum, AccentViolet, "Ask the coach",
            "Get straight answers about courses, skills and next steps."
        )

        Spacer(Modifier.height(28.dp))

        PrimaryButton(text = "Create your account", onClick = onGetStarted)
        Spacer(Modifier.height(12.dp))
        SecondaryButton(text = "I already have an account", onClick = onLogIn)
        Spacer(Modifier.height(4.dp))
        TextButton(
            onClick = onBackendSettings,
            modifier = Modifier.align(Alignment.CenterHorizontally)
        ) {
            Text("Connection settings", style = MaterialTheme.typography.labelMedium, color = TextMuted)
        }

        Spacer(Modifier.height(20.dp))
    }
}

@Composable
private fun LandingFeature(icon: ImageVector, accent: Color, title: String, caption: String) {
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(accent.copy(alpha = 0.12f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(icon, contentDescription = null, tint = accent)
            }
            Spacer(Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(2.dp))
                Text(caption, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
            }
        }
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
private fun LandingScreenPreview() {
    AICareerCoachTheme {
        LandingScreen()
    }
}
