import psycopg2
import psycopg2.extras


class DBHandler:
    def __init__(self, **kwargs) -> None:
        self.user = kwargs["USER"]
        self.password = kwargs["PASSWORD"]
        self.host = kwargs["HOST"]
        self.port = kwargs["PORT"]
        self.database = kwargs["NAME"]

    def execute_query(self, query: str, *params):
        with psycopg2.connect(
            user=self.user, password=self.password, host=self.host, port=self.port, database=self.database
        ) as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, (params))
                return cursor.fetchall()
