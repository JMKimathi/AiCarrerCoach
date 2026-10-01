package com.aicareercoach.mobile.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.CareerResource
import com.aicareercoach.mobile.ui.components.AppTextField
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary
import java.util.UUID
import com.aicareercoach.mobile.data.network.ApiClient
import kotlinx.coroutines.launch

@Composable
fun AdminUploadScreen(
    token: String = "",
    onBack: () -> Unit = {},
    onUploaded: (CareerResource) -> Unit = {}
) {
    val categories = listOf("CV Templates", "Interview Prep", "Career Paths", "Skill Building")
    var title by remember { mutableStateOf("") }
    var category by remember { mutableStateOf(categories.first()) }
    var summary by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    var submitting by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(title = "Upload resource", onBack = onBack, showProfile = false)
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
        ) {
            Text(
                "New pages join the knowledge base the chatbot retrieves from.",
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary
            )
            Spacer(Modifier.height(20.dp))
            AppTextField(label = "Title", value = title, onValueChange = { title = it })
            Spacer(Modifier.height(14.dp))
            AppTextField(label = "Category", value = category, onValueChange = { category = it })
            Spacer(Modifier.height(14.dp))
            AppTextField(label = "Summary", value = summary, onValueChange = { summary = it })
            if (error != null) {
                Spacer(Modifier.height(10.dp))
                Text(error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            }
            Spacer(Modifier.height(24.dp))
            PrimaryButton(text = if (submitting) "Saving…" else "Add to knowledge base", enabled = !submitting) {
                if (title.isBlank() || summary.isBlank()) {
                    error = "Title and summary are required."
                } else {
                    submitting = true
                    scope.launch {
                        val resource = ApiClient.createResource(token, title.trim(), category.trim().ifBlank { "Career Paths" }, summary.trim())
                        submitting = false
                        if (resource == null) error = "The resource was not saved. Check the backend connection and your administrator access."
                        else onUploaded(resource)
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun AdminUploadScreenPreview() {
    AICareerCoachTheme { AdminUploadScreen() }
}
