#!/bin/bash
# Скрипт сборки JamSpell и запуска HTTP-сервиса внутри WSL2
# Запуск из Windows: wsl bash -c "./wsl_service/build.sh"

set -e

echo "=== Building JamSpell in WSL2 ==="

# 1. Установка зависимостей
echo "[1/5] Установка зависимостей..."
sudo apt-get update -qq
sudo apt-get install -y -qq cmake swig3 build-essential git wget python3-dev > /dev/null 2>&1

# 2. Клонирование репозитория JamSpell
JAMSPELL_DIR="$HOME/jamspell_src"
if [ ! -d "$JAMSPELL_DIR" ]; then
    echo "[2/5] Клонирование репозитория bakwc/JamSpell..."
    git clone --depth 1 https://github.com/bakwc/JamSpell.git "$JAMSPELL_DIR"
else
    echo "[2/5] Репозиторий JamSpell уже существует."
fi

# 3. Сборка JamSpell
echo "[3/5] Сборка JamSpell через cmake..."
cd "$JAMSPELL_DIR"
mkdir -p build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# 4. Скачивание моделей
MODELS_DIR="$HOME/jamspell_models"
mkdir -p "$MODELS_DIR"

echo "[4/5] Скачивание моделей (ru.bin, en.bin)..."
# Модели JamSpell
RU_MODEL_URL="https://raw.githubusercontent.com/bakwc/JamSpell/master/models/ru.bin"
EN_MODEL_URL="https://raw.githubusercontent.com/bakwc/JamSpell/master/models/en.bin"

if [ ! -f "$MODELS_DIR/ru.bin" ]; then
    wget -O "$MODELS_DIR/ru.bin" "$RU_MODEL_URL" || echo "WARNING: Не удалось скачать ru.bin"
fi

if [ ! -f "$MODELS_DIR/en.bin" ]; then
    wget -O "$MODELS_DIR/en.bin" "$EN_MODEL_URL" || echo "WARNING: Не удалось скачать en.bin"
fi

# 5. Запуск веб-сервера
echo "[5/5] Запуск веб-серверов..."
WEB_SERVER_BIN="$JAMSPELL_DIR/build/web_server/web_server"

if [ ! -f "$WEB_SERVER_BIN" ]; then
    echo "ERROR: Веб-сервер не найден: $WEB_SERVER_BIN"
    exit 1
fi

# Запускаем русский сервис на порту 8080
echo "Запуск RU сервиса на порту 8080..."
$WEB_SERVER_BIN "$MODELS_DIR/ru.bin" 0.0.0.0 8080 &

# Запускаем английский сервис на порту 8081
echo "Запуск EN сервиса на порту 8081..."
$WEB_SERVER_BIN "$MODELS_DIR/en.bin" 0.0.0.0 8081 &

echo "Сервисы запущены!"
wait
