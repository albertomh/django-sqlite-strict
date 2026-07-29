from django.db import connection


def non_strict_tables():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM pragma_table_list "
            "WHERE schema = 'main' AND type = 'table' "
            "AND NOT strict AND name NOT LIKE 'sqlite\\_%' ESCAPE '\\'"
        )
        return [row[0] for row in cursor.fetchall()]
