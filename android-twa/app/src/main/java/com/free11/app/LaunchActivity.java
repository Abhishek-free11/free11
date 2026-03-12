package com.free11.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import androidx.appcompat.app.AppCompatActivity;
import androidx.browser.customtabs.CustomTabsIntent;
import androidx.browser.trusted.TrustedWebActivityIntentBuilder;
import androidx.core.splashscreen.SplashScreen;

import com.google.firebase.messaging.FirebaseMessaging;

import okhttp3.*;
import okhttp3.MediaType;

import java.io.IOException;

/**
 * FREE11 Trusted Web Activity Launcher
 *
 * This activity launches the FREE11 web app as a TWA, providing:
 * - Full-screen experience (no browser chrome)
 * - Native splash screen with FREE11 branding
 * - PWA install prompt disabled inside the app
 * - URL verification via assetlinks.json
 * - FCM token registration on every launch
 */
public class LaunchActivity extends AppCompatActivity {

    private static final String TAG = "FREE11_Launch";
    private static final String LAUNCH_URL = "https://free11.com";
    private static final String BACKEND_PUSH_URL = "https://free11.com/api/v2/push/register";
    private static final String PREFS_NAME = "free11_prefs";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Handle the splash screen transition (Android 12+)
        SplashScreen splashScreen = SplashScreen.installSplashScreen(this);

        super.onCreate(savedInstanceState);

        // Fetch and register FCM token in background
        refreshFcmToken();

        // Build the TWA intent
        Uri launchUri = Uri.parse(LAUNCH_URL);

        // Check if the intent came from a deep link
        if (getIntent() != null && getIntent().getData() != null) {
            Uri intentUri = getIntent().getData();
            if (intentUri != null && "free11.com".equals(intentUri.getHost())) {
                launchUri = intentUri;
            }
        }

        // Launch as Trusted Web Activity
        new TrustedWebActivityIntentBuilder(launchUri)
                .setColorSchemeParams(
                        CustomTabsIntent.COLOR_SCHEME_DARK,
                        new CustomTabsIntent.ColorSchemeParams.Builder()
                                .setToolbarColor(0xFF0a0e17) // FREE11 dark background
                                .setNavigationBarColor(0xFF0a0e17)
                                .setNavigationBarDividerColor(0xFF1e293b)
                                .build()
                )
                .setDefaultColorSchemeParams(
                        new CustomTabsIntent.ColorSchemeParams.Builder()
                                .setToolbarColor(0xFF0a0e17)
                                .setNavigationBarColor(0xFF0a0e17)
                                .build()
                )
                .build(this)
                .launchActivity(this);

        // Finish this activity so it doesn't appear in back stack
        finish();
    }

    /**
     * Fetch FCM token and register with FREE11 backend.
     * The auth token must have been saved to SharedPreferences by the web app.
     */
    private void refreshFcmToken() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);

        FirebaseMessaging.getInstance().getToken()
            .addOnSuccessListener(token -> {
                if (token == null || token.isEmpty()) return;
                Log.d(TAG, "FCM token: " + token.substring(0, 20) + "...");
                // Save token locally
                prefs.edit().putString("fcm_token", token).apply();

                // Send to backend if logged in
                String authToken = prefs.getString("auth_token", null);
                if (authToken != null && !authToken.isEmpty()) {
                    sendTokenToServer(token, authToken);
                }
            })
            .addOnFailureListener(e -> Log.e(TAG, "FCM token fetch failed: " + e.getMessage()));
    }

    private void sendTokenToServer(String fcmToken, String authToken) {
        OkHttpClient client = new OkHttpClient();
        MediaType json = MediaType.get("application/json; charset=utf-8");
        String payload = "{\"device_token\":\"" + fcmToken + "\",\"device_type\":\"android\"}";
        RequestBody body = RequestBody.create(payload, json);

        Request request = new Request.Builder()
            .url(BACKEND_PUSH_URL)
            .post(body)
            .addHeader("Authorization", "Bearer " + authToken)
            .addHeader("Content-Type", "application/json")
            .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.e(TAG, "Push token registration failed: " + e.getMessage());
            }
            @Override
            public void onResponse(Call call, Response response) {
                Log.d(TAG, "Push token registered: " + response.code());
                response.close();
            }
        });
    }
}
