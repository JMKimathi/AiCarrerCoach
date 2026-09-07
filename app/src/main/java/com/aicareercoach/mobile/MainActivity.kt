package com.aicareercoach.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.aicareercoach.mobile.ui.navigation.AppNavigation
import com.aicareercoach.mobile.ui.theme.AICareerCoachTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AICareerCoachTheme(darkTheme = false) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AppNavigation(modifier = Modifier.safeDrawingPadding())
                }
            }
        }
    }
}
