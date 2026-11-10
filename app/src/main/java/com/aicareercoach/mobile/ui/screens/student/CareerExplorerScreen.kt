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
import androidx.compose.material.icons.filled.Work
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.CareerCategory
import com.aicareercoach.mobile.data.CareerSummary
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.components.Tag
import com.aicareercoach.mobile.ui.theme.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private const val CAREER_PAGE_SIZE = 50

/** Browse and search the career catalogue served by the backend. */
@Composable
fun CareerExplorerScreen(
    session: UserSession,
    onBack: () -> Unit = {},
    onOpenCareer: (String) -> Unit = {},
    onOpenAssessment: () -> Unit = {}
) {
    var categories by remember { mutableStateOf<List<CareerCategory>>(emptyList()) }
    var selectedCategory by rememberSaveable { mutableStateOf<String?>(null) }
    var query by rememberSaveable { mutableStateOf("") }
    val careers = remember { mutableStateListOf<CareerSummary>() }
    var total by remember { mutableStateOf(0) }
    var loading by remember { mutableStateOf(true) }
    var loadingMore by remember { mutableStateOf(false) }
    var failed by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(session.token) {
        ApiClient.getCareerCategories(session.token)?.let { categories = it }
    }

    // Reload from the first page whenever the filter changes; wait briefly while the student is typing.
    LaunchedEffect(session.token, selectedCategory, query) {
        if (query.isNotBlank()) delay(350)
        loading = true
        failed = false
        val page = ApiClient.searchCareers(session.token, selectedCategory, query, offset = 0, limit = CAREER_PAGE_SIZE)
        careers.clear()
        if (page == null) {
            failed = true
            total = 0
        } else {
            careers.addAll(page.items)
            total = page.total
        }
        loading = false
    }

    val chipLabels: List<String?> = listOf<String?>(null) + categories.map { it.name }

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(
            title = "Explore Careers",
            subtitle = "Roles, skills and how to get in",
            onBack = onBack,
            showProfile = false
        )

        OutlinedTextField(
            value = query,
            onValueChange = { query = it.take(80) },
            placeholder = { Text("Search by role or skill") },
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
            items(chipLabels) { name ->
                ExplorerChip(label = name ?: "All", selected = name == selectedCategory) {
                    selectedCategory = name
                }
            }
        }

        Spacer(Modifier.height(12.dp))

        val status = when {
            loading -> "Loading careers…"
            failed -> "Careers could not be loaded. Check that the backend is running and try again."
            careers.isEmpty() -> "No careers match this search."
            else -> "$total careers found"
        }
        Text(
            status,
            modifier = Modifier.padding(horizontal = 20.dp),
            style = MaterialTheme.typography.bodyMedium,
            color = TextSecondary
        )

        Spacer(Modifier.height(8.dp))

        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(bottom = 20.dp)
        ) {
            item {
                SectionCard(onClick = onOpenAssessment) {
                    Text("Not sure where to start?", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Answer a few questions about your skills and interests to see roles worth exploring.",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Take the career assessment →",
                        color = MaterialTheme.colorScheme.primary,
                        style = MaterialTheme.typography.labelLarge
                    )
                }
            }
            items(careers, key = { it.careerId }) { career ->
                SectionCard(onClick = { onOpenCareer(career.careerId) }) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Work, contentDescription = null, tint = BluePrimary)
                        Spacer(Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(career.roleTitle, style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(4.dp))
                            Text(
                                career.coreSkills.take(3).joinToString(" · "),
                                style = MaterialTheme.typography.bodySmall,
                                color = TextSecondary,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            Spacer(Modifier.height(6.dp))
                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                Tag(career.category, BluePrimary)
                                if (career.commonlyRegulated) Tag("Regulated", WarningAmber)
                            }
                        }
                        Icon(Icons.Default.ChevronRight, contentDescription = null, tint = TextMuted)
                    }
                }
            }
            if (!loading && careers.size < total) {
                item {
                    TextButton(
                        onClick = {
                            scope.launch {
                                loadingMore = true
                                val page = ApiClient.searchCareers(
                                    session.token, selectedCategory, query,
                                    offset = careers.size, limit = CAREER_PAGE_SIZE
                                )
                                if (page != null) {
                                    val known = careers.map { it.careerId }.toSet()
                                    careers.addAll(page.items.filter { it.careerId !in known })
                                    total = page.total
                                }
                                loadingMore = false
                            }
                        },
                        enabled = !loadingMore,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(if (loadingMore) "Loading…" else "Load more (${careers.size} of $total)")
                    }
                }
            }
        }
    }
}

@Composable
private fun ExplorerChip(label: String, selected: Boolean, onClick: () -> Unit) {
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
