package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarBorder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.data.network.ApiClient
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.SuccessGreen
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary
import com.aicareercoach.mobile.ui.theme.WarningAmber
import kotlinx.coroutines.launch

@Composable
fun FeedbackScreen(
    sessionToken: String = "",
    topic: String = "General feedback about your career coach experience",
    onBack: () -> Unit = {},
    onSubmit: () -> Unit = {}
) {
    val scope = rememberCoroutineScope()
    var rating by remember { mutableStateOf(0) }
    var accurate by remember { mutableStateOf<Boolean?>(null) }
    var comments by remember { mutableStateOf("") }
    var submitted by remember { mutableStateOf(false) }
    var submitError by remember { mutableStateOf<String?>(null) }
    var submitting by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
    ) {
        AppTopBar(
            title = "Feedback",
            subtitle = "Help us improve the coach",
            onBack = onBack,
            showProfile = false
        )

        if (submitted) {
            Column(
                modifier = Modifier.fillMaxSize().padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Spacer(Modifier.height(40.dp))
                Icon(Icons.Default.CheckCircle, contentDescription = null, tint = SuccessGreen, modifier = Modifier.size(56.dp))
                Spacer(Modifier.height(12.dp))
                Text("Thanks — feedback recorded", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(8.dp))
                Text(
                    "Your feedback has been saved to the career coach database.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary
                )
                Spacer(Modifier.height(24.dp))
                PrimaryButton(text = "Back", onClick = onSubmit)
            }
            return
        }

        Column(modifier = Modifier.padding(horizontal = 20.dp).padding(bottom = 20.dp).fillMaxSize()) {
            SectionCard {
                Text("About your experience", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(6.dp))
                Text(topic, style = MaterialTheme.typography.bodyMedium, color = TextSecondary)
            }

            submitError?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(top = 8.dp)) }

            Spacer(Modifier.height(16.dp))

            SectionCard {
                Text("Rate this response", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    for (i in 1..5) {
                        IconButton(onClick = { rating = i }) {
                            Icon(
                                imageVector = if (i <= rating) Icons.Default.Star else Icons.Default.StarBorder,
                                contentDescription = "Star $i",
                                tint = WarningAmber,
                                modifier = Modifier.size(32.dp)
                            )
                        }
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            SectionCard {
                Text("Was this accurate?", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(selected = accurate == true, onClick = { accurate = true }, label = { Text("Yes") })
                    FilterChip(selected = accurate == false, onClick = { accurate = false }, label = { Text("No") })
                }
            }

            Spacer(Modifier.height(16.dp))

            SectionCard {
                Text("Tell us more (optional)", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(10.dp))
                OutlinedTextField(
                    value = comments,
                    onValueChange = { comments = it },
                    placeholder = { Text("Was the advice relevant and easy to understand?") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(120.dp),
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)
                )
            }

            Spacer(Modifier.weight(1f))

            PrimaryButton(
                text = "Submit Feedback",
                enabled = rating > 0 && accurate != null && !submitting,
                onClick = {
                    scope.launch {
                        submitting = true
                        val saved = ApiClient.submitFeedback(
                            rating = rating,
                            isAccurate = accurate ?: false,
                            comments = comments,
                            token = sessionToken
                        )
                        submitting = false
                        if (saved) submitted = true else submitError = "Feedback was not saved. Check your connection and try again."
                    }
                }
            )
        }
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
private fun FeedbackScreenPreview() {
    AICareerCoachTheme {
        FeedbackScreen()
    }
}
