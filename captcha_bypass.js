/**
 * 美团验证码 Bypass Frida Script
 * 策略：
 * 1. Hook WebView 的 JS → Native 接口（captcha 验证结果回传）
 * 2. Hook YodaRouter 的 Activity 回调（直接注入验证通过）
 * 3. Hook mtguard 验证接口
 */

'use strict';

console.log("[Captcha Bypass] 初始化...");

// ── 工具函数 ─────────────────────────────────────────────────
function tryHook(name, fn) {
    try {
        fn();
        console.log("[✓] " + name);
    } catch(e) {
        console.log("[✗] " + name + ": " + e.message);
    }
}

// ── 等待 Java 就绪 ────────────────────────────────────────────
Java.perform(function() {

    // ── 1. Hook WebView.evaluateJavascript / loadUrl ──────────────
    // 美团 WebView 验证码通过后会调用 JS 通知 Native
    tryHook("WebView.evaluateJavascript", function() {
        var WebView = Java.use("android.webkit.WebView");
        WebView.evaluateJavascript.overload("java.lang.String", "android.webkit.ValueCallback")
            .implementation = function(script, callback) {
            // 拦截验证结果上报的 JS 调用
            if (script && (
                script.indexOf("captcha") !== -1 ||
                script.indexOf("verify") !== -1 ||
                script.indexOf("slider") !== -1 ||
                script.indexOf("success") !== -1
            )) {
                console.log("[WebView] JS: " + script.substring(0, 120));
            }
            return this.evaluateJavascript(script, callback);
        };
    });

    // ── 2. Hook YodaRouter — 美团验证码容器 Activity ─────────────
    tryHook("YodaRouterActivity onResult", function() {
        var classes = Java.enumerateLoadedClassesSync();
        var yodaClasses = classes.filter(function(c) {
            return c.indexOf("yoda") !== -1 || c.indexOf("Yoda") !== -1;
        });
        console.log("[Yoda] 找到 " + yodaClasses.length + " 个 Yoda 类:");
        yodaClasses.forEach(function(c) { console.log("  " + c); });
    });

    // ── 3. Hook 美团 OneID / mtguard 验证接口 ────────────────────
    // mtguard 的 SecurityTokenHelper 控制风控 token
    tryHook("SecurityTokenHelper", function() {
        var STH = Java.use("com.meituan.android.common.mtguard.SecurityTokenHelper");
        // 拦截验证请求，返回 mock token
        if (STH.getSecurityToken) {
            STH.getSecurityToken.implementation = function() {
                console.log("[mtguard] getSecurityToken called -> returning mock");
                return "bypass_token_" + Date.now();
            };
        }
    });

    // ── 4. Hook Android WebView 的 shouldOverrideUrlLoading ──────
    // 验证码页面通常通过 URL scheme 回传结果
    tryHook("WebViewClient.shouldOverrideUrlLoading", function() {
        var WebViewClient = Java.use("android.webkit.WebViewClient");
        WebViewClient.shouldOverrideUrlLoading.overload(
            "android.webkit.WebView", "android.webkit.WebResourceRequest"
        ).implementation = function(view, request) {
            var url = request.getUrl().toString();
            if (url.indexOf("captcha") !== -1 || url.indexOf("verify") !== -1 || url.indexOf("yoda") !== -1) {
                console.log("[WebViewClient] intercepted URL: " + url);
            }
            return this.shouldOverrideUrlLoading(view, request);
        };
    });

    // ── 5. Hook addJavascriptInterface —— 捕获 JS→Native 桥 ──────
    tryHook("WebView.addJavascriptInterface", function() {
        var WebView = Java.use("android.webkit.WebView");
        WebView.addJavascriptInterface.implementation = function(obj, name) {
            console.log("[WebView] addJavascriptInterface: name=" + name +
                        " cls=" + Java.cast(obj, Java.use("java.lang.Object")).getClass().getName());
            return this.addJavascriptInterface(obj, name);
        };
    });

    // ── 6. Hook Activity.onActivityResult ─────────────────────────
    // 验证码 Activity 关闭时通过 onActivityResult 传递结果
    tryHook("Activity.onActivityResult", function() {
        var Activity = Java.use("android.app.Activity");
        Activity.onActivityResult.implementation = function(requestCode, resultCode, data) {
            console.log("[Activity] onActivityResult: requestCode=" + requestCode +
                        " resultCode=" + resultCode);
            return this.onActivityResult(requestCode, resultCode, data);
        };
    });

    console.log("[Captcha Bypass] Hook 安装完毕，监控中...");
});
