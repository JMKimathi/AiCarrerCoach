package com.aicareercoach.mobile.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.CareerResource
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.components.AppTextField
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary
import kotlinx.coroutines.launch

/** Lets an administrator change a knowledge-base resource's title, category and content. */
@Composable
fun AdminEditResourceScreen(
    token: String,
    resource: CareerResource,
    onBack: () -> Unit = {},
    onSaved: (CareerResource) -> Unit = {}
) {
    var title by remember { mutableStateOf(resource.title) }
    var category by remember { mutableStateOf(resource.category) }
    var content by remember { mutableStateOf("") }
    var loaded by remember { mutableStateOf(false) }
    var loadFailed by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var saving by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(token, resource.id) {
        val existing = ApiClient.getResourceContent(token, resource.id)
        if (existing == null) loadFailed = true else content = existing
        loaded = true
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
            .imePadding()
    ) {
        AppTopBar(title = "Edit resource", onBack = onBack, showProfile = false)
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
        ) {
            Text(
                when {
                    !loaded -> "Loading the current content…"
                    loadFailed -> "The current content could not be loaded. Check the backend connection and go back to try again."
                    else -> "Changes apply to the stored resource straight away."
                },
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary
            )
            Spacer(Modifier.height(20.dp))
            AppTextField(label = "Title", value = title, onValueChange = { title = it })
            Spacer(Modifier.height(14.dp))
            AppTextField(label = "Category", value = category, onValueChange = { category = it })
            Spacer(Modifier.height(14.dp))
            OutlinedTextField(
                value = content,
                onValueChange = { content = it },
                label = { Text("Content") },
                minLines = 8,
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            )
            val message = error
            if (message != null) {
                Spacer(Modifier.height(10.dp))
                Text(message, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            }
            Spacer(Modifier.height(24.dp))
            PrimaryButton(
                text = if (saving) "Saving…" else "Save changes",
                enabled = loaded && !loadFailed && !saving
            ) {
                if (title.trim().length < 3 || category.trim().length < 2 || content.trim().length < 10) {
                    error = "Title, category and content are all required."
                } else {
                    saving = true
                    error = null
                    scope.launch {
                        val updated = ApiClient.updateResource(
                            token, resource.id, title.trim(), category.trim(), content.trim()
                        )
                        saving = false
                        if (updated == null) {
                            error = "The changes were not saved. Check the backend connection and your administrator access."
                        } else {
                            onSaved(updated)
                        }
                    }
                }
            }
            Spacer(Modifier.height(20.dp))
        }
    }
}
