package com.caliof.tradingsignals;

import java.net.URI;

/** Navigation stays on the app's HTTPS origin. No native JavaScript bridge is exposed. */
public final class OriginPolicy {
    public static final String HOME = "https://signals-app-production-ba26.up.railway.app/";
    private static final String HOST = "signals-app-production-ba26.up.railway.app";

    public static boolean isAppUrl(String value) {
        if (value == null) return false;
        try {
            URI uri = new URI(value);
            return "https".equalsIgnoreCase(uri.getScheme())
                    && HOST.equalsIgnoreCase(uri.getHost())
                    && uri.getRawUserInfo() == null
                    && (uri.getPort() == -1 || uri.getPort() == 443);
        } catch (Exception invalid) {
            return false;
        }
    }

    public static String launchUrl(String value) {
        return isAppUrl(value) ? value : HOME;
    }
}
