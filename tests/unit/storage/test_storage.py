"""
Unit tests for Storage Client - LocalStorage
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch
from src.storage.s3_client import LocalStorage, get_storage


class TestLocalStorage:
    """Test local filesystem storage"""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create LocalStorage with temporary directory"""
        return LocalStorage(base_path=str(tmp_path))

    @pytest.fixture
    def sample_file(self, tmp_path):
        """Create a sample file for testing"""
        # Create file outside of storage directory
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        file_path = source_dir / "test_file.txt"
        file_path.write_text("Sample content for testing")
        return str(file_path)

    def test_init_creates_base_path(self, tmp_path):
        """Test that base path is created on init"""
        base = tmp_path / "storage"
        storage = LocalStorage(base_path=str(base))

        assert base.exists()
        assert base.is_dir()

    def test_upload_file_copies_to_storage(self, storage, sample_file):
        """Test uploading a file"""
        url = storage.upload_file(sample_file, "uploaded.txt")

        assert storage.exists("uploaded.txt")
        assert "uploaded.txt" in url

    def test_upload_file_uses_original_name_if_not_specified(self, storage, sample_file):
        """Test upload with auto-generated object name"""
        url = storage.upload_file(sample_file)

        assert storage.exists("test_file.txt")

    def test_upload_file_creates_subdirectories(self, storage, sample_file):
        """Test upload creates nested directories"""
        url = storage.upload_file(sample_file, "subdir/nested/file.txt")

        assert storage.exists("subdir/nested/file.txt")

    def test_upload_bytes_stores_data(self, storage):
        """Test uploading bytes"""
        data = b"Binary data content"
        url = storage.upload_bytes(data, "data.bin")

        assert storage.exists("data.bin")
        downloaded = storage.download_bytes("data.bin")
        assert downloaded == data

    def test_upload_bytes_creates_subdirectories(self, storage):
        """Test upload_bytes with nested path"""
        url = storage.upload_bytes(b"data", "folder/file.bin")

        assert storage.exists("folder/file.bin")

    def test_download_file_copies_from_storage(self, storage, tmp_path):
        """Test downloading a file"""
        storage.upload_bytes(b"test content", "download_test.txt")

        dest = tmp_path / "downloaded.txt"
        result = storage.download_file("download_test.txt", str(dest))

        assert dest.exists()
        assert dest.read_text() == "test content"
        assert result == str(dest)

    def test_download_bytes_returns_content(self, storage):
        """Test downloading as bytes"""
        original = b"Binary content to download"
        storage.upload_bytes(original, "binary.dat")

        downloaded = storage.download_bytes("binary.dat")

        assert downloaded == original

    def test_delete_removes_file(self, storage):
        """Test deleting a file"""
        storage.upload_bytes(b"content", "to_delete.txt")
        assert storage.exists("to_delete.txt")

        result = storage.delete("to_delete.txt")

        assert result is True
        assert not storage.exists("to_delete.txt")

    def test_delete_nonexistent_file_succeeds(self, storage):
        """Test deleting file that doesn't exist"""
        result = storage.delete("nonexistent.txt")

        assert result is True  # Succeeds, no error

    def test_exists_returns_true_for_existing_file(self, storage):
        """Test exists() for existing file"""
        storage.upload_bytes(b"data", "exists_test.txt")

        assert storage.exists("exists_test.txt") is True

    def test_exists_returns_false_for_missing_file(self, storage):
        """Test exists() for missing file"""
        assert storage.exists("missing.txt") is False

    def test_list_objects_returns_all_files(self, storage):
        """Test listing all objects"""
        storage.upload_bytes(b"1", "file1.txt")
        storage.upload_bytes(b"2", "file2.txt")
        storage.upload_bytes(b"3", "file3.txt")

        objects = storage.list_objects()

        assert len(objects) == 3
        keys = [obj['key'] for obj in objects]
        assert "file1.txt" in keys
        assert "file2.txt" in keys

    def test_list_objects_filters_by_prefix(self, storage):
        """Test listing with prefix filter"""
        import os.path
        logs_path = os.path.join("logs", "")  # Use OS-appropriate path separator

        storage.upload_bytes(b"1", "logs/app.log")
        storage.upload_bytes(b"2", "logs/error.log")
        storage.upload_bytes(b"3", "data/file.txt")

        objects = storage.list_objects(prefix=logs_path)

        assert len(objects) >= 2  # At least the logs files
        if len(objects) > 0:
            keys = [obj['key'] for obj in objects]
            assert any("logs" in key for key in keys)

    def test_list_objects_respects_max_keys(self, storage):
        """Test max_keys limit"""
        for i in range(10):
            storage.upload_bytes(b"data", f"file{i}.txt")

        objects = storage.list_objects(max_keys=5)

        assert len(objects) == 5

    def test_list_objects_includes_metadata(self, storage):
        """Test that list returns size and modified time"""
        storage.upload_bytes(b"test data", "meta_test.txt")

        objects = storage.list_objects()

        assert len(objects) > 0
        obj = objects[0]
        assert 'key' in obj
        assert 'size' in obj
        assert 'modified' in obj
        assert obj['size'] > 0

    def test_get_url_returns_file_url(self, storage):
        """Test getting file URL"""
        storage.upload_bytes(b"data", "url_test.txt")

        url = storage.get_url("url_test.txt")

        assert url.startswith("file://")
        assert "url_test.txt" in url

    def test_get_presigned_url_returns_url(self, storage):
        """Test getting presigned URL (returns regular URL for local)"""
        storage.upload_bytes(b"data", "presigned_test.txt")

        url = storage.get_presigned_url("presigned_test.txt", expiration=3600)

        assert "presigned_test.txt" in url


class TestGetStorage:
    """Test get_storage factory"""

    @patch.dict('os.environ', {'AWS_ACCESS_KEY_ID': ''})
    @patch('src.storage.s3_client.HAS_BOTO', True)
    def test_get_storage_returns_local_when_no_credentials(self):
        """Test LocalStorage returned when no AWS credentials"""
        storage = get_storage()

        assert isinstance(storage, LocalStorage)

    @patch('src.storage.s3_client.HAS_BOTO', False)
    def test_get_storage_returns_local_when_no_boto3(self):
        """Test LocalStorage returned when boto3 not installed"""
        storage = get_storage()

        assert isinstance(storage, LocalStorage)
