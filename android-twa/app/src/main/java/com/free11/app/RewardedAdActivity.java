package com.free11.app;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import com.google.android.gms.ads.AdError;
import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.FullScreenContentCallback;
import com.google.android.gms.ads.LoadAdError;
import com.google.android.gms.ads.MobileAds;
import com.google.android.gms.ads.OnUserEarnedRewardListener;
import com.google.android.gms.ads.rewarded.RewardItem;
import com.google.android.gms.ads.rewarded.RewardedAd;
import com.google.android.gms.ads.rewarded.RewardedAdLoadCallback;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import java.io.IOException;

/**
 * FREE11 AdMob Rewarded Ad Activity
 *
 * Flow:
 * 1. Web button opens intent: free11://rewarded-ad?token=<jwt>
 * 2. This activity loads and shows the rewarded ad
 * 3. On reward earned → calls POST /api/v2/ads/reward with JWT
 * 4. On completion → opens https://free11.com/watch-earn?admob_complete=1
 * 5. On failure/dismiss → opens https://free11.com/watch-earn?admob_failed=1
 */
public class RewardedAdActivity extends AppCompatActivity {

    private static final String TAG = "FREE11_AdMob";
    private static final String AD_UNIT_ID = "ca-app-pub-9797748350990489/8149671186";
    private static final String RETURN_URL_BASE = "https://free11.com/watch-earn";
    private static final String BACKEND_URL = "https://free11.com/api/v2/ads/reward";

    private RewardedAd rewardedAd;
    private String authToken;
    private boolean rewardEarned = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Extract JWT token from intent data
        Uri intentData = getIntent().getData();
        if (intentData != null) {
            authToken = intentData.getQueryParameter("token");
        }

        // Initialize MobileAds SDK
        MobileAds.initialize(this, initializationStatus ->
            Log.d(TAG, "AdMob SDK initialized")
        );

        loadRewardedAd();
    }

    private void loadRewardedAd() {
        AdRequest adRequest = new AdRequest.Builder().build();

        RewardedAd.load(this, AD_UNIT_ID, adRequest, new RewardedAdLoadCallback() {
            @Override
            public void onAdLoaded(@NonNull RewardedAd ad) {
                Log.d(TAG, "Ad loaded successfully");
                rewardedAd = ad;
                setupCallbacks();
                showAd();
            }

            @Override
            public void onAdFailedToLoad(@NonNull LoadAdError loadAdError) {
                Log.e(TAG, "Ad failed to load: " + loadAdError.getMessage());
                Toast.makeText(RewardedAdActivity.this,
                    "Ad not available right now. Try again later.", Toast.LENGTH_SHORT).show();
                returnToApp(false);
            }
        });
    }

    private void setupCallbacks() {
        rewardedAd.setFullScreenContentCallback(new FullScreenContentCallback() {
            @Override
            public void onAdDismissedFullScreenContent() {
                Log.d(TAG, "Ad dismissed");
                returnToApp(rewardEarned);
            }

            @Override
            public void onAdFailedToShowFullScreenContent(@NonNull AdError adError) {
                Log.e(TAG, "Ad failed to show: " + adError.getMessage());
                returnToApp(false);
            }

            @Override
            public void onAdShowedFullScreenContent() {
                Log.d(TAG, "Ad shown");
            }
        });
    }

    private void showAd() {
        rewardedAd.show(this, new OnUserEarnedRewardListener() {
            @Override
            public void onUserEarnedReward(@NonNull RewardItem rewardItem) {
                Log.d(TAG, "User earned reward: " + rewardItem.getAmount() + " " + rewardItem.getType());
                rewardEarned = true;
                // Call backend to credit coins if we have a token
                if (authToken != null && !authToken.isEmpty()) {
                    callRewardBackend(authToken);
                }
            }
        });
    }

    private void callRewardBackend(String token) {
        OkHttpClient client = new OkHttpClient();
        MediaType JSON = MediaType.get("application/json; charset=utf-8");
        RequestBody body = RequestBody.create("{\"reward_type\":\"ad_watch\"}", JSON);

        Request request = new Request.Builder()
            .url(BACKEND_URL)
            .post(body)
            .addHeader("Authorization", "Bearer " + token)
            .addHeader("Content-Type", "application/json")
            .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                Log.e(TAG, "Backend reward call failed: " + e.getMessage());
                // Still return success — ad was watched. Web page will retry/refresh.
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) {
                Log.d(TAG, "Reward API response: " + response.code());
                response.close();
            }
        });
    }

    private void returnToApp(boolean success) {
        String returnUrl = RETURN_URL_BASE + (success ? "?admob_complete=1" : "?admob_failed=1");
        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(returnUrl));
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(intent);
        finish();
    }
}
