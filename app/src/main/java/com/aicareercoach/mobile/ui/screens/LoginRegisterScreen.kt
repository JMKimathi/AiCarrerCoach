package com.aicareercoach.mobile.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.ui.components.AppTextField
import com.aicareercoach.mobile.ui.components.PrimaryButton
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme
import com.aicareercoach.mobile.ui.theme.TextSecondary

@Composable
fun LoginRegisterScreen(
    startInRegister: Boolean = false,
    onAuthenticated: (isAdmin: Boolean) -> Unit = {},
    onBack: () -> Unit = {}
) {
    var isLoginMode by remember(startInRegister) { mutableStateOf(!startInRegister) }
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    fun submit(asAdmin: Boolean) {
        if (email.isBlank() || password.isBlank() || (!isLoginMode && name.isBlank())) {
            error = "Please fill in all required fields."
            return
        }
        error = null
        onAuthenticated(asAdmin)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 28.dp)
    ) {
        Spacer(Modifier.height(12.dp))
        IconButton(onClick = onBack, modifier = Modifier.offset(x = (-12).dp)) {
            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
        }

        Text(
            if (isLoginMode) "Welcome back" else "Create your account",
            style = MaterialTheme.typography.headlineLarge
        )
        Spacer(Modifier.height(6.dp))
        Text(
            if (isLoginMode) "Log in to continue your career coaching journey."
            else "Sign up to get personalized, AI-powered career guidance.",
            style = MaterialTheme.typography.bodyMedium,
            color = TextSecondary
        )

        Spacer(Modifier.height(28.dp))

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .padding(4.dp)
        ) {
            ModeTab("Log In", isLoginMode, Modifier.weight(1f)) {
                isLoginMode = true
                error = null
            }
            ModeTab("Register", !isLoginMode, Modifier.weight(1f)) {
                isLoginMode = false
                error = null
            }
        }

        Spacer(Modifier.height(24.dp))

        if (!isLoginMode) {
            AppTextField(label = "Full Name", value = name, onValueChange = { name = it })
            Spacer(Modifier.height(14.dp))
        }
        AppTextField(label = "Email Address", value = email, onValueChange = { email = it })
        Spacer(Modifier.height(14.dp))
        AppTextField(label = "Password", value = password, onValueChange = { password = it }, isPassword = true)

        if (isLoginMode) {
            Spacer(Modifier.height(10.dp))
            Text(
                "Forgot password?",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.align(Alignment.End)
            )
        }

        if (error != null) {
            Spacer(Modifier.height(12.dp))
            Text(error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(24.dp))

        PrimaryButton(
            text = if (isLoginMode) "Log In" else "Create Account",
            onClick = { submit(asAdmin = false) }
        )

        if (isLoginMode) {
            Spacer(Modifier.height(8.dp))
            TextButton(
                onClick = { submit(asAdmin = true) },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Sign in as administrator")
            }
        }

        Spacer(Modifier.height(12.dp))

        Text(
            "By continuing, you agree to our Terms of Service and Privacy Policy.",
            style = MaterialTheme.typography.bodySmall,
            color = TextSecondary,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(24.dp))
    }
}

@Composable
private fun ModeTab(label: String, selected: Boolean, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val bg = if (selected) Color.White else Color.Transparent
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(10.dp))
            .background(bg)
            .clickable(onClick = onClick)
            .padding(vertical = 10.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            label,
            style = MaterialTheme.typography.titleMedium,
            color = if (selected) MaterialTheme.colorScheme.primary else TextSecondary
        )
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 780)
@Composable
private fun LoginRegisterScreenPreview() {
    AICareerCoachTheme {
        LoginRegisterScreen()
    }
}
