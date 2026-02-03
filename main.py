import os
import threading
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.utils import platform

# Import the existing Flask app
# We assume app.py is in the same directory and has an 'app' object
from app import app as flask_app

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = app
        self.daemon = True

    def run(self):
        # We need to run on localhost for the WebView to access it
        # Disable debug mode for production/Android to avoid auto-reloader issues
        self.server.run(host="127.0.0.1", port=5000, debug=False)

class ImageSearchApp(App):
    def build(self):
        # Start the Flask server
        self.server_thread = ServerThread(flask_app)
        self.server_thread.start()
        
        # Give the server a moment to start
        # In a real production app, you might want to poll the port
        time.sleep(1) 
        
        # Create a placeholder widget
        self.root_widget = Widget()
        
        # Schedule the WebView creation
        Clock.schedule_once(self.create_webview, 0)
        return self.root_widget

    def create_webview(self, *args):
        if platform == 'android':
            from jnius import autoclass
            from android.runnable import run_on_ui_thread

            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            activity = autoclass('org.kivy.android.PythonActivity').mActivity

            @run_on_ui_thread
            def start_webview():
                webview = WebView(activity)
                webview.setWebViewClient(WebViewClient())
                webview.getSettings().setJavaScriptEnabled(True)
                webview.getSettings().setDomStorageEnabled(True)
                
                # Load the local Flask server
                webview.loadUrl('http://127.0.0.1:5000')
                
                # Add to the activity
                activity.setContentView(webview)
                
            start_webview()
        else:
            # Fallback for desktop testing (prints message only)
            print("Not running on Android. WebView would be created here pointing to http://127.0.0.1:5000")
            print("Please open your browser to http://127.0.0.1:5000 for local testing.")

    def on_stop(self):
        # Clean up if needed
        pass

if __name__ == '__main__':
    ImageSearchApp().run()
