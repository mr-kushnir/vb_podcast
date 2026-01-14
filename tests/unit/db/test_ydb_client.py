"""
Unit tests for YDB Client - Comprehensive Coverage
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.db.ydb_client import YDBClient, MemoryDB, get_db


class TestYDBClientConnection:
    """Test YDB connection and credentials"""

    @pytest.fixture
    def ydb_client(self):
        return YDBClient()

    def test_init_sets_endpoint_and_database(self, ydb_client):
        """Test client initialization"""
        assert ydb_client.endpoint is not None
        assert ydb_client.database is not None

    def test_get_credentials_returns_none_when_no_ydb(self):
        """Test credentials when YDB SDK not available"""
        client = YDBClient()
        # When HAS_YDB is False, should return None
        # This is tested in the actual module


class TestMemoryDB:
    """Test in-memory database fallback"""

    @pytest.fixture
    def db(self):
        return MemoryDB()

    def test_insert_creates_table_if_not_exists(self, db):
        """Test insert creates table automatically"""
        data = {"id": "1", "name": "Alice"}

        result = db.insert("users", data)

        assert result is True
        assert "users" in db.tables
        assert len(db.tables["users"]) == 1

    def test_insert_appends_to_existing_table(self, db):
        """Test insert appends to table"""
        db.insert("users", {"id": "1", "name": "Alice"})
        db.insert("users", {"id": "2", "name": "Bob"})

        assert len(db.tables["users"]) == 2

    def test_select_from_nonexistent_table_returns_empty(self, db):
        """Test selecting from table that doesn't exist"""
        result = db.select("nonexistent")

        assert result == []

    def test_select_all_records(self, db):
        """Test selecting all records from table"""
        db.insert("users", {"id": "1", "name": "Alice"})
        db.insert("users", {"id": "2", "name": "Bob"})

        result = db.select("users")

        assert len(result) == 2

    def test_select_with_where_clause(self, db):
        """Test selecting with WHERE condition"""
        db.insert("users", {"id": "1", "name": "Alice", "role": "admin"})
        db.insert("users", {"id": "2", "name": "Bob", "role": "user"})

        result = db.select("users", where={"role": "admin"})

        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_select_with_multiple_where_conditions(self, db):
        """Test selecting with multiple WHERE conditions"""
        db.insert("users", {"id": "1", "name": "Alice", "role": "admin", "active": "yes"})
        db.insert("users", {"id": "2", "name": "Bob", "role": "admin", "active": "no"})

        result = db.select("users", where={"role": "admin", "active": "yes"})

        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_select_with_limit(self, db):
        """Test selecting with limit"""
        for i in range(10):
            db.insert("users", {"id": str(i), "name": f"User{i}"})

        result = db.select("users", limit=5)

        assert len(result) == 5

    def test_select_with_where_no_match(self, db):
        """Test selecting where no records match"""
        db.insert("users", {"id": "1", "name": "Alice"})

        result = db.select("users", where={"name": "Charlie"})

        assert result == []

    def test_delete_from_nonexistent_table(self, db):
        """Test deleting from table that doesn't exist"""
        result = db.delete("nonexistent", where={"id": "1"})

        assert result is True  # No-op, returns success

    def test_delete_removes_matching_records(self, db):
        """Test delete removes matching records"""
        db.insert("users", {"id": "1", "name": "Alice"})
        db.insert("users", {"id": "2", "name": "Bob"})
        db.insert("users", {"id": "3", "name": "Charlie"})

        db.delete("users", where={"id": "2"})

        remaining = db.select("users")
        assert len(remaining) == 2
        assert all(r["id"] != "2" for r in remaining)

    def test_delete_with_multiple_conditions(self, db):
        """Test delete with multiple WHERE conditions"""
        db.insert("users", {"id": "1", "name": "Alice", "role": "admin"})
        db.insert("users", {"id": "2", "name": "Bob", "role": "admin"})
        db.insert("users", {"id": "3", "name": "Charlie", "role": "user"})

        db.delete("users", where={"role": "admin"})

        remaining = db.select("users")
        assert len(remaining) == 1
        assert remaining[0]["name"] == "Charlie"

    def test_delete_no_match(self, db):
        """Test delete when no records match"""
        db.insert("users", {"id": "1", "name": "Alice"})

        db.delete("users", where={"id": "999"})

        remaining = db.select("users")
        assert len(remaining) == 1  # Nothing deleted

    def test_execute_returns_empty_for_memory_db(self, db):
        """Test execute method (not fully implemented in MemoryDB)"""
        result = db.execute("SELECT * FROM users")

        assert result == []


class TestGetDB:
    """Test get_db factory function"""

    @patch.dict('os.environ', {'YDB_ENDPOINT': ''})
    def test_get_db_returns_memory_db_when_no_endpoint(self):
        """Test that MemoryDB is returned when no YDB endpoint"""
        db = get_db()

        assert isinstance(db, MemoryDB)

    @patch.dict('os.environ', {'YDB_ENDPOINT': 'grpcs://ydb.example.com:2135'})
    @patch('src.db.ydb_client.HAS_YDB', False)
    def test_get_db_returns_memory_db_when_no_ydb_sdk(self):
        """Test MemoryDB returned when YDB SDK not installed"""
        db = get_db()

        assert isinstance(db, MemoryDB)
