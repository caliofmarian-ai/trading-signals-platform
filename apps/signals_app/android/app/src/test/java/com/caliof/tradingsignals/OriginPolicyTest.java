package com.caliof.tradingsignals;

import org.junit.Test;
import static org.junit.Assert.*;

public class OriginPolicyTest {
    @Test public void appLinksKeepTheirPathAndFragment() {
        String link = OriginPolicy.HOME+"#account";
        assertEquals(link,OriginPolicy.launchUrl(link));
        assertTrue(OriginPolicy.isAppUrl(OriginPolicy.HOME+"api/session"));
    }
    @Test public void externalAndMalformedLaunchesGoHome() {
        for (String url : new String[]{null,"","https://evil.invalid/", "not a URL"}) {
            assertEquals(OriginPolicy.HOME,OriginPolicy.launchUrl(url));
        }
    }
    @Test public void hostileSchemesCannotReachNativeHost() {
        for (String url : new String[]{"javascript:alert(1)","file:///data/private", "intent://launch", "content://app/private", "http://signals-app-production-ba26.up.railway.app/"}) {
            assertFalse(OriginPolicy.isAppUrl(url));
        }
    }
    @Test public void hostSpoofingAndCredentialsAreRejected() {
        assertFalse(OriginPolicy.isAppUrl("https://signals-app-production-ba26.up.railway.app.evil.invalid/"));
        assertFalse(OriginPolicy.isAppUrl("https://signals-app-production-ba26.up.railway.app@evil.invalid/"));
        assertFalse(OriginPolicy.isAppUrl("https://name:password@signals-app-production-ba26.up.railway.app/"));
        assertFalse(OriginPolicy.isAppUrl("https://signals-app-production-ba26.up.railway.app:444/"));
        assertTrue(OriginPolicy.isAppUrl("https://signals-app-production-ba26.up.railway.app:443/"));
    }
}
