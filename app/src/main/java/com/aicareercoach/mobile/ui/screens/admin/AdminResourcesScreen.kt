package com.aicareercoach.mobile.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Description
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.CareerResource
import com.aicareercoach.mobile.data.SampleData
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.components.Tag
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.BluePrimary
import com.aicareercoach.mobile.ui.theme.DangerRed
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary

@Composable
fun AdminResourcesScreen(
    resources: List<CareerResource>,
    onUpload: () -> Unit = {},
    onEdit: (CareerResource) -> Unit = {},
    onDelete: (CareerResource) -> Unit = {}
) {
    var pendingDelete by remember { mutableStateOf<CareerResource?>(null) }
    Box(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        Column(modifier = Modifier.fillMaxSize()) {
            AppTopBar(
                title = "Knowledge base",
                subtitle = "${resources.size} resources grounding the coach",
                showProfile = false
            )
            LazyColumn(
                modifier = Modifier.padding(horizontal = 20.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
                contentPadding = PaddingValues(bottom = 88.dp)
            ) {
                items(resources, key = { it.id }) { resource ->
                    SectionCard {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Description, contentDescription = null, tint = BluePrimary)
                            Spacer(Modifier.width(12.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Text(resource.title, style = MaterialTheme.typography.titleMedium)
                                Spacer(Modifier.height(4.dp))
                                Tag(resource.category, BluePrimary)
                                Spacer(Modifier.height(6.dp))
                                Text(resource.summary, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                                Row {
                                    TextButton(onClick = { onEdit(resource) }) { Text("Edit") }
                                    TextButton(onClick = { pendingDelete = resource }) {
                                        Text("Delete", color = DangerRed)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        val target = pendingDelete
        if (target != null) {
            AlertDialog(
                onDismissRequest = { pendingDelete = null },
                title = { Text("Delete resource?") },
                text = { Text("\"${target.title}\" will be removed from the knowledge base. This cannot be undone.") },
                confirmButton = {
                    TextButton(onClick = {
                        pendingDelete = null
                        onDelete(target)
                    }) { Text("Delete", color = DangerRed) }
                },
                dismissButton = {
                    TextButton(onClick = { pendingDelete = null }) { Text("Cancel") }
                }
            )
        }
        FloatingActionButton(
            onClick = onUpload,
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(20.dp)
        ) {
            Icon(Icons.Default.Add, contentDescription = "Upload resource")
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun AdminResourcesScreenPreview() {
    AICareerCoachTheme { AdminResourcesScreen(SampleData.resources) }
}
