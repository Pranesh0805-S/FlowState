package com.pranesh.flowstate;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.content.res.ColorStateList;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.view.animation.DecelerateInterpolator;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.ArrayAdapter;
import android.widget.LinearLayout;
import android.widget.NumberPicker;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.DateFormatSymbols;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Native Flowstate workspace. The screen is Android UI; the existing account and data API is reused. */
public class LauncherActivity extends Activity {
    private static final int INK = 0xff182a22;
    private static final int GREEN = 0xff28694f;
    private static final int MUTED = 0xff66746d;
    private static final int BG = 0xfff4f6f1;
    private static final int CARD = 0xffffffff;
    private static final int BORDER = 0xffe4e9e2;
    private static final int BUTTON_HEIGHT = 48;
    private static final int PRIMARY_BUTTON_HEIGHT = 52;
    private static final int FIELD_HEIGHT = 50;
    private static final int FIELD_GAP = 10;
    private static final int LOGO_MARK_SIZE = 36;
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private ApiClient api;
    private LinearLayout root;
    private LinearLayout body;
    private ScrollView contentScroll;
    private JSONObject user;
    private JSONArray tasks = new JSONArray();
    private JSONArray teams = new JSONArray();
    private JSONArray history = new JSONArray();
    private JSONObject metrics = new JSONObject();
    private String page = "home";
    private String dashboardFilter = "upcoming";
    private String authMode = "welcome";
    private int authStage = 1;
    private String selectedDate = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
    private int selectedTeamId = -1;
    private String selectedTeamName = "";
    private String notice = "";
    private boolean noticeError;
    private boolean loading;
    private boolean sessionRestoreFailed;
    private boolean returnedFromBackground;
    private boolean animateNavigation;
    private int welcomeStep;
    private String emailValue = "", passwordValue = "", nameValue = "", otpValue = "";
    private String newPasswordValue = "", confirmPasswordValue = "";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        api = new ApiClient(this);
        Window window = getWindow();
        window.setStatusBarColor(BG);
        window.setNavigationBarColor(BG);
        window.getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        boolean hasSession = api.hasSession();
        loading = hasSession;
        render();
        if (hasSession) {
            call("GET", "auth/me", null, (data, error) -> {
                loading = false;
                if (error != null) {
                    if (error instanceof ApiClient.ApiException && ((ApiClient.ApiException) error).status == 401) {
                        api.clearSession(); user = null; authMode = "welcome"; sessionRestoreFailed = false;
                    } else {
                        sessionRestoreFailed = true;
                        setNotice("Your session is saved. Check your connection and try again.", true);
                    }
                } else {
                    sessionRestoreFailed = false;
                    user = data.optJSONObject("user");
                    page = "home";
                    refreshWorkspace();
                }
                render();
            });
        }
    }

    @Override protected void onDestroy() {
        super.onDestroy();
        io.shutdownNow();
    }

    @Override protected void onPause() { super.onPause(); returnedFromBackground = true; }

    @Override protected void onResume() {
        super.onResume();
        if (returnedFromBackground && user != null && api != null && api.hasSession()) {
            returnedFromBackground = false;
            refreshCurrentPage();
        }
    }

    private interface Callback { void done(JSONObject data, Exception error); }

    private void call(String method, String path, JSONObject payload, Callback callback) {
        loading = true;
        render();
        io.execute(() -> {
            JSONObject result = null;
            Exception failure = null;
            try { result = api.request(method, path, payload); }
            catch (Exception e) { failure = e; }
            JSONObject finalResult = result;
            Exception finalFailure = failure;
            main.post(() -> {
                loading = false;
                if (finalFailure instanceof ApiClient.ApiException && ((ApiClient.ApiException) finalFailure).status == 401) {
                    api.clearSession(); user = null; authMode = "welcome";
                }
                callback.done(finalResult, finalFailure);
            });
        });
    }

    private void render() {
        int savedScrollY = user != null && contentScroll != null ? contentScroll.getScrollY() : 0;
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG);
        root.setFitsSystemWindows(true);
        setContentView(root);

        if (user == null) {
            renderAuth();
            return;
        }

        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(20), dp(16), dp(20), dp(12));
        header.setBackgroundColor(BG);
        LinearLayout brand = new LinearLayout(this);
        brand.setGravity(Gravity.CENTER_VERTICAL);
        TextView mark = text("✓", 17, INK, true);
        mark.setGravity(Gravity.CENTER);
        mark.setBackground(round(0xffd9ed9e, 14));
        brand.addView(mark, new LinearLayout.LayoutParams(dp(LOGO_MARK_SIZE), dp(LOGO_MARK_SIZE)));
        TextView brandName = text("  flowstate", 19, INK, true);
        brand.addView(brandName);
        View spacer = new View(this);
        header.addView(brand);
        header.addView(spacer, new LinearLayout.LayoutParams(0, 1, 1));
        TextView avatar = text(first(user.optString("name", "F")), 14, GREEN, true);
        avatar.setGravity(Gravity.CENTER);
        avatar.setBackground(round(0xffe3eee5, 22));
        header.addView(avatar, new LinearLayout.LayoutParams(dp(36), dp(36)));
        root.addView(header);

        ScrollView scroll = new ScrollView(this);
        contentScroll = scroll;
        scroll.setFillViewport(false);
        body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(20), dp(12), dp(20), dp(26));
        scroll.addView(body);
        int restoreY = savedScrollY;
        scroll.post(() -> scroll.scrollTo(0, restoreY));
        scroll.setOnTouchListener(new View.OnTouchListener() {
            float startY;
            @Override public boolean onTouch(View view, MotionEvent event) {
                if (event.getAction() == MotionEvent.ACTION_DOWN) startY = event.getY();
                if (event.getAction() == MotionEvent.ACTION_UP && scroll.getScrollY() == 0 && event.getY() - startY > dp(90)) {
                    refreshCurrentPage(); return false;
                }
                return false;
            }
        });
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

        if (!notice.isEmpty()) {
            TextView message = text(notice, 13, noticeError ? 0xffa63f35 : GREEN, false);
            message.setPadding(dp(14), dp(12), dp(14), dp(12));
            message.setBackground(round(noticeError ? 0xffffe9e5 : 0xffe6f1e8, 12));
            body.addView(message, margin(-1, -2, 0, 14));
        }
        if (loading) {
            TextView busy = text("Connecting to your workspace…", 14, MUTED, false);
            body.addView(busy, margin(-1, dp(6), 0, 12));
        }

        switch (page) {
            case "tasks": renderTasks(); break;
            case "board": renderBoard(); break;
            case "calendar": renderCalendar(); break;
            case "activity": renderActivity(); break;
            case "teams": renderTeams(); break;
            case "settings": renderSettings(); break;
            default: renderHome(); break;
        }
        renderNavigation();
    }

    private void renderNavigation() {
        LinearLayout dock = new LinearLayout(this);
        dock.setGravity(Gravity.CENTER_VERTICAL);
        dock.setPadding(dp(7), dp(7), dp(7), dp(7));
        dock.setBackground(round(0xff17221c, 30));
        dock.setElevation(dp(10));
        if (animateNavigation) {
            dock.setTranslationY(dp(9)); dock.setAlpha(0f);
            dock.animate().translationY(0).alpha(1f).setDuration(230).setInterpolator(new DecelerateInterpolator()).start();
            animateNavigation = false;
        }
        String[][] items = {{"home", "Home"}, {"tasks", "Tasks"}, {"board", "Board"}, {"more", "More"}};
        int[] icons = {R.drawable.ic_nav_home, R.drawable.ic_nav_tasks, R.drawable.ic_nav_board, R.drawable.ic_nav_more};
        for (int i = 0; i < items.length; i++) {
            String[] item = items[i];
            boolean active = page.equals(item[0]) || (item[0].equals("more") && isMorePage());
            LinearLayout tab = new LinearLayout(this); tab.setOrientation(LinearLayout.VERTICAL); tab.setGravity(Gravity.CENTER);
            tab.setBackground(round(active ? 0xff294d3c : 0x0017221c, 21));
            ImageView glyph = new ImageView(this); glyph.setImageResource(icons[i]);
            glyph.setColorFilter(active ? 0xffd9ed9e : 0xffe4eae5);
            tab.addView(glyph, new LinearLayout.LayoutParams(dp(22), dp(22)));
            TextView caption = text(item[1], 10, active ? CARD : 0xffb8c3bb, active);
            LinearLayout.LayoutParams captionParams = new LinearLayout.LayoutParams(-2, -2); captionParams.topMargin = dp(1); tab.addView(caption, captionParams);
            tab.setOnClickListener(v -> {
                tab.animate().scaleX(.91f).scaleY(.91f).setDuration(75).withEndAction(() -> tab.animate().scaleX(1f).scaleY(1f).setDuration(120).start()).start();
                if (item[0].equals("more")) showMore(); else navigate(item[0]);
            });
            dock.addView(tab, new LinearLayout.LayoutParams(0, dp(BUTTON_HEIGHT), 1));
        }
        ImageView add = new ImageView(this); add.setImageResource(R.drawable.ic_nav_add); add.setColorFilter(INK); add.setPadding(dp(12), dp(12), dp(12), dp(12)); add.setScaleType(ImageView.ScaleType.FIT_CENTER); add.setBackground(round(0xffd9ed9e, 30));
        add.setElevation(dp(2)); add.setOnClickListener(v -> editTask(null));
        LinearLayout.LayoutParams addParams = new LinearLayout.LayoutParams(dp(BUTTON_HEIGHT), dp(BUTTON_HEIGHT)); addParams.setMargins(dp(6), 0, 0, 0);
        dock.addView(add, addParams);
        LinearLayout shell = new LinearLayout(this); shell.setGravity(Gravity.CENTER); shell.setPadding(dp(14), dp(6), dp(14), dp(10));
        shell.addView(dock, new LinearLayout.LayoutParams(-1, dp(64)));
        root.addView(shell, new LinearLayout.LayoutParams(-1, dp(80)));
    }

    private boolean isMorePage() { return page.equals("calendar") || page.equals("activity") || page.equals("teams") || page.equals("settings"); }

    private void navigate(String destination) {
        page = destination; notice = ""; contentScroll = null; animateNavigation = true; render();
        if (destination.equals("home")) refreshDashboard();
        if (destination.equals("tasks") || destination.equals("board") || destination.equals("calendar")) refreshTasks();
        if (destination.equals("activity")) refreshHistory();
        if (destination.equals("teams")) refreshTeams();
    }

    private void showMore() {
        LinearLayout sheet = new LinearLayout(this); sheet.setOrientation(LinearLayout.VERTICAL); sheet.setPadding(dp(18), dp(8), dp(18), dp(12));
        sheet.addView(text("Your workspace", 21, INK, true), margin(-1, 0, 0, 3));
        sheet.addView(text("More places to plan and keep things moving.", 13, MUTED, false), margin(-1, 0, 0, 12));
        String[][] choices = {{"calendar", "◷", "Calendar", "See tasks by day"}, {"activity", "↗", "Activity", "Track recent progress"}, {"teams", "♧", "Teams", "Work together"}, {"settings", "⚙", "Settings", "Profile and security"}};
        AlertDialog dialog = new AlertDialog.Builder(this).setView(sheet).create();
        for (String[] item : choices) {
            LinearLayout row = new LinearLayout(this); row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(dp(10), dp(8), dp(10), dp(8)); row.setBackground(round(0xfff6f7f3, 14));
            TextView icon = text(item[1], 20, GREEN, true); icon.setGravity(Gravity.CENTER); icon.setBackground(round(0xffe5efe5, 14)); row.addView(icon, new LinearLayout.LayoutParams(dp(44), dp(44)));
            LinearLayout labels = new LinearLayout(this); labels.setOrientation(LinearLayout.VERTICAL); labels.setPadding(dp(11), 0, 0, 0);
            labels.addView(text(item[2], 14, INK, true)); labels.addView(text(item[3], 11, MUTED, false));
            row.addView(labels, new LinearLayout.LayoutParams(0, -2, 1)); row.addView(text("›", 20, MUTED, false));
            row.setOnClickListener(v -> { dialog.dismiss(); navigate(item[0]); }); sheet.addView(row, margin(-1, 0, 0, 7));
        }
        Button signOut = smallButton("Sign out", true); signOut.setOnClickListener(v -> { dialog.dismiss(); confirmSignOut(); }); sheet.addView(signOut, margin(-1, dp(44), 0, 0));
        dialog.show();
        if (dialog.getWindow() != null) dialog.getWindow().setBackgroundDrawable(round(CARD, 26));
    }

    private void renderAuth() {
        if (sessionRestoreFailed && api.hasSession()) { renderSessionRecovery(); return; }
        if (loading && api.hasSession()) {
            renderStartup();
            return;
        }
        if (authMode.equals("welcome")) {
            renderWelcome();
            return;
        }
        ScrollView scroll = new ScrollView(this);
        LinearLayout wrap = new LinearLayout(this);
        wrap.setGravity(Gravity.CENTER_HORIZONTAL);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setPadding(dp(24), dp(34), dp(24), dp(24));
        scroll.addView(wrap);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, -1));

        LinearLayout logo = new LinearLayout(this);
        logo.setGravity(Gravity.CENTER_VERTICAL);
        TextView mark = text("✓", 18, INK, true); mark.setGravity(Gravity.CENTER); mark.setBackground(round(0xffd9ed9e, 14));
        logo.addView(mark, new LinearLayout.LayoutParams(dp(LOGO_MARK_SIZE), dp(LOGO_MARK_SIZE)));
        logo.addView(text("  flowstate", 22, INK, true));
        wrap.addView(logo, margin(-1, 0, 0, 38));
        Button backHome = linkButton("←  Welcome");
        backHome.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        backHome.setOnClickListener(v -> { authMode = "welcome"; authStage = 1; notice = ""; render(); });
        wrap.addView(backHome, margin(-1, 0, 0, 15));

        TextView kicker = text(authMode.equals("login") ? "WELCOME BACK" : authMode.equals("register") ? "YOUR WORKSPACE STARTS HERE" : "ACCOUNT RECOVERY", 11, GREEN, true);
        kicker.setLetterSpacing(0.08f);
        wrap.addView(kicker, margin(-1, 0, 0, 8));
        wrap.addView(text(authMode.equals("login") ? "Good to see you." : authMode.equals("register") ? "Create your account." : "Reset your password.", 28, INK, true), margin(-1, 0, 0, 5));
        wrap.addView(text(authMode.equals("login") ? "Sign in to pick up where you left off." : "Your plans, priorities, and people in one calm workspace.", 14, MUTED, false), margin(-1, 0, 0, 20));

        if (authMode.equals("register")) {
            LinearLayout steps = new LinearLayout(this); steps.setGravity(Gravity.CENTER_VERTICAL);
            String[] stepLabels = {"Your details", "Verify email", "Password"};
            for (int i = 0; i < stepLabels.length; i++) {
                final int stepIndex = i + 1;
                LinearLayout segment = new LinearLayout(this); segment.setOrientation(LinearLayout.VERTICAL);
                View line = new View(this); line.setBackground(round(authStage >= stepIndex ? GREEN : 0xffdfe5dc, 4));
                segment.addView(line, new LinearLayout.LayoutParams(-1, dp(4)));
                TextView label = text(stepLabels[i], 9, authStage >= stepIndex ? GREEN : MUTED, authStage == stepIndex);
                segment.addView(label, margin(-1, dp(6), 0, 0));
                LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(0, -2, 1); sp.setMargins(dp(2), 0, dp(6), 0); steps.addView(segment, sp);
            }
            wrap.addView(steps, margin(-1, 0, 0, 17));
        }

        LinearLayout form = card();
        form.setPadding(dp(17), dp(18), dp(17), dp(18));
        form.setElevation(dp(2));
        if (authMode.equals("login")) {
            EditText email = field("Email address", emailValue, false); email.setInputType(33); form.addView(email, margin(-1, 0, 0, FIELD_GAP)); email.addTextChangedListener(watcher(v -> emailValue = v));
            EditText pass = field("Password", passwordValue, true); form.addView(pass, margin(-1, 0, 0, 2)); pass.addTextChangedListener(watcher(v -> passwordValue = v));
            addPasswordToggle(form, pass);
            form.addView(new View(this), new LinearLayout.LayoutParams(1, dp(9)));
            Button signIn = primary("Sign in"); signIn.setOnClickListener(v -> doLogin()); form.addView(signIn, margin(-1, dp(3), 0, 0));
            Button forgot = linkButton("Forgot password?"); forgot.setOnClickListener(v -> {authMode="forgot";authStage=1;notice="";render();}); form.addView(forgot, margin(-1, dp(6), 0, 0));
            Button create = linkButton("New to Flowstate?  Create an account"); create.setOnClickListener(v -> {authMode="register";authStage=1;notice="";render();}); form.addView(create, margin(-1, dp(2), 0, 0));
        } else if (authMode.equals("register")) {
            if (authStage == 1) {
                EditText name = field("Your name", nameValue, false); form.addView(name, margin(-1, 0, 0, 10)); name.addTextChangedListener(watcher(v -> nameValue = v));
                EditText email = field("Email address", emailValue, false); email.setInputType(33); form.addView(email, margin(-1, 0, 0, FIELD_GAP)); email.addTextChangedListener(watcher(v -> emailValue = v));
                Button next = primary("Send verification code"); next.setOnClickListener(v -> sendRegistrationCode()); form.addView(next);
            } else if (authStage == 2) {
                form.addView(text("Enter the six-digit code sent to " + emailValue, 13, MUTED, false), margin(-1, 0, 0, FIELD_GAP));
                EditText otp = field("Verification code", otpValue, false); otp.setInputType(2); form.addView(otp, margin(-1, 0, 0, FIELD_GAP)); otp.addTextChangedListener(watcher(v -> otpValue = v));
                Button verify = primary("Verify email"); verify.setOnClickListener(v -> verifyRegistrationCode()); form.addView(verify);
            } else {
                EditText pass = field("Create password", newPasswordValue, true); form.addView(pass, margin(-1, 0, 0, 2)); pass.addTextChangedListener(watcher(v -> newPasswordValue = v));
                addPasswordToggle(form, pass);
                form.addView(text("Use at least 8 characters. A longer passphrase is easier to remember.", 11, MUTED, false), margin(-1, 0, 0, 10));
                EditText confirm = field("Confirm password", confirmPasswordValue, true); form.addView(confirm, margin(-1, 0, 0, FIELD_GAP)); confirm.addTextChangedListener(watcher(v -> confirmPasswordValue = v));
                Button finish = primary("Create my account"); finish.setOnClickListener(v -> completeRegistration()); form.addView(finish);
            }
            Button back = linkButton("Already have an account?  Sign in"); back.setOnClickListener(v -> {authMode="login";authStage=1;render();}); form.addView(back, margin(-1, dp(8), 0, 0));
        } else {
            if (authStage == 1) {
                EditText email = field("Email address", emailValue, false); email.setInputType(33); form.addView(email, margin(-1, 0, 0, FIELD_GAP)); email.addTextChangedListener(watcher(v -> emailValue = v));
                Button send = primary("Send verification code"); send.setOnClickListener(v -> sendResetCode()); form.addView(send);
            } else if (authStage == 2) {
                form.addView(text("Enter the six-digit code sent to " + emailValue, 13, MUTED, false), margin(-1, 0, 0, FIELD_GAP));
                EditText otp = field("Verification code", otpValue, false); otp.setInputType(2); form.addView(otp, margin(-1, 0, 0, FIELD_GAP)); otp.addTextChangedListener(watcher(v -> otpValue = v));
                Button verify = primary("Verify code"); verify.setOnClickListener(v -> verifyResetCode()); form.addView(verify);
            } else {
                EditText pass = field("New password (8+ characters)", newPasswordValue, true); form.addView(pass, margin(-1, 0, 0, 10)); pass.addTextChangedListener(watcher(v -> newPasswordValue = v));
                EditText confirm = field("Confirm new password", confirmPasswordValue, true); form.addView(confirm, margin(-1, 0, 0, FIELD_GAP)); confirm.addTextChangedListener(watcher(v -> confirmPasswordValue = v));
                Button finish = primary("Set new password"); finish.setOnClickListener(v -> completePasswordReset()); form.addView(finish);
            }
            Button back = linkButton("Back to sign in"); back.setOnClickListener(v -> {authMode="login";authStage=1;render();}); form.addView(back, margin(-1, dp(8), 0, 0));
        }
        wrap.addView(form, margin(-1, 0, 0, 12));
        if (!notice.isEmpty()) {
            TextView msg = text(notice, 13, noticeError ? 0xffa63f35 : GREEN, false);
            msg.setPadding(dp(12), dp(11), dp(12), dp(11)); msg.setBackground(round(noticeError ? 0xffffe9e5 : 0xffe6f1e8, 10));
            wrap.addView(msg, margin(-1, 0, 0, 8));
        }
        if (loading) wrap.addView(text("Please wait…", 13, MUTED, false), margin(-1, dp(8), 0, 0));
        wrap.addView(text("Your workspace is private and secure.", 12, MUTED, false), margin(-1, dp(14), 0, 0));
    }

    private void addPasswordToggle(LinearLayout parent, EditText input) {
        Button toggle = linkButton("Show password"); toggle.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        toggle.setOnClickListener(v -> {
            boolean visible = toggle.getText().toString().startsWith("Show");
            int position = input.getSelectionStart();
            input.setInputType(visible ? 145 : 129);
            input.setSelection(Math.max(0, Math.min(position, input.length())));
            toggle.setText(visible ? "Hide password" : "Show password");
        });
        parent.addView(toggle, margin(-1, dp(BUTTON_HEIGHT), 0, 0));
    }

    private void renderStartup() {
        LinearLayout center = new LinearLayout(this);
        center.setOrientation(LinearLayout.VERTICAL);
        center.setGravity(Gravity.CENTER);
        center.setPadding(dp(28), dp(30), dp(28), dp(30));
        root.addView(center, new LinearLayout.LayoutParams(-1, -1));
        TextView mark = text("✓", 22, INK, true);
        mark.setGravity(Gravity.CENTER);
        mark.setBackground(round(0xffd9ed9e, 20));
        center.addView(mark, new LinearLayout.LayoutParams(dp(56), dp(56)));
        center.addView(text("flowstate", 25, INK, true), margin(-1, 0, 0, 7));
        center.addView(text("Getting your workspace ready…", 14, MUTED, false));
    }

    private void renderWelcome() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setGravity(Gravity.CENTER_HORIZONTAL);
        wrap.setPadding(dp(24), dp(24), dp(24), dp(20));
        scroll.addView(wrap);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        TextView mark = text("✓", 17, INK, true);
        mark.setGravity(Gravity.CENTER);
        mark.setBackground(round(0xffd9ed9e, 13));
        top.addView(mark, new LinearLayout.LayoutParams(dp(LOGO_MARK_SIZE), dp(LOGO_MARK_SIZE)));
        top.addView(text("  flowstate", 20, INK, true));
        View push = new View(this);
        top.addView(push, new LinearLayout.LayoutParams(0, 1, 1));
        TextView version = text(String.format(Locale.US, "%02d  /  03", welcomeStep + 1), 10, MUTED, true);
        top.addView(version);
        wrap.addView(top, margin(-1, 0, 0, 0));

        FrameLayout art = new FrameLayout(this);
        GradientDrawable artBg = new GradientDrawable(GradientDrawable.Orientation.TL_BR, new int[]{0xffdcece1, 0xfff1f4e9});
        artBg.setCornerRadius(dp(30)); art.setBackground(artBg);
        TextView ring = text("✓", 42, INK, true); ring.setGravity(Gravity.CENTER); ring.setBackground(round(0xffd9ed9e, 60));
        FrameLayout.LayoutParams ringParams = new FrameLayout.LayoutParams(dp(112), dp(112), Gravity.CENTER);
        art.addView(ring, ringParams);
        TextView note = text("TODAY", 10, GREEN, true); note.setGravity(Gravity.CENTER); note.setPadding(dp(12), dp(9), dp(12), dp(9)); note.setBackground(round(CARD, 22));
        FrameLayout.LayoutParams noteParams = new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.END); noteParams.setMargins(0, dp(18), dp(16), 0); art.addView(note, noteParams);
        TextView focus = text("◷  25 min focus", 12, INK, true); focus.setGravity(Gravity.CENTER); focus.setPadding(dp(14), dp(10), dp(14), dp(10)); focus.setBackground(round(CARD, 22));
        FrameLayout.LayoutParams focusParams = new FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM | Gravity.START); focusParams.setMargins(dp(15), 0, 0, dp(16)); art.addView(focus, focusParams);
        TextView done = text("2 tasks done", 11, GREEN, true); done.setGravity(Gravity.CENTER); done.setPadding(dp(12), dp(9), dp(12), dp(9)); done.setBackground(round(CARD, 22));
        FrameLayout.LayoutParams doneParams = new FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM | Gravity.END); doneParams.setMargins(0, 0, dp(15), dp(19)); art.addView(done, doneParams);
        wrap.addView(art, new LinearLayout.LayoutParams(-1, dp(210)));

        String[] headlines = {"Make space for your best work.", "Turn big plans into next steps.", "Keep your momentum visible."};
        String[] copies = {"A quieter place to plan your day, focus on what matters, and keep your work moving.", "Capture a task, give it a clear next step, and move it through your workflow.", "See what is done, what needs attention, and where your time is going."};
        TextView headline = text(headlines[welcomeStep], 29, INK, true); headline.setGravity(Gravity.CENTER); headline.setLineSpacing(dp(1), 1f);
        wrap.addView(headline, margin(-1, dp(24), 0, 8));
        TextView copy = text(copies[welcomeStep], 14, MUTED, false); copy.setGravity(Gravity.CENTER); copy.setLineSpacing(dp(3), 1.05f);
        wrap.addView(copy, margin(-1, 0, 0, 17));
        Button explore = linkButton(welcomeStep == 2 ? "Back to the beginning" : "See how Flowstate works   →");
        explore.setOnClickListener(v -> { welcomeStep = welcomeStep == 2 ? 0 : welcomeStep + 1; render(); });
        wrap.addView(explore, margin(-1, dp(44), 0, 7));

        LinearLayout actions = new LinearLayout(this); actions.setOrientation(LinearLayout.VERTICAL); actions.setPadding(dp(24), dp(8), dp(24), dp(10));
        Button create = primary("Create your free account");
        create.setOnClickListener(v -> { authMode = "register"; authStage = 1; notice = ""; render(); });
        actions.addView(create, margin(-1, dp(50), 0, 5));
        Button signIn = button("I already have an account  ·  Sign in", 0x00000000, GREEN, true);
        signIn.setMinHeight(dp(BUTTON_HEIGHT));
        signIn.setOnClickListener(v -> { authMode = "login"; authStage = 1; notice = ""; render(); });
        actions.addView(signIn, margin(-1, dp(44), 0, 0));
        root.addView(actions, new LinearLayout.LayoutParams(-1, -2));
    }

    private void addPreviewTask(LinearLayout parent, String icon, String label, boolean completed) {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER_VERTICAL);
        TextView check = text(icon, 12, completed ? GREEN : MUTED, true);
        check.setGravity(Gravity.CENTER);
        check.setBackground(round(completed ? 0xffe5f0e6 : 0xffedf0eb, 20));
        row.addView(check, new LinearLayout.LayoutParams(dp(21), dp(21)));
        TextView task = text(label, 12, completed ? MUTED : INK, !completed);
        if (completed) task.setPaintFlags(task.getPaintFlags() | android.graphics.Paint.STRIKE_THRU_TEXT_FLAG);
        LinearLayout.LayoutParams taskParams = new LinearLayout.LayoutParams(-2, -2);
        taskParams.setMargins(dp(8), 0, 0, 0);
        row.addView(task, taskParams);
        parent.addView(row, margin(-1, 0, 0, 5));
    }

    private LinearLayout benefitChip(String number, String label) {
        LinearLayout chip = new LinearLayout(this);
        chip.setOrientation(LinearLayout.VERTICAL);
        chip.setPadding(dp(9), dp(9), dp(6), dp(9));
        chip.setBackground(round(CARD, 13));
        chip.addView(text(number, 9, GREEN, true));
        chip.addView(text(label, 10, INK, true), margin(-1, 0, 0, 0));
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, -2, 1);
        p.setMargins(dp(2), 0, dp(2), 0);
        chip.setLayoutParams(p);
        return chip;
    }

    private void doLogin() {
        if (emailValue.trim().isEmpty() || passwordValue.isEmpty()) { setNotice("Enter your email address and password.", true); render(); return; }
        setNotice("", false);
        call("POST", "auth/login", obj("email", emailValue.trim(), "password", passwordValue), (result, error) -> {
            if (error != null) { setNotice(error.getMessage(), true); render(); return; }
            call("GET", "auth/me", null, (me, meError) -> {
                if (meError != null) { setNotice(meError.getMessage(), true); render(); return; }
                user = me.optJSONObject("user"); page = "home"; authMode = "login"; passwordValue = ""; notice = "";
                render(); refreshWorkspace();
            });
        });
    }

    private void sendRegistrationCode() {
        if (nameValue.trim().isEmpty() || emailValue.trim().isEmpty()) { setNotice("Enter your name and email address.", true); render(); return; }
        call("POST", "auth/register", obj("name", nameValue.trim(), "email", emailValue.trim()), (data, error) -> {
            if (error != null) setNotice(error.getMessage(), true);
            else { authStage = 2; setNotice("We sent a six-digit code to your email.", false); }
            render();
        });
    }

    private void verifyRegistrationCode() {
        call("POST", "auth/register/verify", obj("email", emailValue.trim(), "otp", otpValue.trim()), (data, error) -> {
            if (error != null) setNotice(error.getMessage(), true);
            else { authStage = 3; setNotice("Email verified. Create a password to finish.", false); }
            render();
        });
    }

    private void completeRegistration() {
        if (newPasswordValue.length() < 8 || !newPasswordValue.equals(confirmPasswordValue)) { setNotice("Use at least 8 characters and make both passwords match.", true); render(); return; }
        call("POST", "auth/register/complete", obj("email", emailValue.trim(), "password", newPasswordValue), (data, error) -> {
            if (error != null) { setNotice(error.getMessage(), true); render(); return; }
            passwordValue = newPasswordValue; doLogin();
        });
    }

    private void sendResetCode() {
        call("POST", "auth/password-reset", obj("email", emailValue.trim()), (data, error) -> {
            if (error != null) setNotice(error.getMessage(), true);
            else { authStage = 2; setNotice("A verification code is on its way.", false); }
            render();
        });
    }

    private void verifyResetCode() {
        call("POST", "auth/password-reset/verify", obj("email", emailValue.trim(), "otp", otpValue.trim()), (data, error) -> {
            if (error != null) setNotice(error.getMessage(), true);
            else { authStage = 3; setNotice("Email verified. Set a new password.", false); }
            render();
        });
    }

    private void completePasswordReset() {
        if (newPasswordValue.length() < 8 || !newPasswordValue.equals(confirmPasswordValue)) { setNotice("Use at least 8 characters and make both passwords match.", true); render(); return; }
        call("POST", "auth/password-reset/complete", obj("email", emailValue.trim(), "new_password", newPasswordValue), (data, error) -> {
            if (error != null) setNotice(error.getMessage(), true);
            else { authMode = "login"; authStage = 1; passwordValue = ""; newPasswordValue = ""; confirmPasswordValue = ""; setNotice("Password changed. Sign in with your new password.", false); }
            render();
        });
    }

    private void renderHome() {
        Calendar now = Calendar.getInstance();
        int hour = now.get(Calendar.HOUR_OF_DAY);
        String greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
        sectionTitle(greeting + ", " + user.optString("name", "there").split(" ")[0] + ".", "Let’s make room for what matters today.");
        body.addView(momentumCard(), margin(-1, dp(4), 0, 12));
        Button add = primary("＋   Add a task"); add.setOnClickListener(v -> editTask(null)); body.addView(add, margin(-1, dp(5), 0, 16));
        LinearLayout row = new LinearLayout(this);
        row.addView(metricCard("Completed today", metrics.optString("tasks_completed_today", "0")), new LinearLayout.LayoutParams(0, -2, 1));
        row.addView(metricCard("Due soon", String.valueOf(dueSoonCount())), new LinearLayout.LayoutParams(0, -2, 1));
        body.addView(row, margin(-1, 0, 0, FIELD_GAP));
        LinearLayout row2 = new LinearLayout(this);
        row2.addView(metricCard("Overdue", metrics.optString("overdue_count", "0")), new LinearLayout.LayoutParams(0, -2, 1));
        row2.addView(metricCard("High priority", metrics.optString("high_priority_count", "0")), new LinearLayout.LayoutParams(0, -2, 1));
        body.addView(row2, margin(-1, 0, 0, 22));
        body.addView(text("Up next", 19, INK, true), margin(-1, 0, 0, 8));
        JSONArray open = new JSONArray();
        for (int i = 0; i < tasks.length(); i++) {
            JSONObject task = tasks.optJSONObject(i);
            if (task != null && !"completed".equals(task.optString("status"))) open.put(task);
        }
        LinearLayout filters = new LinearLayout(this); filters.setGravity(Gravity.CENTER_VERTICAL);
        String[][] filterItems = {{"upcoming", "Next up"}, {"today", "Due today"}, {"overdue", "Overdue"}};
        for (String[] item : filterItems) {
            Button filter = button(item[1], dashboardFilter.equals(item[0]) ? 0xffe1eddf : CARD,
                    dashboardFilter.equals(item[0]) ? GREEN : MUTED, dashboardFilter.equals(item[0]));
            filter.setTextSize(11); filter.setOnClickListener(v -> { dashboardFilter = item[0]; contentScroll = null; render(); });
            LinearLayout.LayoutParams fp = new LinearLayout.LayoutParams(0, dp(BUTTON_HEIGHT), 1); fp.setMargins(dp(3), 0, dp(3), 0); filters.addView(filter, fp);
        }
        body.addView(filters, margin(-1, 0, 0, 8));
        JSONArray visible = new JSONArray();
        String today = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
        for (int i = 0; i < open.length(); i++) {
            JSONObject task = open.optJSONObject(i); if (task == null) continue;
            String due = dateOnly(task.optString("due_date", ""));
            boolean match = dashboardFilter.equals("upcoming") || (dashboardFilter.equals("today") && today.equals(due))
                    || (dashboardFilter.equals("overdue") && !due.isEmpty() && due.compareTo(today) < 0);
            if (match) visible.put(task);
        }
        if (visible.length() == 0) {
            String message = dashboardFilter.equals("today") ? "Nothing due today." : dashboardFilter.equals("overdue") ? "You’re all caught up." : "Your list has room to breathe.";
            body.addView(emptyCard(message, dashboardFilter.equals("overdue") ? "No overdue tasks. Keep that calm momentum." : "Add a task when something needs your attention."));
        }
        for (int i = 0; i < Math.min(visible.length(), 4); i++) addTaskCard(visible.optJSONObject(i), false);
        Button seeAll = linkButton("See all tasks →"); seeAll.setOnClickListener(v -> navigate("tasks")); body.addView(seeAll, margin(-1, dp(7), 0, 0));
        if (history.length() > 0) {
            body.addView(text("Recent activity", 19, INK, true), margin(-1, dp(20), 0, 8));
            LinearLayout activityCard = card(); activityCard.setPadding(dp(14), dp(5), dp(14), dp(5));
            for (int i = 0; i < Math.min(3, history.length()); i++) {
                JSONObject item = history.optJSONObject(i); if (item == null) continue;
                LinearLayout event = new LinearLayout(this); event.setGravity(Gravity.CENTER_VERTICAL);
                TextView dot = text("•", 23, GREEN, true); dot.setGravity(Gravity.CENTER); event.addView(dot, new LinearLayout.LayoutParams(dp(26), dp(32)));
                LinearLayout copy = new LinearLayout(this); copy.setOrientation(LinearLayout.VERTICAL); copy.setPadding(dp(7), dp(6), 0, dp(6));
                copy.addView(text(item.optString("title", "Task"), 12, INK, true));
                copy.addView(text(activityLabel(item.optString("event", "updated")), 10, MUTED, false));
                event.addView(copy, new LinearLayout.LayoutParams(0, -2, 1)); activityCard.addView(event);
                if (i < Math.min(3, history.length()) - 1) { View line = new View(this); line.setBackgroundColor(BORDER); activityCard.addView(line, new LinearLayout.LayoutParams(-1, dp(1))); }
            }
            body.addView(activityCard, margin(-1, 0, 0, 5));
            Button historyLink = linkButton("View activity →"); historyLink.setOnClickListener(v -> navigate("activity")); body.addView(historyLink, margin(-1, 0, 0, 0));
        }
        if (loading) body.addView(text("Refreshing your workspace…", 12, MUTED, false), margin(-1, dp(10), 0, 0));
    }

    private int dueSoonCount() {
        Calendar limit = Calendar.getInstance(); limit.add(Calendar.DAY_OF_YEAR, 3);
        String today = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
        String end = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(limit.getTime());
        int count = 0;
        for (int i = 0; i < tasks.length(); i++) {
            JSONObject task = tasks.optJSONObject(i); if (task == null || "completed".equals(task.optString("status"))) continue;
            String due = dateOnly(task.optString("due_date", "")); if (!due.isEmpty() && due.compareTo(today) >= 0 && due.compareTo(end) <= 0) count++;
        }
        return count;
    }

    private String activityLabel(String event) {
        if (event.startsWith("moved:")) return "Moved " + event.substring("moved:".length()).replace("->", " to ").replace('_', ' ');
        if ("created".equals(event)) return "Added to your workspace";
        return "Updated task";
    }

    private View momentumCard() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(17), dp(18), dp(16));
        GradientDrawable background = new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{0xff173e33, 0xff245743});
        background.setCornerRadius(dp(20));
        panel.setBackground(background);
        LinearLayout head = new LinearLayout(this);
        head.setGravity(Gravity.CENTER_VERTICAL);
        TextView label = text("YOUR MOMENTUM", 10, 0xffd9ed9e, true);
        label.setLetterSpacing(0.11f);
        head.addView(label, new LinearLayout.LayoutParams(0, -2, 1));
        TextView badge = text("THIS WEEK", 9, CARD, true);
        badge.setPadding(dp(9), dp(5), dp(9), dp(5));
        badge.setBackground(round(0x33ffffff, 20));
        head.addView(badge);
        panel.addView(head);
        LinearLayout progressRow = new LinearLayout(this);
        progressRow.setGravity(Gravity.BOTTOM);
        progressRow.addView(text(metrics.optString("completion_rate", "0") + "%", 34, CARD, true));
        progressRow.addView(text("  of your tasks completed", 12, 0xffe2ebe5, false), margin(-2, 0, 0, dp(5)));
        panel.addView(progressRow, margin(-1, dp(7), 0, 8));
        android.widget.FrameLayout track = new android.widget.FrameLayout(this);
        track.setBackground(round(0x44ffffff, 12));
        int completion = Math.max(0, Math.min(100, metrics.optInt("completion_rate", 0)));
        android.widget.FrameLayout.LayoutParams fill = new android.widget.FrameLayout.LayoutParams(dp(4), dp(5));
        View progress = new View(this); progress.setBackground(round(0xffd9ed9e, 12)); track.addView(progress, fill);
        track.post(() -> {
            android.widget.FrameLayout.LayoutParams current = (android.widget.FrameLayout.LayoutParams) progress.getLayoutParams();
            current.width = Math.max(dp(4), track.getWidth() * completion / 100);
            progress.setLayoutParams(current);
        });
        panel.addView(track, new LinearLayout.LayoutParams(-1, dp(5)));
        panel.addView(text(metrics.optString("tasks_completed_week", "0") + " completed this week", 11, 0xffd5e2da, false), margin(-1, dp(7), 0, 0));
        return panel;
    }

    private View metricCard(String label, String value) {
        LinearLayout card = card(); card.setPadding(dp(14), dp(13), dp(14), dp(13));
        card.addView(text(value, 25, INK, true));
        card.addView(text(label, 12, MUTED, false), margin(-1, dp(3), 0, 0));
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, -2, 1); p.setMargins(dp(4), 0, dp(4), 0); card.setLayoutParams(p);
        return card;
    }

    private void renderTasks() {
        sectionTitle("Your tasks, in good order.", "Capture it, clarify the next step, and keep moving.");
        Button add = primary("＋   Add a task"); add.setOnClickListener(v -> editTask(null)); body.addView(add, margin(-1, dp(3), 0, 14));
        int open = 0, completed = 0, high = 0;
        for (int i = 0; i < tasks.length(); i++) {
            JSONObject t = tasks.optJSONObject(i); if (t == null) continue;
            if ("completed".equals(t.optString("status"))) completed++; else open++;
            if ("high".equals(t.optString("priority"))) high++;
        }
        body.addView(text(tasks.length() + " total   ·   " + open + " active   ·   " + completed + " completed   ·   " + high + " high priority", 12, MUTED, false), margin(-1, 0, 0, 10));
        if (tasks.length() == 0) body.addView(emptyCard("A fresh page.", "Add a task to get your plans out of your head and into motion."));
        for (int i = 0; i < tasks.length(); i++) addTaskCard(tasks.optJSONObject(i), true);
    }

    private void renderBoard() {
        sectionTitle("See work move forward.", "Move each task through a clear next step.");
        body.addView(text("Tap a stage action on a card to move it through your workflow.", 12, MUTED, false), margin(-1, 0, 0, 5));
        String[] statuses = {"backlog", "in_progress", "blocked", "completed"};
        String[] labels = {"Backlog", "In progress", "Blocked", "Completed"};
        for (int s = 0; s < statuses.length; s++) {
            LinearLayout head = new LinearLayout(this); head.setGravity(Gravity.CENTER_VERTICAL);
            head.addView(text(labels[s], 17, INK, true));
            TextView count = text("  " + countStatus(statuses[s]), 12, MUTED, false); head.addView(count);
            body.addView(head, margin(-1, dp(16), 0, 8));
            boolean any = false;
            for (int i = 0; i < tasks.length(); i++) {
                JSONObject t = tasks.optJSONObject(i);
                if (t != null && statuses[s].equals(t.optString("status"))) { addTaskCard(t, true); any = true; }
            }
            if (!any) body.addView(text("Nothing here yet.", 12, MUTED, false), margin(-1, dp(3), 0, 2));
        }
    }

    private int countStatus(String status) {
        int n = 0; for (int i = 0; i < tasks.length(); i++) if (status.equals(tasks.optJSONObject(i).optString("status"))) n++; return n;
    }

    private String nextStatus(String status) {
        if ("backlog".equals(status)) return "in_progress";
        if ("in_progress".equals(status)) return "completed";
        if ("blocked".equals(status)) return "in_progress";
        return null;
    }

    private String previousStatus(String status) {
        if ("in_progress".equals(status)) return "backlog";
        if ("blocked".equals(status)) return "in_progress";
        if ("completed".equals(status)) return "in_progress";
        return null;
    }

    private void addTaskCard(JSONObject task, boolean actions) {
        if (task == null) return;
        LinearLayout box = card(); box.setPadding(dp(14), dp(12), dp(12), dp(12));
        LinearLayout titleRow = new LinearLayout(this); titleRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = text(task.optString("title", "Untitled task"), 15, INK, true);
        title.setLayoutParams(new LinearLayout.LayoutParams(0, -2, 1)); titleRow.addView(title);
        String status = task.optString("status", "backlog");
        TextView badge = text(statusLabel(status), 10, GREEN, true); badge.setPadding(dp(8), dp(5), dp(8), dp(5)); badge.setBackground(round(0xffe6f1e8, 20)); titleRow.addView(badge);
        box.addView(titleRow);
        String detail = task.optString("category", "Personal");
        String due = task.optString("due_date", "");
        if (!due.isEmpty() && !"null".equals(due)) detail += "  ·  " + due.substring(0, Math.min(10, due.length()));
        if (task.optInt("estimated_minutes", 0) > 0) {
            int minutes = task.optInt("estimated_minutes");
            detail += "  ·  " + (minutes >= 60 ? (minutes / 60) + "h " + (minutes % 60) + "m" : minutes + " min");
        }
        if (task.optBoolean("overdue", false)) detail += "  ·  OVERDUE";
        box.addView(text(detail, 12, task.optBoolean("overdue", false) ? 0xffa63f35 : MUTED, false), margin(-1, dp(6), 0, 0));
        if (!task.optString("description", "").isEmpty() && !"null".equals(task.optString("description"))) {
            box.addView(text(task.optString("description"), 13, MUTED, false), margin(-1, dp(6), 0, 0));
        }
        LinearLayout actionsRow = new LinearLayout(this); actionsRow.setGravity(Gravity.CENTER_VERTICAL);
        if (actions) {
            if (page.equals("board")) {
                String next = nextStatus(status);
                if (next != null) {
                    Button moveForward = smallButton("Move to " + statusLabel(next) + "   →", false);
                    moveForward.setOnClickListener(v -> moveTask(task, next));
                    box.addView(moveForward, margin(-1, dp(40), 0, dp(7)));
                }
                String previous = previousStatus(status);
                if (previous != null) {
                    Button moveBack = linkButton("←  Back to " + statusLabel(previous));
                    moveBack.setOnClickListener(v -> moveTask(task, previous));
                    box.addView(moveBack, margin(-1, dp(36), 0, 0));
                }
            }
            Button complete = smallButton("completed".equals(status) ? "Reopen" : "Complete", false);
            complete.setOnClickListener(v -> moveTask(task, "completed".equals(status) ? "in_progress" : "completed"));
            actionsRow.addView(complete, new LinearLayout.LayoutParams(0, dp(BUTTON_HEIGHT), 1));
            Button edit = smallButton("Edit", false); edit.setOnClickListener(v -> editTask(task));
            LinearLayout.LayoutParams ep = new LinearLayout.LayoutParams(0, dp(BUTTON_HEIGHT), 1); ep.setMargins(dp(7), 0, 0, 0); actionsRow.addView(edit, ep);
            Button delete = smallButton("Delete", true); delete.setOnClickListener(v -> confirmDelete(task));
            LinearLayout.LayoutParams dp = new LinearLayout.LayoutParams(0, dp(BUTTON_HEIGHT), 1); dp.setMargins(dp(7), 0, 0, 0); actionsRow.addView(delete, dp);
            box.addView(actionsRow, margin(-1, dp(9), 0, 0));
        }
        body.addView(box, margin(-1, 0, 0, 9));
    }

    private void renderCalendar() {
        sectionTitle("Your time, made visible.", "Choose a day to see what is on your list.");
        LinearLayout dateCard = card(); dateCard.setPadding(dp(15), dp(14), dp(15), dp(14));
        dateCard.addView(text("SELECTED DAY", 10, GREEN, true));
        Button choose = smallButton(selectedDate, false);
        choose.setOnClickListener(v -> {
            Calendar c = Calendar.getInstance();
            try { c.setTime(new SimpleDateFormat("yyyy-MM-dd", Locale.US).parse(selectedDate)); } catch (Exception ignored) {}
            new DatePickerDialog(this, (view, y, m, d) -> {
                selectedDate = String.format(Locale.US, "%04d-%02d-%02d", y, m + 1, d); render();
            }, c.get(Calendar.YEAR), c.get(Calendar.MONTH), c.get(Calendar.DAY_OF_MONTH)).show();
        });
        dateCard.addView(choose, margin(-1, dp(8), 0, 0)); body.addView(dateCard, margin(-1, 0, 0, 15));
        body.addView(text("Agenda", 19, INK, true), margin(-1, 0, 0, 8));
        int count = 0;
        for (int i = 0; i < tasks.length(); i++) {
            JSONObject task = tasks.optJSONObject(i);
            if (task != null && selectedDate.equals(task.optString("due_date", "").substring(0, Math.min(10, task.optString("due_date", "").length())))) {
                addTaskCard(task, true); count++;
            }
        }
        if (count == 0) body.addView(emptyCard("Nothing scheduled.", "Tasks with a due date on " + selectedDate + " will appear here."));
        Button add = primary("＋   Add a task"); add.setOnClickListener(v -> editTask(null)); body.addView(add, margin(-1, dp(14), 0, 0));
    }

    private void renderActivity() {
        sectionTitle("A clear view of your progress.", "Recent changes across your workspace.");
        if (history.length() == 0) body.addView(emptyCard("Your story starts here.", "Create or update a task to see your activity."));
        for (int i = 0; i < history.length(); i++) {
            JSONObject item = history.optJSONObject(i); if (item == null) continue;
            LinearLayout box = card(); box.setPadding(dp(15), dp(13), dp(15), dp(13));
            String event = item.optString("event", "updated").replace("moved:", "Moved ").replace("->", " → ").replace('_', ' ');
            box.addView(text(item.optString("title", "Task"), 15, INK, true));
            box.addView(text(event, 12, GREEN, false), margin(-1, dp(5), 0, 0));
            String time = item.optString("timestamp", "");
            if (!time.isEmpty() && !"null".equals(time)) box.addView(text(time.replace('T', ' ').replace("Z", ""), 11, MUTED, false), margin(-1, dp(4), 0, 0));
            body.addView(box, margin(-1, 0, 0, 8));
        }
    }

    private void renderTeams() {
        sectionTitle("Better work, together.", "Shared spaces for work you do with others.");
        Button create = primary("＋   Create a team"); create.setOnClickListener(v -> prompt("New team", "Team name", name -> {
            call("POST", "teams", obj("name", name), (data, error) -> {
                if (error != null) setNotice(error.getMessage(), true); else setNotice("Team created.", false);
                refreshTeams();
            });
        })); body.addView(create, margin(-1, dp(3), 0, 13));
        if (teams.length() == 0) body.addView(emptyCard("A space to work together.", "Create a team, then invite people by email."));
        for (int i = 0; i < teams.length(); i++) {
            JSONObject team = teams.optJSONObject(i); if (team == null) continue;
            int id = team.optInt("team_id", team.optInt("id", -1));
            LinearLayout box = card(); box.setPadding(dp(15), dp(13), dp(15), dp(13));
            box.addView(text(team.optString("name", "Team space"), 16, INK, true));
            LinearLayout buttons = new LinearLayout(this);
            Button view = smallButton("View team tasks", false); view.setOnClickListener(v -> openTeam(team));
            buttons.addView(view, new LinearLayout.LayoutParams(0, dp(BUTTON_HEIGHT), 1));
            Button invite = smallButton("Invite", false); invite.setOnClickListener(v -> prompt("Invite a teammate", "Email address", address -> {
                call("POST", "teams/" + id + "/members", obj("email", address), (data, error) -> {
                    setNotice(error == null ? "Invitation added to the team." : error.getMessage(), error != null); render();
                });
            }));
            LinearLayout.LayoutParams ip = new LinearLayout.LayoutParams(0, dp(BUTTON_HEIGHT), 1); ip.setMargins(dp(7), 0, 0, 0); buttons.addView(invite, ip);
            box.addView(buttons, margin(-1, dp(9), 0, 0)); body.addView(box, margin(-1, 0, 0, 9));
        }
        if (selectedTeamId > 0) renderTeamTasks();
    }

    private void openTeam(JSONObject team) {
        selectedTeamId = team.optInt("team_id", team.optInt("id", -1));
        selectedTeamName = team.optString("name", "Team");
        call("GET", "teams/" + selectedTeamId + "/tasks", null, (data, error) -> {
            if (error != null) { setNotice(error.getMessage(), true); render(); return; }
            JSONArray teamTasks = data.optJSONArray("tasks");
            if (teamTasks == null) teamTasks = new JSONArray();
            new AlertDialog.Builder(this).setTitle(selectedTeamName + " · Tasks")
                    .setMessage(teamTasks.length() == 0 ? "No tasks have been shared with this team yet." : taskTitles(teamTasks))
                    .setPositiveButton("Assign a task", (d, w) -> chooseTaskForTeam())
                    .setNegativeButton("Done", null).show();
        });
    }

    private void renderTeamTasks() {
        body.addView(text(selectedTeamName + " tasks", 18, INK, true), margin(-1, dp(13), 0, 8));
        Button assign = smallButton("Assign one of my tasks", false); assign.setOnClickListener(v -> chooseTaskForTeam());
        body.addView(assign, margin(-1, 0, 0, 10));
    }

    private String taskTitles(JSONArray list) {
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < list.length(); i++) {
            JSONObject item = list.optJSONObject(i); if (item != null) result.append("• ").append(item.optString("title", "Task")).append('\n');
        }
        return result.toString().trim();
    }

    private void chooseTaskForTeam() {
        if (tasks.length() == 0) { new AlertDialog.Builder(this).setMessage("Create a personal task first.").setPositiveButton("OK", null).show(); return; }
        String[] names = new String[tasks.length()];
        for (int i = 0; i < tasks.length(); i++) names[i] = tasks.optJSONObject(i).optString("title", "Task");
        new AlertDialog.Builder(this).setTitle("Choose a task").setItems(names, (dialog, which) -> {
            JSONObject task = tasks.optJSONObject(which);
            call("POST", "teams/" + selectedTeamId + "/tasks", obj("task_id", task.optInt("id")), (data, error) -> {
                setNotice(error == null ? "Task shared with " + selectedTeamName + "." : error.getMessage(), error != null); render();
            });
        }).show();
    }

    private void renderSettings() {
        sectionTitle("Make Flowstate yours.", "Your personal details and account security.");
        LinearLayout profile = card(); profile.setPadding(dp(16), dp(15), dp(16), dp(15));
        profile.addView(text("Personal details", 17, INK, true));
        EditText name = field("Display name", user.optString("name", ""), false); profile.addView(name, margin(-1, dp(12), 0, 8));
        EditText email = field("Email address", user.optString("email", ""), false); email.setEnabled(false); profile.addView(email, margin(-1, 0, 0, 10));
        Button save = primary("Save profile"); save.setOnClickListener(v -> call("PATCH", "profile", obj("name", name.getText().toString().trim()), (data, error) -> {
            if (error != null) setNotice(error.getMessage(), true);
            else { user = obj("name", name.getText().toString().trim(), "email", user.optString("email"), "id", user.optInt("id")); setNotice("Your profile is up to date.", false); }
            render();
        })); profile.addView(save); body.addView(profile, margin(-1, 0, 0, 12));

        LinearLayout password = card(); password.setPadding(dp(16), dp(15), dp(16), dp(15));
        password.addView(text("Change password", 17, INK, true));
        EditText current = field("Current password", "", true); password.addView(current, margin(-1, dp(12), 0, 8));
        EditText next = field("New password (8+ characters)", "", true); password.addView(next, margin(-1, 0, 0, 8));
        EditText confirm = field("Confirm new password", "", true); password.addView(confirm, margin(-1, 0, 0, 10));
        Button change = primary("Update password"); change.setOnClickListener(v -> {
            String p = next.getText().toString();
            if (p.length() < 8 || !p.equals(confirm.getText().toString())) { setNotice("Use at least 8 characters and make both new passwords match.", true); render(); return; }
            call("POST", "auth/change-password", obj("current_password", current.getText().toString(), "new_password", p), (data, error) -> {
                setNotice(error == null ? "Password updated successfully." : error.getMessage(), error != null); render();
            });
        }); password.addView(change); body.addView(password, margin(-1, 0, 0, 13));
        Button logout = smallButton("Sign out", true); logout.setOnClickListener(v -> signOut()); body.addView(logout, margin(-1, 0, 0, 10));
    }

    private void editTask(JSONObject existing) {
        LinearLayout form = new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(3), dp(5), dp(3), dp(2));
        form.addView(text("A little clarity makes the next step easier.", 13, MUTED, false), margin(-1, 0, 0, 13));
        form.addView(text("TASK DETAILS", 10, GREEN, true), margin(-1, 0, 0, 6));
        EditText title = field("What needs doing?", existing == null ? "" : existing.optString("title", ""), false); form.addView(title, margin(-1, 0, 0, FIELD_GAP));
        EditText description = field("Add a note or next step (optional)", existing == null ? "" : existing.optString("description", ""), false); form.addView(description, margin(-1, 0, 0, FIELD_GAP));
        LinearLayout categoryRow = new LinearLayout(this); categoryRow.setGravity(Gravity.CENTER_VERTICAL);
        EditText category = field("Category", existing == null ? "Personal" : existing.optString("category", "Personal"), false);
        categoryRow.addView(category, new LinearLayout.LayoutParams(0, -2, 1));
        String[] allStatuses = {"backlog", "in_progress", "blocked", "completed"};
        ArrayList<String> allowedStatuses = new ArrayList<>();
        String currentStatus = existing == null ? "backlog" : existing.optString("status", "backlog");
        if (existing == null) { for (String value : allStatuses) allowedStatuses.add(value); }
        else if ("backlog".equals(currentStatus)) { allowedStatuses.add("backlog"); allowedStatuses.add("in_progress"); }
        else if ("in_progress".equals(currentStatus)) { allowedStatuses.add("in_progress"); allowedStatuses.add("backlog"); allowedStatuses.add("blocked"); allowedStatuses.add("completed"); }
        else if ("blocked".equals(currentStatus)) { allowedStatuses.add("blocked"); allowedStatuses.add("in_progress"); allowedStatuses.add("completed"); }
        else { allowedStatuses.add("completed"); allowedStatuses.add("in_progress"); }
        String[] statusLabels = new String[allowedStatuses.size()];
        int selectedStatus = 0;
        for (int i = 0; i < allowedStatuses.size(); i++) { statusLabels[i] = statusLabel(allowedStatuses.get(i)); if (allowedStatuses.get(i).equals(currentStatus)) selectedStatus = i; }
        Spinner status = new Spinner(this); ArrayAdapter<String> statusAdapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, statusLabels);
        statusAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item); status.setAdapter(statusAdapter);
        status.setSelection(selectedStatus);
        LinearLayout.LayoutParams statusParams = new LinearLayout.LayoutParams(0, dp(FIELD_HEIGHT), 1); statusParams.setMargins(dp(8), 0, 0, 0); categoryRow.addView(status, statusParams);
        form.addView(categoryRow, margin(-1, 0, 0, FIELD_GAP));

        form.addView(text("DUE DATE", 10, GREEN, true), margin(-1, 0, 0, 6));
        EditText due = field("Choose a date (optional)", existing == null ? "" : dateOnly(existing.optString("due_date", "")), false); due.setFocusable(false); due.setCompoundDrawablesWithIntrinsicBounds(0, 0, android.R.drawable.ic_menu_my_calendar, 0); due.setOnClickListener(v -> {
            Calendar c = Calendar.getInstance();
            new DatePickerDialog(this, (picker, year, month, day) -> due.setText(String.format(Locale.US, "%04d-%02d-%02d", year, month + 1, day)), c.get(Calendar.YEAR), c.get(Calendar.MONTH), c.get(Calendar.DAY_OF_MONTH)).show();
        }); form.addView(due, margin(-1, 0, 0, FIELD_GAP));

        form.addView(text("TIME ESTIMATE", 10, GREEN, true), margin(-1, 0, 0, 3));
        form.addView(text("Plan in hours and minutes", 12, MUTED, false), margin(-1, 0, 0, 3));
        LinearLayout timeRow = new LinearLayout(this); timeRow.setGravity(Gravity.CENTER);
        NumberPicker hours = new NumberPicker(this); hours.setMinValue(0); hours.setMaxValue(48); hours.setWrapSelectorWheel(false); hours.setFormatter(v -> v + " hr");
        NumberPicker minutes = new NumberPicker(this); minutes.setMinValue(0); minutes.setMaxValue(59); minutes.setWrapSelectorWheel(true); minutes.setFormatter(v -> String.format(Locale.US, "%02d min", v));
        int originalMinutes = existing == null ? 0 : existing.optInt("estimated_minutes", 0);
        hours.setValue(originalMinutes / 60); minutes.setValue(originalMinutes % 60);
        LinearLayout.LayoutParams pickerParams = new LinearLayout.LayoutParams(0, dp(104), 1);
        timeRow.addView(hours, pickerParams); timeRow.addView(minutes, new LinearLayout.LayoutParams(0, dp(104), 1));
        form.addView(timeRow, margin(-1, 0, 0, 7));

        LinearLayout urgentCard = new LinearLayout(this); urgentCard.setGravity(Gravity.CENTER_VERTICAL); urgentCard.setPadding(dp(11), dp(3), dp(11), dp(3)); urgentCard.setBackground(round(0xfff6f7f3, 13));
        CheckBox urgent = new CheckBox(this); urgent.setText("Priority task"); urgent.setTextColor(INK); urgent.setTypeface(Typeface.DEFAULT, Typeface.BOLD); urgent.setButtonTintList(android.content.res.ColorStateList.valueOf(GREEN)); urgent.setChecked(existing != null && existing.optBoolean("urgent", false));
        urgentCard.addView(urgent); urgentCard.addView(text("  Bring this to the top of your focus.", 11, MUTED, false)); form.addView(urgentCard, margin(-1, 0, 0, 0));
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(false); scroll.addView(form);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle(existing == null ? "Plan a task" : "Shape this task")
                .setView(scroll).setNegativeButton("Cancel", null).setPositiveButton(existing == null ? "Add task" : "Save changes", null).create();
        dialog.setOnShowListener(v -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(button -> {
            if (title.getText().toString().trim().isEmpty()) { title.setError("Add a title"); return; }
            int totalMinutes = hours.getValue() * 60 + minutes.getValue();
            JSONObject payload = obj("title", title.getText().toString().trim(), "description", description.getText().toString().trim(),
                    "category", category.getText().toString().trim(), "due_date", due.getText().toString().trim(),
                    "urgency_flag", urgent.isChecked(), "status", allowedStatuses.get(status.getSelectedItemPosition()),
                    "duration_estimated", totalMinutes == 0 ? JSONObject.NULL : totalMinutes);
            String method = existing == null ? "POST" : "PATCH";
            String path = existing == null ? "tasks" : "tasks/" + existing.optInt("id");
            call(method, path, payload, (data, error) -> {
                if (error != null) setNotice(error.getMessage(), true); else setNotice(existing == null ? "Task created." : "Task updated.", false);
                render(); refreshTasks();
            });
            dialog.dismiss();
        }));
        dialog.show();
        dialog.getWindow().setBackgroundDrawable(round(CARD, 24));
        dialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(GREEN);
        dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setTextColor(MUTED);
    }

    private void confirmDelete(JSONObject task) {
        new AlertDialog.Builder(this).setTitle("Delete task?").setMessage("Delete “" + task.optString("title") + "”? This cannot be undone.")
                .setNegativeButton("Cancel", null).setPositiveButton("Delete", (d, w) -> call("DELETE", "tasks/" + task.optInt("id"), null, (data, error) -> {
                    setNotice(error == null ? "Task deleted." : error.getMessage(), error != null); render(); refreshTasks();
                })).show();
    }

    private void moveTask(JSONObject task, String status) {
        call("POST", "tasks/" + task.optInt("id") + "/move", obj("status", status), (data, error) -> {
            setNotice(error == null ? (status.equals("completed") ? "Task completed." : "Task reopened.") : error.getMessage(), error != null);
            render(); refreshTasks();
        });
    }

    private void refreshWorkspace() { refreshDashboard(); refreshTasks(); }
    private void refreshDashboard() {
        call("GET", "dashboard", null, (data, error) -> {
            if (error == null) metrics = data;
            else setNotice(error.getMessage(), true);
            render();
        });
        loadTasksSilently();
        io.execute(() -> {
            try {
                JSONObject result = api.request("GET", "history?limit=5", null);
                JSONArray updated = result.optJSONArray("items");
                main.post(() -> { if (updated != null) { history = updated; render(); } });
            } catch (Exception ignored) { }
        });
    }
    private void refreshTasks() {
        call("GET", "tasks", null, (data, error) -> {
            if (error == null) { tasks = data.optJSONArray("tasks"); if (tasks == null) tasks = new JSONArray(); }
            else setNotice(error.getMessage(), true);
            render();
        });
    }
    private void loadTasksSilently() {
        io.execute(() -> {
            try {
                JSONObject result = api.request("GET", "tasks", null);
                JSONArray updated = result.optJSONArray("tasks");
                main.post(() -> { if (updated != null) { tasks = updated; render(); } });
            } catch (Exception ignored) { }
        });
    }
    private void refreshHistory() {
        call("GET", "history?limit=100", null, (data, error) -> {
            if (error == null) { history = data.optJSONArray("items"); if (history == null) history = new JSONArray(); }
            else setNotice(error.getMessage(), true);
            render();
        });
    }
    private void refreshTeams() {
        call("GET", "teams", null, (data, error) -> {
            if (error == null) { teams = data.optJSONArray("teams"); if (teams == null) teams = new JSONArray(); }
            else setNotice(error.getMessage(), true);
            render();
        });
    }
    private void signOut() {
        call("POST", "auth/logout", new JSONObject(), (data, error) -> {
            api.clearSession(); user = null; page = "home"; authMode = "welcome"; setNotice("You’re signed out.", false); render();
        });
    }

    private void refreshCurrentPage() {
        if (user == null) return;
        switch (page) {
            case "tasks": case "board": case "calendar": refreshTasks(); break;
            case "activity": refreshHistory(); break;
            case "teams": refreshTeams(); break;
            case "settings": call("GET", "auth/me", null, (data, error) -> {
                if (error == null && data.optJSONObject("user") != null) user = data.optJSONObject("user");
                else if (error != null) setNotice("Could not refresh your profile: " + error.getMessage(), true);
                render();
            }); break;
            default: refreshDashboard();
        }
    }

    private void retrySessionRestore() {
        sessionRestoreFailed = false;
        call("GET", "auth/me", null, (data, error) -> {
            if (error != null) {
                if (error instanceof ApiClient.ApiException && ((ApiClient.ApiException) error).status == 401) {
                    api.clearSession(); authMode = "welcome"; sessionRestoreFailed = false;
                } else {
                    sessionRestoreFailed = true;
                    setNotice("Still offline. Your saved session is safe; try again when connected.", true);
                }
            } else {
                sessionRestoreFailed = false; user = data.optJSONObject("user"); page = "home"; notice = ""; refreshWorkspace();
            }
            render();
        });
    }

    private void renderSessionRecovery() {
        LinearLayout center = new LinearLayout(this); center.setOrientation(LinearLayout.VERTICAL);
        center.setGravity(Gravity.CENTER); center.setPadding(dp(28), dp(30), dp(28), dp(30));
        root.addView(center, new LinearLayout.LayoutParams(-1, -1));
        TextView mark = text("↻", 25, GREEN, true); mark.setGravity(Gravity.CENTER); mark.setBackground(round(0xffe3eee5, 22));
        center.addView(mark, new LinearLayout.LayoutParams(dp(58), dp(58)));
        center.addView(text("Your workspace is saved.", 23, INK, true), margin(-1, dp(18), 0, 7));
        TextView detail = text("We couldn’t reach Flowstate just now. Your sign-in is still saved on this device.", 14, MUTED, false);
        detail.setGravity(Gravity.CENTER); center.addView(detail, margin(-1, 0, 0, 17));
        Button retry = primary("Try again"); retry.setOnClickListener(v -> retrySessionRestore()); center.addView(retry, new LinearLayout.LayoutParams(-1, dp(50)));
        Button welcome = linkButton("Continue to welcome"); welcome.setOnClickListener(v -> { sessionRestoreFailed = false; render(); });
        center.addView(welcome, margin(-1, dp(10), 0, 0));
    }

    private void confirmSignOut() {
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Sign out of Flowstate?")
                .setMessage("Your tasks stay safe in your account. You can sign back in any time.")
                .setNegativeButton("Stay here", null).setPositiveButton("Sign out", (d, w) -> signOut()).create();
        dialog.show();
        dialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(0xffa63f35);
        dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setTextColor(GREEN);
        if (dialog.getWindow() != null) dialog.getWindow().setBackgroundDrawable(round(CARD, 24));
    }

    private void prompt(String title, String hint, java.util.function.Consumer<String> onSubmit) {
        EditText input = field(hint, "", false);
        new AlertDialog.Builder(this).setTitle(title).setView(input).setNegativeButton("Cancel", null)
                .setPositiveButton("Continue", (dialog, which) -> {
                    String value = input.getText().toString().trim();
                    if (!value.isEmpty()) onSubmit.accept(value);
                }).show();
    }

    private void sectionTitle(String title, String subtitle) {
        body.addView(text(title, 24, INK, true), margin(-1, dp(3), 0, 4));
        body.addView(text(subtitle, 13, MUTED, false), margin(-1, 0, 0, 13));
    }

    private LinearLayout emptyCard(String title, String subtitle) {
        LinearLayout box = card(); box.setPadding(dp(16), dp(16), dp(16), dp(16));
        box.addView(text(title, 15, INK, true)); box.addView(text(subtitle, 12, MUTED, false), margin(-1, dp(5), 0, 0));
        return box;
    }

    private LinearLayout card() {
        LinearLayout box = new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL);
        box.setBackground(round(CARD, 15)); box.setElevation(dp(1)); return box;
    }

    private EditText field(String hint, String value, boolean password) {
        EditText input = new EditText(this);
        input.setSingleLine(!hint.equals("Description"));
        if (hint.equals("Description")) { input.setSingleLine(false); input.setMinLines(2); input.setGravity(Gravity.TOP); }
        input.setTextSize(14); input.setTextColor(INK); input.setHintTextColor(0xff8a958e); input.setHint(hint); input.setMinHeight(dp(FIELD_HEIGHT));
        input.setPadding(dp(12), dp(10), dp(12), dp(10)); input.setBackground(round(CARD, 10)); input.setBackgroundTintList(null);
        input.setText(value == null || "null".equals(value) ? "" : value);
        if (password) input.setInputType(129);
        return input;
    }

    private Button primary(String label) {
        Button b = button(label, GREEN, CARD, true); b.setMinHeight(dp(PRIMARY_BUTTON_HEIGHT)); return b;
    }
    private Button smallButton(String label, boolean danger) {
        return button(label, danger ? 0xffffefec : 0xffedf3ed, danger ? 0xffa63f35 : GREEN, true);
    }
    private Button linkButton(String label) { return button(label, BG, GREEN, false); }
    private Button navButton(String label, boolean active) { return button(label, active ? 0xffe6f1e8 : CARD, active ? GREEN : MUTED, active); }
    private Button button(String label, int background, int foreground, boolean bold) {
        Button b = new Button(this); b.setText(label); b.setTextColor(foreground); b.setTextSize(13); b.setAllCaps(false);
        b.setTypeface(Typeface.DEFAULT, bold ? Typeface.BOLD : Typeface.NORMAL); b.setPadding(dp(10), dp(5), dp(10), dp(5));
        b.setBackground(new RippleDrawable(ColorStateList.valueOf(0x26000000), round(background, 14), round(CARD, 14)));
        b.setMinHeight(dp(BUTTON_HEIGHT));
        if (loading) { b.setEnabled(false); b.setAlpha(.65f); }
        return b;
    }
    private TextView text(String value, int size, int color, boolean bold) {
        TextView t = new TextView(this); t.setText(value); t.setTextSize(size); t.setTextColor(color);
        if (bold) t.setTypeface(Typeface.DEFAULT, Typeface.BOLD); t.setIncludeFontPadding(true); return t;
    }
    private GradientDrawable round(int color, int radius) {
        GradientDrawable d = new GradientDrawable(); d.setColor(color); d.setCornerRadius(dp(radius));
        if (color == CARD) d.setStroke(dp(1), BORDER); return d;
    }
    private LinearLayout.LayoutParams margin(int width, int height, int left, int bottom) {
        // Most rows use intrinsic text/input height; spacing is controlled by the bottom margin.
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(width, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.setMargins(dp(left), 0, dp(left), dp(bottom)); return p;
    }
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private static String first(String value) { return value == null || value.trim().isEmpty() ? "F" : value.trim().substring(0, 1).toUpperCase(Locale.getDefault()); }
    private String statusLabel(String status) {
        if ("in_progress".equals(status)) return "In progress";
        if ("completed".equals(status)) return "Completed";
        if ("blocked".equals(status)) return "Blocked";
        return "Backlog";
    }
    private static String dateOnly(String value) { return value == null || "null".equals(value) ? "" : value.substring(0, Math.min(10, value.length())); }
    private JSONObject obj(Object... pairs) {
        try { return ApiClient.json(pairs); } catch (Exception ignored) { return new JSONObject(); }
    }
    private void setNotice(String value, boolean isError) { notice = value == null ? "" : value; noticeError = isError; }

    private interface StringChanged { void change(String value); }
    private android.text.TextWatcher watcher(StringChanged changed) {
        return new android.text.TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { changed.change(s.toString()); }
            @Override public void afterTextChanged(android.text.Editable s) { }
        };
    }
}
