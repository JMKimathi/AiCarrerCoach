package com.aicareercoach.mobile.ui.screens.student

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.UserSession
import com.aicareercoach.mobile.ui.components.AppTextField
import com.aicareercoach.mobile.ui.components.AppTopBar
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.SurfaceAlt
import com.aicareercoach.mobile.data.network.ApiClient
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import kotlinx.coroutines.launch

@Composable
fun EditProfileScreen(
    session: UserSession,
    onBack: () -> Unit = {},
    onSave: (UserSession) -> Unit = {}
) {
    var name by remember { mutableStateOf(session.name) }
    var course by remember { mutableStateOf(session.course) }
    var goal by remember { mutableStateOf(session.careerGoal) }
    var error by remember { mutableStateOf<String?>(null) }
    var saving by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SurfaceAlt)
    ) {
        AppTopBar(title = "Edit profile", onBack = onBack, showProfile = false)
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
        ) {
            AppTextField(label = "Full name", value = name, onValueChange = { name = it })
            Spacer(Modifier.height(14.dp))
            AppTextField(label = "Course", value = course, onValueChange = { course = it })
            Spacer(Modifier.height(14.dp))
            AppTextField(label = "Career goal", value = goal, onValueChange = { goal = it })
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Spacer(Modifier.height(24.dp))
            PrimaryButton(text = if (saving) "Saving…" else "Save changes", enabled = !saving) {
                if (name.trim().length < 2) {
                    error = "Enter a name with at least 2 characters."
                } else {
                    saving = true
                    scope.launch {
                        val saved = ApiClient.updateProfile(session, name, course, goal)
                        saving = false
                        if (saved != null) onSave(saved) else error = "Your profile was not saved. Check the backend connection and try again."
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun EditProfileScreenPreview() {
    AICareerCoachTheme {
        EditProfileScreen(UserSession("John Mwiti", "john.mwiti@strathmore.edu"))
    }
}
