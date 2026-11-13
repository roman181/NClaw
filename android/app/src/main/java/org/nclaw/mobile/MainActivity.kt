package org.nclaw.mobile

import android.app.Activity
import android.os.Bundle
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.TextView
import android.widget.LinearLayout
import android.graphics.Color
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlin.concurrent.thread

class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var web: WebView
    @Volatile private var started = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(10, 16, 28))
        }
        status = TextView(this).apply {
            text = "NClaw wird gestartet …"
            setTextColor(Color.WHITE)
            textSize = 14f
            setPadding(18, 14, 18, 14)
        }
        web = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = false
            settings.allowContentAccess = false
            webViewClient = WebViewClient()
            webChromeClient = WebChromeClient()
        }
        root.addView(status)
        root.addView(web, LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(root)
        startBackend()
    }

    private fun startBackend() {
        thread(name = "nclaw-python") {
            try {
                if (!Python.isStarted()) Python.start(AndroidPlatform(this))
                val py = Python.getInstance()
                py.getModule("os").get("environ")?.asMap()
                py.getModule("os").callAttr("environ", "get", "HOME")
                py.getModule("os").callAttr("makedirs", filesDir.absolutePath + "/.nclaw", "exist_ok")
                py.getModule("os").get("environ").set("NCLAW_DATA_DIR", filesDir.absolutePath + "/.nclaw")
                py.getModule("dashboard.server").callAttr("main")
            } catch (error: Throwable) {
                runOnUiThread { status.text = "NClaw-Backend konnte nicht starten: ${error.message}" }
            }
        }
        thread(name = "nclaw-webview-start") {
            repeat(30) {
                try {
                    val connection = java.net.URL("http://127.0.0.1:8765/api/status").openConnection() as java.net.HttpURLConnection
                    connection.connectTimeout = 500
                    connection.readTimeout = 500
                    if (connection.responseCode == 200) {
                        connection.disconnect()
                        runOnUiThread {
                            status.text = "NClaw läuft lokal auf diesem Gerät"
                            web.loadUrl("http://127.0.0.1:8765/")
                        }
                        started = true
                        return@thread
                    }
                    connection.disconnect()
                } catch (_: Exception) { }
                Thread.sleep(500)
            }
            runOnUiThread { status.text = "Backend startet nicht. Bitte App neu öffnen." }
        }
    }

    override fun onBackPressed() {
        if (::web.isInitialized && web.canGoBack()) web.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        if (::web.isInitialized) web.destroy()
        super.onDestroy()
    }
}
