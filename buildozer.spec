[app]
# (str) Название приложения (отображается на телефоне)
title = Журнал посещаемости

# (str) Имя пакета (только латиница, без пробелов!)
package.name = journal

# (str) Домен пакета (только латиница)
package.domain = com.jour

# (str) Папка с исходным кодом (точка = текущая папка)
source.dir = .

# (list) Какие файлы включать в сборку
source.include_exts = py,png,jpg,kv,atlas

# (str) Версия приложения
version = 1.0

# (list) Зависимости приложения
# python3 и kivy — обязательны
requirements = python3,kivy

# (str) Иконка приложения (файл .png в папке проекта)
icon.filename = %(source.dir)s/icon.png

# (str) Ориентация экрана: portrait, landscape или all
orientation = portrait

# (bool) Запускать в полноэкранном режиме
fullscreen = 0

# (list) Разрешения Android
# INTERNET — нужен для связи с сервером jour.pythonanywhere.com
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# (int) Целевая версия Android API
android.api = 33

# (int) Минимальная поддерживаемая версия Android API
android.minapi = 21

# (str) Версия Android NDK (ОБЯЗАТЕЛЬНО для стабильной сборки)
android.ndk = 25b

# (int) Версия Android NDK API
android.ndk_api = 21

# (list) Архитектуры. Оставлена только arm64-v8a для экономии памяти и времени
android.archs = arm64-v8a

# (str) Имя Python-скрипта с приложением (точка входа)
# По умолчанию ищет main.py в source.dir

[buildozer]
# (int) Уровень логирования: 0 = ошибки, 1 = инфо, 2 = детально
log_level = 2

# (int) Предупреждать при запуске от root
warn_on_root = 1
