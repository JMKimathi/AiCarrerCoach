package com.aicareercoach.mobile.ui.screens.shared

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.aicareercoach.mobile.data.network.ApiClient
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BackendConnectionScreen(onBack: () -> Unit) {
    val savedEndpoints = remember { ApiClient.configuredEndpoints() }
    var wifiAddress by remember { mutableStateOf(savedEndpoints.getOrNull(0).orEmpty().ifBlank { "http://192.168.100.3:8000/api" }) }
    var hotspotAddress by remember { mutableStateOf(savedEndpoints.getOrNull(1).orEmpty()) }
    var status by remember { mutableStateOf("The home Wi-Fi address is prefilled. Add the laptop's hotspot address when it is connected to your phone hotspot.") }
    var checking by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    fun save() {
        ApiClient.saveEndpoints(listOf(wifiAddress, hotspotAddress))
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Backend connection") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Text(
                "Save the laptop's local backend address while it is connected to each network. " +
                    "When the phone changes networks, the app checks the saved addresses and switches to a responding API.",
                style = MaterialTheme.typography.bodyMedium
            )
            OutlinedTextField(
                value = wifiAddress,
                onValueChange = { wifiAddress = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Home / school Wi-Fi laptop address") },
                placeholder = { Text("http://192.168.1.20:8000/api") },
                singleLine = true
            )
            OutlinedTextField(
                value = hotspotAddress,
                onValueChange = { hotspotAddress = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Phone hotspot laptop address") },
                placeholder = { Text("http://192.168.100.20:8000/api") },
                singleLine = true
            )
            Text(
                "Use the laptop's IPv4 address from ipconfig while it is connected to that network. " +
                    "Keep the API running and connect the phone and laptop to the same network.",
                style = MaterialTheme.typography.bodySmall
            )
            Card(modifier = Modifier.fillMaxWidth()) {
                Text(
                    status,
                    modifier = Modifier.padding(14.dp),
                    style = MaterialTheme.typography.bodyMedium
                )
            }
            Button(
                onClick = {
                    save()
                    status = "Saved these addresses. Checking the API health endpoint…"
                    checking = true
                    scope.launch {
                        val endpoints = ApiClient.configuredEndpoints()
                        val results = endpoints.map { endpoint -> endpoint to ApiClient.checkHealth(endpoint) }
                        val reachable = results.firstOrNull { it.second }?.first
                        status = if (reachable != null) {
                            "Connected to $reachable. The app will recheck after the phone changes networks."
                        } else {
                            "No saved address responded. Checked: ${endpoints.joinToString()}. Confirm the laptop IP, firewall, same network, and running API."
                        }
                        checking = false
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = !checking
            ) {
                if (checking) CircularProgressIndicator(modifier = Modifier.height(18.dp), strokeWidth = 2.dp)
                else Text("Save and test connection")
            }
            TextButton(
                onClick = {
                    wifiAddress = "http://192.168.100.3:8000/api"
                    hotspotAddress = ""
                    ApiClient.saveEndpoints(listOf(wifiAddress))
                    status = "Reset to the confirmed home Wi-Fi address. Add your current hotspot address separately."
                },
                modifier = Modifier.fillMaxWidth()
            ) { Text("Reset to confirmed home Wi-Fi address") }
            Spacer(Modifier.height(4.dp))
        }
    }
}
