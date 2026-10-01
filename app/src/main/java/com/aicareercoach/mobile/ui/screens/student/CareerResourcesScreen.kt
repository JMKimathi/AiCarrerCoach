package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Description
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.CareerResource
import com.aicareercoach.mobile.data.SampleData
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.components.Tag
import com.aicareercoach.mobile.ui.theme.*

@Composable
fun CareerResourcesScreen(
    resources: List<CareerResource> = SampleData.resources,
    onOpenResource: (CareerResource) -> Unit = {}
) {
    val categories = listOf("All", "CV Templates", "Interview Prep", "Career Paths", "Skill Building")
    var selectedCategory by remember { mutableStateOf(categories.first()) }
    var query by remember { mutableStateOf("") }

    val filtered = resources.filter { resource ->
        val matchesCategory = selectedCategory == "All" || resource.category == selectedCategory
        val matchesQuery = query.isBlank() ||
            resource.title.contains(query, ignoreCase = true) ||
            resource.summary.contains(query, ignoreCase = true)
        matchesCategory && matchesQuery
    }

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(
            title = "Career Resources",
            subtitle = "Curated content backing your AI coach",
            showProfile = false
        )

        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            placeholder = { Text("Search resources") },
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp),
            shape = RoundedCornerShape(12.dp),
            singleLine = true
        )

        Spacer(Modifier.height(12.dp))

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

        if (filtered.isEmpty()) {
            Text(
                "No resources in this filter yet.",
                modifier = Modifier.padding(horizontal = 20.dp),
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary
            )
        } else {
            LazyColumn(
                modifier = Modifier.padding(horizontal = 20.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
                contentPadding = PaddingValues(bottom = 20.dp)
            ) {
                items(filtered, key = { it.id }) { resource ->
                    SectionCard(onClick = { onOpenResource(resource) }) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Description, contentDescription = null, tint = BluePrimary)
                            Spacer(Modifier.width(12.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Text(resource.title, style = MaterialTheme.typography.titleMedium)
                                Spacer(Modifier.height(4.dp))
                                Tag(resource.category, BluePrimary)
                            }
                            Icon(Icons.Default.ChevronRight, contentDescription = null, tint = TextMuted)
                        }
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
