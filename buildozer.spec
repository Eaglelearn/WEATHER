[app]
title = Weather Forecast
package.name = weatherforecast
package.domain = org.spaceexplorer

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0.0

requirements = python3,kivy==2.2.1,plyer,certifi

orientation = portrait

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION
android.api = 30
android.minapi = 21
android.ndk = 23b
android.sdk = 30
android.gradle_dependencies = 
android.manifest.extra = 
android.allow_backup = True
