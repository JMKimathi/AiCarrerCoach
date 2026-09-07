package com.aicareercoach.mobile.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
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
import com.aicareercoach.mobile.ui.components.Tag
import com.aicareercoach.mobile.ui.theme.*

private data class Resource(val title: String, val category: String, val icon: ImageVector, val color: Color)

@Composable
fun CareerResourcesScreen(
    onOpenChat: () -> Unit = {}
) {
    val categories = listOf("All", "CV Templates", "Interview Prep", "Career Paths", "Skill Building")
    var selectedCategory by remember { mutableStateOf(categories.first()) }

    val resources = listOf(
        Resource("Software Engineer CV Template", "CV Templates", Icons.Default.Description, BluePrimary),
        Resource("Behavioural Interview Question Bank", "Interview Prep", Icons.Default.RecordVoiceOver, SuccessGreen),
        Resource("Careers in Data Science", "Career Paths", Icons.Default.Explore, WarningAmber),
        Resource("Technical Interview Practice: Algorithms", "Interview Prep", Icons.Default.Code, SuccessGreen),
        Resource("Building a Portfolio Website", "Skill Building", Icons.Default.School, DangerRed),
        Resource("Cover Letter Writing Guide", "CV Templates", Icons.Default.Description, BluePrimary),
    )

    val filtered = if (selectedCategory == "All") resources else resources.filter { it.category == selectedCategory }

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(
            title = "Career Resources",
            subtitle = "Curated content backing your AI coach",
            showProfile = false
        )

        LazyRow(
            modifier = Modifier.padding(horizontal = 20.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(categories) { category ->
                CategoryChip(category, selected = category == selectedCategory) {
                    selectedCategory = category
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        LazyColumn(
            modifier = Modifier.padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(bottom = 20.dp)
        ) {
            items(filtered) { resource ->
                SectionCard(onClick = onOpenChat) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(resource.icon, contentDescription = null, tint = resource.color)
                        Spacer(Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(resource.title, style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(4.dp))
                            Tag(resource.category, resource.color)
                        }
                        Icon(Icons.Default.ChevronRight, contentDescription = null, tint = TextMuted)
                    }
                }
            }
        }
    }
}

@Composable
private fun CategoryChip(label: String, selected: Boolean, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(if (selected) BluePrimary else Color.White)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        Text(
            label,
            style = MaterialTheme.typography.labelLarge,
            color = if (selected) Color.White else TextSecondary
        )
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
private fun CareerResourcesScreenPreview() {
    AICareerCoachTheme {
        CareerResourcesScreen()
    }
}
