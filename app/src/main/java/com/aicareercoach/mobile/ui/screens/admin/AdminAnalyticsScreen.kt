package com.aicareercoach.mobile.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.AdminFeedback
import com.aicareercoach.mobile.data.AdminOverview
import com.aicareercoach.mobile.data.DailyActivity
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.components.Tag
import com.aicareercoach.mobile.ui.theme.*

private val ChartHeight = 96.dp

/** Usage over the last seven days and what students said about the coach's answers. */
@Composable
fun AdminAnalyticsScreen(
    overview: AdminOverview? = null,
    activity: List<DailyActivity> = emptyList(),
    feedback: List<AdminFeedback> = emptyList(),
    onRefresh: () -> Unit = {}
) {
    var flaggedOnly by rememberSaveable { mutableStateOf(false) }
    val shownFeedback = if (flaggedOnly) feedback.filter { !it.isAccurate } else feedback

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(title = "Insights", subtitle = "How students are using the coach", showProfile = false)

        LazyColumn(
            modifier = Modifier.padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(bottom = 24.dp)
        ) {
            item {
                SectionCard {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Last 7 days", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                        IconButton(onClick = onRefresh) {
                            Icon(Icons.Default.Refresh, contentDescription = "Refresh insights", tint = BluePrimary)
                        }
                    }
                    if (activity.isEmpty()) {
                        Text("Daily activity could not be loaded. Tap refresh to try again.", color = TextSecondary)
                    } else {
                        Spacer(Modifier.height(6.dp))
                        ActivityChart(activity)
                        Spacer(Modifier.height(10.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                            Legend("Chats", BluePrimary, activity.sumOf { it.chats })
                            Legend("Interviews", SuccessGreen, activity.sumOf { it.interviews })
                            Legend("New students", WarningAmber, activity.sumOf { it.newStudents })
                        }
                    }
                }
            }

            item {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Figure("Interviews finished", overview?.interviewsCompleted?.toString() ?: "—", Modifier.weight(1f))
                    Figure("Assessments taken", overview?.assessmentsTotal?.toString() ?: "—", Modifier.weight(1f))
                }
                Spacer(Modifier.height(10.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Figure(
                        "Average rating",
                        overview?.averageRating?.let { String.format("%.1f / 5", it) } ?: "No ratings",
                        Modifier.weight(1f)
                    )
                    Figure("Marked inaccurate", overview?.flaggedResponses?.toString() ?: "—", Modifier.weight(1f))
                }
            }

            item {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Student feedback", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                    Toggle("All", !flaggedOnly) { flaggedOnly = false }
                    Spacer(Modifier.width(6.dp))
                    Toggle("Inaccurate", flaggedOnly) { flaggedOnly = true }
                }
            }

            if (shownFeedback.isEmpty()) item {
                Text(
                    if (flaggedOnly) "No answer has been marked inaccurate." else "No feedback has been submitted yet.",
                    color = TextSecondary
                )
            }
            items(shownFeedback, key = { it.id }) { item -> FeedbackCard(item) }
        }
    }
}

@Composable
private fun ActivityChart(activity: List<DailyActivity>) {
    val highest = activity.maxOf { maxOf(it.chats, it.interviews, it.newStudents) }.coerceAtLeast(1)
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Bottom
    ) {
        activity.forEach { day ->
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Row(
                    modifier = Modifier.height(ChartHeight),
                    horizontalArrangement = Arrangement.spacedBy(2.dp),
                    verticalAlignment = Alignment.Bottom
                ) {
                    Bar(day.chats, highest, BluePrimary)
                    Bar(day.interviews, highest, SuccessGreen)
                    Bar(day.newStudents, highest, WarningAmber)
                }
                Spacer(Modifier.height(4.dp))
                Text(day.label, style = MaterialTheme.typography.labelSmall, color = TextSecondary)
            }
        }
    }
}

@Composable
private fun Bar(value: Int, highest: Int, color: Color) {
    // A day with no activity still shows a thin line so the columns stay aligned.
    val height = if (value <= 0) 2.dp else ChartHeight * (value.toFloat() / highest.toFloat())
    Box(
        modifier = Modifier
            .width(7.dp)
            .height(height)
            .clip(RoundedCornerShape(topStart = 3.dp, topEnd = 3.dp))
            .background(if (value <= 0) BorderLight else color)
    )
}

@Composable
private fun Legend(label: String, color: Color, total: Int) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(modifier = Modifier.size(10.dp).clip(RoundedCornerShape(3.dp)).background(color))
        Spacer(Modifier.width(6.dp))
        Text("$label: $total", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
    }
}

@Composable
private fun Figure(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White)
            .padding(14.dp)
    ) {
        Text(value, style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(2.dp))
        Text(label, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
    }
}

@Composable
private fun Toggle(label: String, selected: Boolean, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(if (selected) BluePrimary else Color.White)
            .clickable(onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 6.dp)
    ) {
        Text(label, style = MaterialTheme.typography.labelLarge, color = if (selected) Color.White else TextSecondary)
    }
}

@Composable
private fun FeedbackCard(item: AdminFeedback) {
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Row(modifier = Modifier.weight(1f)) {
                repeat(5) { index ->
                    Icon(
                        Icons.Default.Star,
                        contentDescription = null,
                        tint = if (index < item.rating) WarningAmber else BorderLight,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }
            if (!item.isAccurate) Tag("Inaccurate", DangerRed)
        }
        Spacer(Modifier.height(8.dp))
        Text(
            item.comments.ifBlank { "No comment was written." },
            style = MaterialTheme.typography.bodyMedium,
            color = if (item.comments.isBlank()) TextMuted else TextPrimary
        )
        Spacer(Modifier.height(8.dp))
        Text(
            listOf(item.studentName, shortDate(item.createdAt)).filter { it.isNotBlank() }.joinToString("  •  "),
            style = MaterialTheme.typography.bodySmall,
            color = TextSecondary
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun AdminAnalyticsScreenPreview() {
    AICareerCoachTheme {
        AdminAnalyticsScreen(
            activity = listOf("Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed").mapIndexed { index, day ->
                DailyActivity(day, index * 2, index, index % 3)
            },
            feedback = listOf(
                AdminFeedback("1", "Amina Otieno", "amina@example.com", 2, false, "It named the wrong regulator.", "2026-11-10T10:00:00")
            )
        )
    }
}
