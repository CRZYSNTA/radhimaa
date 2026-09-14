package com.example.jarviscompanion.ui.main

import android.annotation.SuppressLint
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.navigation3.runtime.NavKey

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun MainScreen(
  onItemClick: (NavKey) -> Unit,
  modifier: Modifier = Modifier,
) {
  var serverHost by remember { mutableStateOf("192.168.1.4:8000") }
  var inputHost by remember { mutableStateOf("192.168.1.4:8000") }
  var showSettings by remember { mutableStateOf(false) }
  var webViewRef by remember { mutableStateOf<WebView?>(null) }

  Column(
    modifier = modifier
      .fillMaxSize()
      .background(Color(0xFF040810))
  ) {
    if (showSettings) {
      Card(
        modifier = Modifier
          .fillMaxWidth()
          .padding(8.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0A1324))
      ) {
        Column(modifier = Modifier.padding(12.dp)) {
          Text(
            text = "JARVIS HOST CONFIGURATION",
            color = Color(0xFF00D2FF),
            fontSize = 12.sp,
            letterSpacing = 1.sp
          )
          Spacer(modifier = Modifier.height(6.dp))
          OutlinedTextField(
            value = inputHost,
            onValueChange = { inputHost = it },
            label = { Text("PC IP Address:Port", color = Color(0xFF88A4C4)) },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
              focusedTextColor = Color.White,
              unfocusedTextColor = Color.White,
              focusedBorderColor = Color(0xFF00D2FF),
              unfocusedBorderColor = Color(0xFF2A4365)
            )
          )
          Spacer(modifier = Modifier.height(8.dp))
          Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
          ) {
            Button(
              onClick = {
                serverHost = inputHost.trim()
                showSettings = false
                webViewRef?.loadUrl("http://$serverHost/app")
              },
              colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF00D2FF)),
              modifier = Modifier.weight(1f)
            ) {
              Text("Connect", color = Color.Black)
            }
            OutlinedButton(
              onClick = {
                inputHost = "100.125.111.70:8000"
                serverHost = "100.125.111.70:8000"
                showSettings = false
                webViewRef?.loadUrl("http://$serverHost/app")
              },
              modifier = Modifier.weight(1f)
            ) {
              Text("Tailscale", color = Color(0xFF00D2FF))
            }
          }
        }
      }
    }

    Box(modifier = Modifier.weight(1f)) {
      AndroidView(
        modifier = Modifier.fillMaxSize(),
        factory = { context ->
          WebView(context).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.databaseEnabled = true
            settings.mediaPlaybackRequiresUserGesture = false
            settings.cacheMode = WebSettings.LOAD_DEFAULT

            webViewClient = WebViewClient()
            webChromeClient = object : WebChromeClient() {
              override fun onPermissionRequest(request: PermissionRequest?) {
                request?.grant(request.resources)
              }
            }

            loadUrl("http://$serverHost/app")
            webViewRef = this
          }
        },
        update = { webView ->
          webViewRef = webView
        }
      )
    }
  }
}
