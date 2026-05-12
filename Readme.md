Каюмов Альберт Фанисович 
6310
Курсовая работа

Работа с ботом:
# 1. Клонирование репозитория
    sudo apt install git -y        - установка git, если нет
    git clone https://github.com/твой_логин/currency_telegram_bot.git
    cd currency_telegram_bot

# 2. Создание .env файла

В файле .env укажите токен вашего Telegram‑бота по примеру:
    nano .env
"BOT_TOKEN=ваш_токен_от_BotFather"

Конфигурация:
history.db – файл базы данных, создаётся автоматически при первом запуске.
requirements.txt – зависимости для ручного запуска.
Dockerfile – образ для контейнеризации.

# 3. Запуск через Docker

Убедитесь, что Docker установлен:
    docker --version

Если Docker не установлен на Виртуальной машине:

    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    
После этого перезапускаем/перезаходим 
    exit -> ssh ....

Сборка образа

    docker build -t currency-bot .

Первый запуск контейнера

    docker run -d --name currency-bot --restart unless-stopped -v $(pwd)/history.db:/app/history.db --env-file .env currency-bot

--restart unless-stopped – автоматический перезапуск (кроме случая, когда остановлено вручную).
-v – монтирование файла БД на хост (важно для сохранения истории).
--env-file – передача переменных из .env.

# Возможные команды через Docker
  Команда                               Действие
    docker ps -a	                      Показать все контейнеры (включая остановленные)
    docker start currency-bot	          Запустить остановленный контейнер
    docker stop currency-bot	          Остановить работающий контейнер
    docker restart currency-bot	          Перезапустить контейнер
    docker logs currency-bot	          Посмотреть логи
    docker logs -f currency-bot	          Логи в реальном времени
    docker rm currency-bot	              Удалить контейнер (перед этим остановите)