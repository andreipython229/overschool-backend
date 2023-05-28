# Git
## Для корректного отображения истории коммитов и сообщений необходимо установить параметры пользователя:
```
$ git config --global user.name '<Name Surname>'
$ git config --local user.email '<Email address>'
```

# Redis
## Привязан к общему Redis контейнеру

## Запуск приложения локально:
```
$ huey_consumer.py config.main.huey
```
## Восстанавливает базу данных PostgreSQL из файла дампа:
```
$ pg_restore -h {{host}} -p {{port}} -d {{db_name}} {{archive_file.dump}}
```
Выполнение команды запросит ввести пароль для базы данных.

Для того что бы отчистить базу данных перед восстановлением нужно добавить флаг "--clean"
