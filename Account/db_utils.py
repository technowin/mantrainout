# myapp/db_utils.py

from django.db import connections

class Db:
    @staticmethod
    def get_connection(database_alias='default'):
        """
        Get the database connection based on the alias provided ('default').
        """
        return connections["default"]

    @staticmethod
    def close_connection(database_alias='default'):
        """
        Close the database connection if it's open.
        """
        connection = connections["default"]
        
def callproc(procedure_name, params=None):
    """
    Calls the specified stored procedure on the selected database.
    """
    connection = Db.get_connection()
    try:
        fetched_data=[]
        with connection.cursor() as cursor:
            cursor.callproc(procedure_name, params)
            for result in cursor.stored_results():
                fetched_data = result.fetchall()
            connection.commit()
            return fetched_data
    except Exception as e:
        connection.rollback()
        print(f"Error: {e}")
        raise
    finally:
        Db.close_connection()

