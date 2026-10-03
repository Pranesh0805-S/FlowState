package com.pranesh.flowstate;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Small client for the same authenticated API used by Flowstate Web. */
final class ApiClient {
    private static final String BASE_URL = "https://flowstate-pranesh0805.vercel.app/api/";
    private static final String SESSION_COOKIE = "flowstate_session";
    private final SharedPreferences preferences;

    ApiClient(Context context) {
        preferences = context.getSharedPreferences("flowstate_session", Context.MODE_PRIVATE);
    }

    boolean hasSession() {
        return preferences.contains(SESSION_COOKIE);
    }

    void clearSession() {
        preferences.edit().remove(SESSION_COOKIE).apply();
    }

    JSONObject request(String method, String path, JSONObject body) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(BASE_URL + path).openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(30000);
        connection.setReadTimeout(120000); // the API host may be waking from its free-tier sleep.
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");

        String session = preferences.getString(SESSION_COOKIE, null);
        if (session != null && !session.isEmpty()) {
            connection.setRequestProperty("Cookie", SESSION_COOKIE + "=" + session);
        }

        if (body != null) {
            connection.setDoOutput(true);
            byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(bytes);
            }
        }

        int status = connection.getResponseCode();
        saveSessionFromResponse(connection);
        if (status == HttpURLConnection.HTTP_NO_CONTENT) {
            connection.disconnect();
            return new JSONObject();
        }
        InputStream stream = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
        String responseText = readAll(stream);
        connection.disconnect();

        JSONObject response;
        try {
            response = new JSONObject(responseText);
        } catch (Exception parseError) {
            throw new Exception("Flowstate returned an unreadable response (HTTP " + status + ").");
        }
        if (status < 200 || status >= 300) {
            String message = response.optString("detail", response.optString("message", "Request failed."));
            throw new ApiException(message, status);
        }
        return response;
    }

    private void saveSessionFromResponse(HttpURLConnection connection) {
        for (int i = 1; ; i++) {
            String header = connection.getHeaderFieldKey(i);
            if (header == null && connection.getHeaderField(i) == null) break;
            if (header == null || !header.equalsIgnoreCase("Set-Cookie")) continue;
            String value = connection.getHeaderField(i);
            if (value == null || !value.startsWith(SESSION_COOKIE + "=")) continue;
            String cookieValue = value.substring((SESSION_COOKIE + "=").length()).split(";", 2)[0];
            if (cookieValue.isEmpty()) clearSession();
            else preferences.edit().putString(SESSION_COOKIE, cookieValue).apply();
        }
    }

    private static String readAll(InputStream stream) throws Exception {
        if (stream == null) return "{}";
        StringBuilder result = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) result.append(line);
        }
        return result.toString();
    }

    static JSONObject json(Object... values) throws Exception {
        JSONObject result = new JSONObject();
        for (int i = 0; i + 1 < values.length; i += 2) {
            result.put(String.valueOf(values[i]), values[i + 1]);
        }
        return result;
    }

    static final class ApiException extends Exception {
        final int status;
        ApiException(String message, int status) {
            super(message);
            this.status = status;
        }
    }
}
