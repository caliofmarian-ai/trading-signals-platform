package com.caliof.tradingsignals;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.CookieManager;
import android.webkit.RenderProcessGoneDetail;
import android.webkit.SslErrorHandler;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

/** Persistent Android host: an unavailable browser/network never silently closes the app. */
public class MainActivity extends Activity {
    private static final int BACKGROUND = Color.rgb(16,24,23);
    private static final int TEXT = Color.rgb(237,242,237);
    private static final String STATE = "signals.web.state";
    private WebView web;
    private LinearLayout root;
    private FrameLayout content;
    private LinearLayout errorPanel;
    private TextView errorText;
    private ProgressBar progress;
    private boolean failed;
    private String destination = OriginPolicy.HOME;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        destination = OriginPolicy.launchUrl(getIntent().getDataString());
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BACKGROUND);
        root.setOnApplyWindowInsetsListener((view,insets) -> {
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                view.setPadding(bars.left,bars.top,bars.right,bars.bottom);
            } else {
                view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),
                        insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        progress = new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        root.addView(progress,new LinearLayout.LayoutParams(-1,dp(3)));
        content = new FrameLayout(this);
        root.addView(content,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);
        makeErrorPanel();
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,this::navigateBack);
        }
        if (createWebView()) {
            Bundle saved = state == null ? null : state.getBundle(STATE);
            if (saved == null || web.restoreState(saved) == null) web.loadUrl(destination);
        }
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    private void makeErrorPanel() {
        errorPanel = new LinearLayout(this);
        errorPanel.setOrientation(LinearLayout.VERTICAL);
        errorPanel.setPadding(dp(28),dp(44),dp(28),dp(28));
        errorPanel.setBackgroundColor(BACKGROUND);
        TextView title = new TextView(this);
        title.setText("Trading Signals"); title.setTextColor(TEXT); title.setTextSize(26);
        errorPanel.addView(title);
        errorText = new TextView(this);
        errorText.setTextColor(TEXT); errorText.setTextSize(16); errorText.setPadding(0,dp(24),0,dp(24));
        errorPanel.addView(errorText);
        Button retry = new Button(this); retry.setText("Try again"); retry.setOnClickListener(v -> retryLoad());
        errorPanel.addView(retry,new LinearLayout.LayoutParams(-1,dp(54)));
        Button browser = new Button(this); browser.setText("Open website in browser");
        browser.setOnClickListener(v -> openWebsite());
        errorPanel.addView(browser,new LinearLayout.LayoutParams(-1,dp(54)));
        content.addView(errorPanel,new FrameLayout.LayoutParams(-1,-1));
        errorPanel.setVisibility(View.GONE);
    }

    WebView newWebView() { return new WebView(this); }

    private boolean createWebView() {
        try {
            WebView candidate = newWebView();
            WebSettings settings = candidate.getSettings();
            settings.setJavaScriptEnabled(true);
            settings.setDomStorageEnabled(true);
            settings.setAllowFileAccess(false);
            settings.setAllowContentAccess(false);
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
            settings.setJavaScriptCanOpenWindowsAutomatically(false);
            settings.setSupportMultipleWindows(false);
            settings.setGeolocationEnabled(false);
            settings.setMediaPlaybackRequiresUserGesture(true);
            settings.setUserAgentString(settings.getUserAgentString()+" TradingSignalsAndroid/0.1.1");
            CookieManager.getInstance().setAcceptCookie(true);
            CookieManager.getInstance().setAcceptThirdPartyCookies(candidate,false);
            candidate.setBackgroundColor(BACKGROUND);
            candidate.setWebViewClient(new AppClient());
            candidate.setWebChromeClient(new WebChromeClient() {
                @Override public void onProgressChanged(WebView view,int value) {
                    progress.setProgress(value);
                    progress.setVisibility(!failed && value<100 ? View.VISIBLE : View.GONE);
                }
            });
            web = candidate;
            content.addView(web,0,new FrameLayout.LayoutParams(-1,-1));
            return true;
        } catch (RuntimeException unavailable) {
            showError("Android could not open its web component. Enable or update Android System WebView, or open the website in your browser.");
            return false;
        }
    }

    private void showError(String message) {
        failed = true;
        progress.setVisibility(View.GONE);
        errorText.setText(message);
        errorPanel.setVisibility(View.VISIBLE);
        errorPanel.bringToFront();
    }

    private void retryLoad() {
        failed = false;
        errorPanel.setVisibility(View.GONE);
        progress.setVisibility(View.VISIBLE);
        if (web != null || createWebView()) web.loadUrl(destination);
    }

    private void openWebsite() {
        String browser = browserPackage();
        if (browser == null) {
            Toast.makeText(this,"Enable a browser to open the website.",Toast.LENGTH_LONG).show();
            return;
        }
        try { startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(OriginPolicy.HOME)).setPackage(browser)); }
        catch (ActivityNotFoundException unavailable) {
            Toast.makeText(this,"Enable a browser to open the website.",Toast.LENGTH_LONG).show();
        }
    }

    private String browserPackage() {
        Intent generic = new Intent(Intent.ACTION_VIEW,Uri.parse("https://www.example.com/"));
        android.content.pm.ResolveInfo handler = getPackageManager().resolveActivity(generic,android.content.pm.PackageManager.MATCH_DEFAULT_ONLY);
        return handler != null && handler.activityInfo != null && !getPackageName().equals(handler.activityInfo.packageName)
            ? handler.activityInfo.packageName : null;
    }

    private boolean navigate(String url) {
        if (OriginPolicy.isAppUrl(url)) return false;
        // Browser-escaping navigation must be an explicit user gesture; no intent://, file:// or JavaScript bridge.
        Toast.makeText(this,"This link is outside the application.",Toast.LENGTH_SHORT).show();
        return true;
    }

    private class AppClient extends WebViewClient {
        @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request) {
            return navigate(request.getUrl().toString());
        }
        @Override public boolean shouldOverrideUrlLoading(WebView view,String url) { return navigate(url); }
        @Override public void onPageStarted(WebView view,String url,android.graphics.Bitmap icon) {
            if (!OriginPolicy.isAppUrl(url)) { view.stopLoading(); showError("Navigation outside the secure application was blocked."); return; }
            destination = url;
            failed = false; errorPanel.setVisibility(View.GONE); progress.setVisibility(View.VISIBLE);
        }
        @Override public void onPageFinished(WebView view,String url) {
            progress.setVisibility(View.GONE);
            if (!failed) errorPanel.setVisibility(View.GONE);
            CookieManager.getInstance().flush();
        }
        @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError error) {
            if (request.isForMainFrame()) showError("The application could not connect. Check your connection and try again.");
        }
        @Override public void onReceivedHttpError(WebView view,WebResourceRequest request,WebResourceResponse error) {
            if (request.isForMainFrame()) showError("The server could not load the application. Please try again.");
        }
        @Override public void onReceivedSslError(WebView view,SslErrorHandler handler,SslError error) {
            handler.cancel();
            showError("A secure connection could not be established. Please try again later.");
        }
        @Override public boolean onRenderProcessGone(WebView view,RenderProcessGoneDetail detail) {
            content.removeView(view); view.destroy(); web = null;
            showError("The Android web component stopped. Tap Try again to reopen the application.");
            return true;
        }
    }

    private void navigateBack() {
        if (web != null && web.canGoBack()) web.goBack(); else moveTaskToBack(true);
    }
    @Override public void onBackPressed() { navigateBack(); }
    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent); setIntent(intent);
        String url = intent.getDataString();
        if (OriginPolicy.isAppUrl(url)) { destination = url; retryLoad(); }
    }
    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        if (web != null) { Bundle webState = new Bundle(); web.saveState(webState); state.putBundle(STATE,webState); }
    }
    @Override protected void onPause() {
        super.onPause(); if (web != null) { web.onPause(); CookieManager.getInstance().flush(); }
    }
    @Override protected void onResume() { super.onResume(); if (web != null) web.onResume(); }
    @Override protected void onDestroy() {
        if (web != null) { content.removeView(web); web.destroy(); web = null; }
        super.onDestroy();
    }
}
