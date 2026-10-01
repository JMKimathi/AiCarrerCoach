package com.aicareercoach.mobile.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.StudentAccount
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.SectionCard
import com.aicareercoach.mobile.ui.components.Tag
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.BluePrimary
import com.aicareercoach.mobile.ui.theme.SuccessGreen
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.ui.theme.TextSecondary
import com.aicareercoach.mobile.ui.theme.WarningAmber

@Composable
fun AdminUsersScreen(
    students: List<StudentAccount> = emptyList()
) {
    Column(modifier = Modifier.fillMaxSize().background(SurfaceAlt)) {
        AppTopBar(title = "Students", subtitle = "${students.size} accounts on the platform", showProfile = false)
        LazyColumn(
            modifier = Modifier.padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(bottom = 24.dp)
        ) {
            if (students.isEmpty()) item {
                Text("No student accounts were returned. Check your connection or register a student account.", color = TextSecondary)
            }
            items(students, key = { it.email }) { student ->
                SectionCard {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        androidx.compose.material3.Icon(
                            Icons.Default.Person,
                            contentDescription = null,
                            tint = BluePrimary
                        )
                        Spacer(Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(student.name, style = MaterialTheme.typography.titleMedium)
                            Text(student.email, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                            Text(student.course, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                        }
                        Tag(
                            student.status,
                            if (student.status == "Active") SuccessGreen else WarningAmber
                        )
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun AdminUsersScreenPreview() {
    AICareerCoachTheme { AdminUsersScreen() }
}
