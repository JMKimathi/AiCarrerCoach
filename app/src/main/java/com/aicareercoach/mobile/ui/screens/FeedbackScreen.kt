package com.aicareercoach.mobile.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarBorder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary
import com.aicareercoach.mobile.ui.theme.WarningAmber

@Composable
fun FeedbackScreen(
    onBack: () -> Unit = {},
    onSubmit: () -> Unit = {}
) {
    var rating by remember { mutableStateOf(0) }
    var comments by remember { mutableStateOf("") }

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

        Column(modifier = Modifier.padding(horizontal = 20.dp).padding(bottom = 20.dp).fillMaxSize()) {
            Text(
                "Your feedback helps us verify AI-generated advice and improve future recommendations.",
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary
            )

            Spacer(Modifier.height(20.dp))

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
                Text("Tell us more (optional)", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(10.dp))
                OutlinedTextField(
                    value = comments,
                    onValueChange = { comments = it },
                    placeholder = { Text("Was the advice accurate, relevant, and easy to understand?") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(120.dp),
                    shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)
                )
            }

            Spacer(Modifier.weight(1f))

            PrimaryButton(
                text = "Submit Feedback",
                enabled = rating > 0,
                onClick = onSubmit
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
