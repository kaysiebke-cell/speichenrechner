package de.speichenrechner.app

import android.os.Build
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.webkit.WebSettingsCompat
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewFeature

/**
 * Hüllt die Web-Fassung in eine Android-App – nicht mehr als das.
 *
 * Die Dateien aus `public/` liegen als Assets in der App; der Build kopiert
 * sie dorthin (siehe `app/build.gradle`). Gerechnet wird auf dem Gerät, es
 * gibt keine Netz-Berechtigung und keinen Server.
 *
 * Geladen wird **nicht** über `file://`, sondern über den
 * [WebViewAssetLoader] unter einer echten https-Adresse. Das ist nötig, weil
 * die Anwendung ES-Module benutzt (`import` in app.js): unter `file://`
 * verweigert der WebView die – dort gilt jede Datei als eigener Ursprung.
 * Aus demselben Grund funktioniert so auch der Service Worker.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    /** Virtuelle Adresse, unter der die Assets erscheinen. */
    private val startseite =
        "https://appassets.androidplatform.net/assets/www/index.html"

    override fun onCreate(zustand: Bundle?) {
        super.onCreate(zustand)

        val laden = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView = WebView(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT,
            )
            settings.javaScriptEnabled = true
            // Für localStorage – die App behält die zuletzt eingegebenen Werte.
            settings.domStorageEnabled = true
            settings.allowFileAccess = false
            settings.allowContentAccess = false
            // Die Seite bringt ihr eigenes Layout mit; kein Hineinzoomen nötig.
            settings.builtInZoomControls = false
            settings.textZoom = 100

            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(
                    ansicht: WebView,
                    anfrage: WebResourceRequest,
                ): WebResourceResponse? = laden.shouldInterceptRequest(anfrage.url)
            }
        }

        // Dunkelmodus: die Seite wertet prefers-color-scheme aus, dafür muss der
        // WebView die Einstellung des Geräts weitergeben.
        if (WebViewFeature.isFeatureSupported(WebViewFeature.ALGORITHMIC_DARKENING)) {
            WebSettingsCompat.setAlgorithmicDarkeningAllowed(webView.settings, true)
        }

        setContentView(webView)

        if (zustand == null) {
            webView.loadUrl(startseite)
        } else {
            webView.restoreState(zustand)
        }

        // Zurück-Taste blättert in der Seite, statt die App gleich zu schließen.
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
    }

    override fun onSaveInstanceState(zustand: Bundle) {
        super.onSaveInstanceState(zustand)
        webView.saveState(zustand)
    }

    override fun onDestroy() {
        // Auf älteren Fassungen hält ein WebView sonst die Activity fest.
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            webView.destroy()
        }
        super.onDestroy()
    }
}
