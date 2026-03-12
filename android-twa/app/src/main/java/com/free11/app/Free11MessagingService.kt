package com.free11.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException

/**
 * FREE11 Firebase Messaging Service
 *
 * Handles:
 * 1. Incoming push notifications (show as system notification)
 * 2. FCM token refresh (register new token with FREE11 backend)
 */
class Free11MessagingService : FirebaseMessagingService() {

    companion object {
        private const val TAG = "FREE11_FCM"
        private const val CHANNEL_ID = "free11_notifications"
        private const val CHANNEL_NAME = "FREE11 Notifications"
        private const val BACKEND_URL = "https://free11.com/api/v2/push/register"
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        Log.d(TAG, "Message received from: ${remoteMessage.from}")

        val title = remoteMessage.notification?.title ?: remoteMessage.data["title"] ?: "FREE11"
        val body = remoteMessage.notification?.body ?: remoteMessage.data["body"] ?: ""
        val deepLink = remoteMessage.data["deep_link"] ?: "https://free11.com"

        Log.d(TAG, "Title: $title | Body: $body")
        showNotification(title, body, deepLink)
    }

    override fun onNewToken(token: String) {
        Log.d(TAG, "New FCM token: ${token.take(20)}...")
        // Save token locally for LaunchActivity to pick up
        val prefs = getSharedPreferences("free11_prefs", Context.MODE_PRIVATE)
        prefs.edit().putString("fcm_token", token).apply()

        // Register with backend if auth token is available
        val authToken = prefs.getString("auth_token", null)
        if (!authToken.isNullOrEmpty()) {
            sendTokenToBackend(token, authToken)
        }
    }

    private fun showNotification(title: String, body: String, deepLink: String) {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // Create notification channel (required for Android 8+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "FREE11 match updates and rewards"
                enableVibration(true)
            }
            notificationManager.createNotificationChannel(channel)
        }

        // Intent to open the app at deep link
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(deepLink)).apply {
            addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_ONE_SHOT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()

        notificationManager.notify(System.currentTimeMillis().toInt(), notification)
    }

    private fun sendTokenToBackend(fcmToken: String, authToken: String) {
        val client = OkHttpClient()
        val json = """{"device_token":"$fcmToken","device_type":"android"}"""
        val body = json.toRequestBody("application/json".toMediaType())

        val request = Request.Builder()
            .url(BACKEND_URL)
            .post(body)
            .addHeader("Authorization", "Bearer $authToken")
            .addHeader("Content-Type", "application/json")
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e(TAG, "Failed to register token: ${e.message}")
            }
            override fun onResponse(call: Call, response: Response) {
                Log.d(TAG, "Token registered: ${response.code}")
                response.close()
            }
        })
    }
}
