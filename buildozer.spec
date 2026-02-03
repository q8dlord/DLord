[app]

# (str) Title of your application
title = Image Search

# (str) Version of your application
version = 0.1

# (str) Package name
package.name = imagesearch

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,html,css,js,txt

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,flask,requests,android,jnius,openssl,sqlite3

# (str) Custom source folders to include in the package
# source.include_patterns = assets/*,images/*.png

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible (usually 33+)
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (list) List of service to declare
# services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

# (str) The main.py file name
# main.py = main.py

# (list) List of Java classes to add to the compilation
# android.add_jars = foo.jar,bar.jar,common/one.jar

# (list) List of Java files to add to the android project (can be java or a
# directory containing the files)
# android.add_src =

# (list) Android AAR archives to add
# android.add_aars =

# (list) Gradle dependencies to add
# android.gradle_dependencies =

# (bool) Use the local p4a (python-for-android) instead of downloading it
# p4a.source_dir =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
