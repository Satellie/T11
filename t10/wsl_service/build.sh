#!/bin/bash
# Скрипт сборки JamSpell и запуска HTTP-сервиса внутри WSL2

set -e

echo "=== Building JamSpell in WSL2 ==="

# TODO: Добавить команды для:
# 1. Клонирования репозитория JamSpell (если не клонирован)
# 2. Установки зависимостей (cmake, swig, python-dev)
# 3. Сборки библиотеки
# 4. Запуска HTTP-сервера на порту 8080

echo "TODO: Реализовать сборку JamSpell по официальной инструкции"
echo "https://github.com/bakwc/JamSpell"

# Примерная структура (раскомментировать и доработать при реализации):
# git clone https://github.com/bakwc/JamSpell.git || true
# cd JamSpell
# mkdir build && cd build
# cmake ..
# make
# sudo make install
# python3 web_server.py &

echo "JamSpell service should be running on http://127.0.0.1:8080"
