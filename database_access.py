import sqlite3
from typing import List, Tuple, Optional

class DatabaseAccess:
    def __init__(self, db_path: str = "db_path/issues_database.sqlite"):
        """Initialize database connection."""
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            raise Exception(f"Error connecting to database: {e}")

    def get_all_mids(self) -> List[str]:
        """
        Retrieve all M_IDs from the database.
        
        Returns:
            List[str]: List of all M_IDs
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT M_ID FROM issues")
            mids = [str(row[0]) for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return mids
        except sqlite3.Error as e:
            raise Exception(f"Error retrieving M_IDs: {e}")

    def get_issue_details(self, mid: str) -> Optional[Tuple[str, str]]:
        """
        Retrieve Title and Description for a specific M_ID.
        
        Args:
            mid (str): The M_ID to look up
            
        Returns:
            Optional[Tuple[str, str]]: Tuple of (Title, Description) if found, None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT Title, Description FROM issues WHERE M_ID = ?",
                (mid,)
            )
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result if result else None
        except sqlite3.Error as e:
            raise Exception(f"Error retrieving issue details for M_ID {mid}: {e}") 

# if __name__ == "__main__":
#     db = DatabaseAccess()
#     print(db.get_all_mids())
#     print(db.get_issue_details("MOLY00436685"))
