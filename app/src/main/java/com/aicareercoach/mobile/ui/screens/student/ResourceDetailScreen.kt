package com.aicareercoach.mobile.ui.screens.student

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
import com.aicareercoach.mobile.data.CareerResource
import com.aicareercoach.mobile.data.SampleData
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.components.Tag
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.BluePrimary
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary

@Composable
fun ResourceDetailScreen(
    resource: CareerResource,
    onBack: () -> Unit = {},
    onAskCoach: () -> Unit = {}
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
    ) {
        AppTopBar(title = "Resource", onBack = onBack, showProfile = false)
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(bottom = 24.dp)
        ) {
            SectionCard {
                Tag(resource.category, BluePrimary)
                Spacer(Modifier.height(12.dp))
                Text(resource.title, style = MaterialTheme.typography.headlineMedium)
                Spacer(Modifier.height(10.dp))
                Text(resource.summary, style = MaterialTheme.typography.bodyLarge, color = TextSecondary)
            }
            Spacer(Modifier.height(16.dp))
            SectionCard {
                Text("How the coach uses this", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(8.dp))
                Text(
                    "When you ask a related question, this page is one of the knowledge-base sources the RAG pipeline can retrieve.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary
                )
            }
            Spacer(Modifier.height(24.dp))
            PrimaryButton(text = "Ask the coach about this", onClick = onAskCoach)
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun ResourceDetailScreenPreview() {
    AICareerCoachTheme {
        ResourceDetailScreen(SampleData.resources.first())
    }
}
