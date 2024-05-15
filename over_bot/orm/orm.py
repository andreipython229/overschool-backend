from sqlalchemy import insert, select, desc
from db.database import session_maker, meta


class TgORM:

    @staticmethod
    def select_user_in_db(email):
        with session_maker() as session:
            db_users = meta.tables['users_user']
            query = (
                select(db_users)
                .filter(db_users.c.email == email)
            )
            res = session.execute(query)
            result = res.unique().first().id
            return result

    @staticmethod
    def insert_user_in_db_tg_users(tg_user_id, first_name, user_id):
        with session_maker() as session:
            db_tg_users = meta.tables['tg_notifications_tgusers']

            query_user = (select(db_tg_users.c.tg_user_id))
            res_user = session.execute(query_user)
            result_user = res_user.unique().all()
            print(result_user)
            print((f'{tg_user_id}',) in result_user)

            if (f'{tg_user_id}',) not in result_user:
                tg_user = [{
                    "tg_user_id": tg_user_id,
                    "first_name": f"{first_name}",
                    "user_id": user_id
                }]

                insert_tg_user = insert(db_tg_users).values(tg_user)
                session.execute(insert_tg_user)
                session.commit()
                return 'Верификация пройдена успешно!'
            else:
                return 'Верификация уже пройдена!'

    @staticmethod
    def insert_user_in_db_tg_notifications():
        with session_maker() as session:
            db_tg_notifications = meta.tables['tg_notifications_notifications']
            db_tg_users = meta.tables['tg_notifications_tgusers']

            query = (
                select(db_tg_users)
                .order_by(desc(db_tg_users.c.id))
            )
            res = session.execute(query)
            tg_user_id = res.first()
            print(tg_user_id[0])

            notification = [{
                "homework_notifications": True,
                "messages_notifications": False,
                "tg_user_id": tg_user_id[0],
                "completed_courses_notifications": True
            }]
            insert_tg_notifications = insert(db_tg_notifications).values(notification)
            session.execute(insert_tg_notifications)
            session.commit()




























