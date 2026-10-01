package com.aicareercoach.mobile.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary
import com.aicareercoach.mobile.data.AdminOverview

@Composable
fun AdminAnalyticsScreen(overview: AdminOverview? = null) {
    val rows = listOf(
        "Active students" to (overview?.activeStudents?.toString() ?: "Unavailable"),
        "Resources" to (overview?.careerResources?.toString() ?: "Unavailable"),
        "Chats this week" to (overview?.chatsThisWeek?.toString() ?: "Unavailable"),
        "Inaccurate response feedback" to (overview?.flaggedResponses?.toString() ?: "Unavailable"),
        "Most referenced resource" to (overview?.topResources?.firstOrNull() ?: "No usage recorded"),
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
    ) {
        AppTopBar(title = "Analytics", subtitle = "How students are using the coach", showProfile = false)
        Column(
            modifier = Modifier
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(bottom = 24.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            rows.forEach { (label, value) ->
                SectionCard {
                    Text(label, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                    Spacer(Modifier.height(4.dp))
                    Text(value, style = MaterialTheme.typography.titleLarge)
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun AdminAnalyticsScreenPreview() {
    AICareerCoachTheme { AdminAnalyticsScreen() }
}
