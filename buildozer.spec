[app]

# (str) Title of your application
title = Image Search

# (str) Package name
package.name = imagesearch

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,html,css,js,txt

# (str) Application versioning
version = 0.1

# (list) Application requirements
# I kept your exact list here
requirements = python3,kivy,flask,requests,duckduckgo_search==5.3.1,android,jnius,certifi,urllib3,idna,charset_normalizer,brotli,click,itsdangerous,jinja2,markupsafe,werkzeug,lxml,platformdirs

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible (usually 33+)
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) The Android arch to build for
android.archs = arm64-v8a

# (bool) Accept SDK license agreements automatically
android.accept_sdk_license = True

# (str) Android Build Tools version to use (THIS IS THE FIX)
# We force version 34.0.0 because version 36 is breaking the build
android.build_tools_version = 34.0.0

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
