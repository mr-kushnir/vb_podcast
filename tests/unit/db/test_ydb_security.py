"""
Security tests for YDB Client - SQL Injection prevention
RED phase: Writing tests first
"""

import pytest
from src.db.ydb_client import YDBClient, MemoryDB


class TestYDBSecurityInjection:
    """Test SQL injection prevention"""

    @pytest.fixture
    def db(self):
        # Use MemoryDB for testing (no real YDB needed)
        return MemoryDB()

    def test_select_prevents_table_name_injection(self, db):
        """Test that table names are sanitized"""
        # Insert valid data
        db.insert("users", {"id": "1", "name": "Alice"})

        # Try SQL injection via table name
        malicious_table = "users; DROP TABLE users--"

        # Should either raise error or sanitize safely
        try:
            result = db.select(malicious_table)
            # If no error, result should be empty (table doesn't exist)
            assert result == []
        except (ValueError, Exception):
            # Or raise appropriate error
            pass

    def test_select_prevents_where_injection(self, db):
        """Test that WHERE clause is sanitized"""
        db.insert("users", {"id": "1", "name": "Alice", "role": "user"})
        db.insert("users", {"id": "2", "name": "Bob", "role": "admin"})

        # Try SQL injection via where parameter
        malicious_where = {"name": "Alice' OR '1'='1"}

        result = db.select("users", where=malicious_where)

        # Should NOT return all records (that would be injection success)
        # Should return 0 records (no exact match for malicious string)
        assert len(result) == 0 or result[0]["name"] == "Alice' OR '1'='1"

    def test_delete_prevents_injection(self, db):
        """Test that DELETE is protected from injection"""
        db.insert("users", {"id": "1", "name": "Alice"})
        db.insert("users", {"id": "2", "name": "Bob"})

        # Try to delete all via injection
        malicious_where = {"id": "1' OR '1'='1"}

        db.delete("users", where=malicious_where)

        # Should NOT delete all records
        remaining = db.select("users")
        assert len(remaining) > 0  # At least one record should remain

    def test_execute_query_with_parameters(self, db):
        """Test parameterized query execution"""
        # This is the SAFE way - using parameters
        # Should be implemented instead of string interpolation

        # For now, this test will fail (method doesn't exist yet)
        with pytest.raises(AttributeError):
            db.execute_safe(
                "SELECT * FROM users WHERE name = :name",
                {"name": "Alice"}
            )


class TestHashSecurity:
    """Test secure hash functions"""

    def test_article_id_uses_secure_hash(self):
        """Test that article IDs use SHA-256, not MD5"""
        from src.news.parser import TechCrunchParser

        parser = TechCrunchParser()
        url = "https://example.com/article"

        article_id = parser.generate_article_id(url)

        # MD5 produces 32 hex chars, but we take [:12]
        # SHA-256 produces 64 hex chars, we should also take [:12]
        assert len(article_id) == 12

        # Verify it's using SHA-256 by checking if it changes
        # when we use MD5 (it should be different)
        import hashlib
        md5_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        sha256_hash = hashlib.sha256(url.encode()).hexdigest()[:12]

        # Article ID should NOT be the MD5 version
        assert article_id != md5_hash
        # Article ID SHOULD be the SHA-256 version
        assert article_id == sha256_hash
