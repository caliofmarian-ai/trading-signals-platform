package com.caliof.tradingsignals;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.Button;
import android.widget.LinearLayout;
import java.lang.reflect.Field;
import java.util.Collections;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.Shadows;
import org.robolectric.annotation.Config;
import org.robolectric.android.controller.ActivityController;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28)
public class MainActivityTest {
    public static class MissingWebViewActivity extends MainActivity {
        @Override WebView newWebView() { throw new IllegalStateException("WebView provider unavailable"); }
    }
    @SuppressWarnings("unchecked") private <T> T field(MainActivity a,String name) throws Exception {
        Field f=MainActivity.class.getDeclaredField(name); f.setAccessible(true); return (T)f.get(a);
    }
    private WebResourceRequest request(boolean main) {
        return new WebResourceRequest() {
            public Uri getUrl(){ return Uri.parse(OriginPolicy.HOME); }
            public boolean isForMainFrame(){ return main; }
            public boolean isRedirect(){ return false; }
            public boolean hasGesture(){ return false; }
            public String getMethod(){ return "GET"; }
            public Map<String,String> getRequestHeaders(){ return Collections.emptyMap(); }
        };
    }
    @Test @Config(sdk={28,33,36})
    public void coldStartKeepsAnActualAppWindowWithoutAnyBrowser() throws Exception {
        try(ActivityController<MainActivity> c=Robolectric.buildActivity(MainActivity.class).setup()) {
            MainActivity a=c.get(); WebView web=field(a,"web");
            assertNotNull(web); assertFalse(a.isFinishing());
            assertEquals(OriginPolicy.HOME,Shadows.shadowOf(web).getLastLoadedUrl());
            assertNull(Shadows.shadowOf(a).getNextStartedActivity());
        }
    }
    @Test public void mainFrameNetworkFailureShowsRetryAndKeepsActivity() throws Exception {
        try(ActivityController<MainActivity> c=Robolectric.buildActivity(MainActivity.class).setup()) {
            MainActivity a=c.get(); WebView web=field(a,"web");
            web.getWebViewClient().onReceivedError(web,request(true),null);
            LinearLayout error=field(a,"errorPanel");
            assertEquals(View.VISIBLE,error.getVisibility()); assertFalse(a.isFinishing());
            Button retry=(Button)error.getChildAt(2); retry.performClick();
            assertEquals(View.GONE,error.getVisibility());
            assertEquals(OriginPolicy.HOME,Shadows.shadowOf(web).getLastLoadedUrl());
        }
    }
    @Test public void missingWebComponentShowsRecoveryInsteadOfClosing() throws Exception {
        try(ActivityController<MissingWebViewActivity> c=Robolectric.buildActivity(MissingWebViewActivity.class).setup()) {
            MainActivity a=c.get();
            assertNull(field(a,"web"));
            LinearLayout error=field(a,"errorPanel");
            assertEquals(View.VISIBLE,error.getVisibility());
            assertFalse(a.isFinishing());
            ((Button)error.getChildAt(2)).performClick();
            assertEquals(View.VISIBLE,error.getVisibility());
            assertFalse(a.isFinishing());
        }
    }
    @Test public void rendererCrashCanBeRecoveredWithoutClosingTheApp() throws Exception {
        try(ActivityController<MainActivity> c=Robolectric.buildActivity(MainActivity.class).setup()) {
            MainActivity a=c.get(); WebView previous=field(a,"web");
            assertTrue(previous.getWebViewClient().onRenderProcessGone(previous,null));
            assertNull(field(a,"web"));
            LinearLayout error=field(a,"errorPanel");
            assertEquals(View.VISIBLE,error.getVisibility());
            ((Button)error.getChildAt(2)).performClick();
            WebView replacement=field(a,"web");
            assertNotNull(replacement); assertNotSame(previous,replacement);
            assertEquals(OriginPolicy.HOME,Shadows.shadowOf(replacement).getLastLoadedUrl());
            assertFalse(a.isFinishing());
        }
    }
    @Test public void aFailedSubresourceDoesNotHideTheWholeApplication() throws Exception {
        try(ActivityController<MainActivity> c=Robolectric.buildActivity(MainActivity.class).setup()) {
            MainActivity a=c.get(); WebView web=field(a,"web");
            web.getWebViewClient().onReceivedError(web,request(false),null);
            assertEquals(View.GONE,((View)field(a,"errorPanel")).getVisibility());
        }
    }
    @Test public void serverFailureIsVisibleAndDoesNotExit() throws Exception {
        try(ActivityController<MainActivity> c=Robolectric.buildActivity(MainActivity.class).setup()) {
            MainActivity a=c.get(); WebView web=field(a,"web");
            WebResourceResponse failure=new WebResourceResponse("text/plain","UTF-8",503,"Unavailable",Collections.emptyMap(),null);
            web.getWebViewClient().onReceivedHttpError(web,request(true),failure);
            assertEquals(View.VISIBLE,((View)field(a,"errorPanel")).getVisibility());
            assertFalse(a.isFinishing());
        }
    }
    @Test public void externalDeepLinksCannotNavigateToAnUntrustedOrigin() throws Exception {
        Intent intent=new Intent(Intent.ACTION_VIEW,Uri.parse("https://evil.invalid/#claim=untrusted"));
        try(ActivityController<MainActivity> c=Robolectric.buildActivity(MainActivity.class,intent).setup()) {
            assertEquals(OriginPolicy.HOME,Shadows.shadowOf((WebView)field(c.get(),"web")).getLastLoadedUrl());
        }
    }
    @Test public void normalDeepLinksRemainInsideTheApp() throws Exception {
        String url=OriginPolicy.HOME+"#account";
        Intent intent=new Intent(Intent.ACTION_VIEW,Uri.parse(url));
        try(ActivityController<MainActivity> c=Robolectric.buildActivity(MainActivity.class,intent).setup()) {
            assertEquals(url,Shadows.shadowOf((WebView)field(c.get(),"web")).getLastLoadedUrl());
            assertFalse(c.get().isFinishing());
        }
    }
    @Test public void webComponentDoesNotPermitFileContentOrMixedContentAccess() throws Exception {
        try(ActivityController<MainActivity> c=Robolectric.buildActivity(MainActivity.class).setup()) {
            WebView web=field(c.get(),"web"); WebSettings settings=web.getSettings();
            assertFalse(settings.getAllowFileAccess()); assertFalse(settings.getAllowContentAccess());
            assertEquals(WebSettings.MIXED_CONTENT_NEVER_ALLOW,settings.getMixedContentMode());
            assertTrue(settings.getDomStorageEnabled());
            assertTrue(settings.getUserAgentString().contains("TradingSignalsAndroid/0.1.1"));
        }
    }
    @Test public void recreationDoesNotFinishTheApplicationWindow() throws Exception {
        ActivityController<MainActivity> first=Robolectric.buildActivity(MainActivity.class).setup();
        Bundle state=new Bundle(); first.saveInstanceState(state).pause().stop().destroy();
        try(ActivityController<MainActivity> second=Robolectric.buildActivity(MainActivity.class).create(state).start().resume().visible()) {
            assertNotNull(field(second.get(),"web")); assertFalse(second.get().isFinishing());
        }
    }
}
