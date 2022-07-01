# Ссылки по установке

- [docker-compose](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04-ru)
- [docker](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04-ru)
- [git](https://www.digitalocean.com/community/tutorials/how-to-install-git-on-ubuntu-20-04-ru)

# Команды для докера

`docker-compose up` - запуск и перезапуск всех служб, определенных в docker-compose.yml.

`docker-compose down` - команда остановит запуск контейнеров, но она также удаляет остановленные контейнеры, а также любые созданные сети. Вы можете сделать еще один шаг и добавить флаг -v, чтобы удалить все тома. Это отлично подходит для выполнения полного сброса в вашей среде путем запуска `docker-compose down -v`.

`docker-compose start` - команда перезапустит только контейнеры, остановленные ранее.

`docker-compose stop` - команда остановит запуск контейнеров, но не удалит их.

# Данные для входа в PgAdmin4

**Логин** `it@overone.by`

**Пароль** `overone`

**Порт** `8080`

# Данные postgres

**Имя пользователя** `root`

**Пароль** `overone`

**Порт** `5432`