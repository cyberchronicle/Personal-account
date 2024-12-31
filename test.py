import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock
from app.main import app
from app.database.models.base import Base
from app.database.models.user import User
from app.database.models.tag import Tag, UserTag
from app.database.models.bookmark import Shelf, Bookmark, BookmarkInShelf
from app.database.connection.session import get_session
from app.s3.minio import S3Service, get_s3
from app.config import cfg
from botocore.exceptions import ClientError

# Использовать URL базы данных из конфигурации
DATABASE_URL = cfg.build_postgres_dsn
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_database():
    """Инициализация схемы базы данных перед тестами."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session(setup_database):
    """Сессия для тестов, очищающая данные между тестами."""
    session = TestingSessionLocal()
    try:
        # Очистка всех таблиц перед каждым тестом
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        yield session
    finally:
        session.close()

@pytest.fixture()
def client():
    """Клиент для тестирования."""
    return TestClient(app)

@pytest.fixture
def test_user(db_session):
    """Создание тестового пользователя."""
    user = User(id=1, login="testuser", first_name="Test", last_name="User")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_shelf(db_session, test_user):
    """Создание тестовой полки."""
    shelf = Shelf(id=1, name="Test Shelf", fk_user=test_user.id)
    db_session.add(shelf)
    db_session.commit()
    return shelf

@pytest.fixture
def test_bookmark(db_session):
    """Создание тестовой закладки."""
    bookmark = Bookmark(id=1, title="Test Bookmark")
    db_session.add(bookmark)
    db_session.commit()
    return bookmark

@pytest.fixture
def test_tags(db_session):
    """Создание тестовых тегов."""
    tags = [Tag(name="tag1"), Tag(name="tag2"), Tag(name="tag3")]
    db_session.add_all(tags)
    db_session.commit()
    return tags

# Тесты для подключения к сессии
def test_get_session(db_session):
    session_generator = get_session()
    session = next(session_generator)
    assert session is not None
    session.close()

# Тесты для users

def test_register_user_success(client, db_session):
    user_id = 1
    response = client.post(
        "/users/register",
        headers={"x-user-id": str(user_id)},
        json={
            "login": "testuser",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 200

    user = db_session.query(User).filter_by(id=user_id).first()
    assert user is not None
    assert user.login == "testuser"
    assert user.first_name == "Test"
    assert user.last_name == "User"

def test_register_user_exists(client, db_session):
    user_id = 1
    response = client.post(
        "/users/register",
        headers={"x-user-id": str(user_id)},
        json={
            "login": "testuser",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    response = client.post(
        "/users/register",
        headers={"x-user-id": str(user_id)},
        json={
            "login": "testuser",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"

def test_get_user_success(client, db_session):
    user = User(id=2, login="getuser", first_name="Get", last_name="User")
    db_session.add(user)
    db_session.commit()

    response = client.get(
        "/users/get",
        headers={"x-user-id": str(user.id)}
    )
    assert response.status_code == 200
    assert response.json() == {
        "login": "getuser",
        "first_name": "Get",
        "last_name": "User"
    }

def test_get_user_not_found(client, db_session):
    response = client.get(
        "/users/get",
        headers={"x-user-id": "999"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"

# Тесты для bookmarks

def test_get_shelves_success(client, db_session, test_user, test_shelf, test_bookmark):
    """Тест успешного получения списка полок."""
    db_session.add(BookmarkInShelf(fk_shelf=test_shelf.id, fk_bookmark=test_bookmark.id))
    db_session.commit()

    headers = {"x-user-id": str(test_user.id)}
    response = client.get("/bookmarks/get_shelves", headers=headers)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": test_shelf.id,
            "name": test_shelf.name,
            "bookmarks": [test_bookmark.title]
        }
    ]


def test_get_shelves_no_data(client, test_user):
    """Тест получения полок, когда их нет."""
    headers = {"x-user-id": str(test_user.id)}
    response = client.get("/bookmarks/get_shelves", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "No bookmarks found for this user"


def test_create_shelf_success(client, test_user):
    """Тест успешного создания полки."""
    headers = {"x-user-id": str(test_user.id)}
    payload = {"name": "New Shelf"}

    response = client.post("/bookmarks/create_shelf", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Shelf successfully created"


def test_create_shelf_user_not_found(client):
    """Тест создания полки для несуществующего пользователя."""
    headers = {"x-user-id": "999"}
    payload = {"name": "New Shelf"}

    response = client.post("/bookmarks/create_shelf", json=payload, headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User with id 999 not found"


def test_get_bookmarks_success(client, db_session, test_user, test_shelf, test_bookmark):
    """Тест успешного получения закладок с полки."""
    db_session.add(BookmarkInShelf(fk_shelf=test_shelf.id, fk_bookmark=test_bookmark.id))
    db_session.commit()

    headers = {"x-user-id": str(test_user.id)}
    response = client.get(f"/bookmarks/get_bookmarks?shelf_id={test_shelf.id}", headers=headers)
    assert response.status_code == 200
    assert response.json() == [{"id": test_bookmark.id, "title": test_bookmark.title}]


def test_get_bookmarks_empty_shelf(client, test_user, test_shelf):
    """Тест получения закладок с пустой полки."""
    headers = {"x-user-id": str(test_user.id)}
    response = client.get(f"/bookmarks/get_bookmarks?shelf_id={test_shelf.id}", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

def test_delete_bookmark_success(client, db_session, test_user, test_shelf, test_bookmark):
    """Тест успешного удаления закладки."""
    db_session.add(BookmarkInShelf(fk_shelf=test_shelf.id, fk_bookmark=test_bookmark.id))
    db_session.commit()

    headers = {"x-user-id": str(test_user.id)}
    payload = {"bookmark_id": test_bookmark.id, "shelf_id": test_shelf.id}

    response = client.post("/bookmarks/delete_bookmark_from_shelf", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Bookmark removed from shelf"


def test_delete_bookmark_not_found(client, test_user, test_shelf):
    """Тест удаления несуществующей закладки."""
    headers = {"x-user-id": str(test_user.id)}
    payload = {"bookmark_id": 999, "shelf_id": test_shelf.id}

    response = client.post("/bookmarks/delete_bookmark_from_shelf", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Bookmark removed from shelf"

def test_delete_shelf_success(client, db_session, test_user, test_shelf):
    """Тест успешного удаления полки."""
    headers = {"x-user-id": str(test_user.id)}
    payload = {"shelf_id": test_shelf.id}

    response = client.post("/bookmarks/delete_shelf", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Shelf removed"

# Тесты для models

def test_user_model(db_session):
    user = User(login="testuser", first_name="Test", last_name="User")
    db_session.add(user)
    db_session.commit()

    saved_user = db_session.query(User).filter_by(login="testuser").first()
    assert saved_user is not None
    assert saved_user.first_name == "Test"
    assert saved_user.last_name == "User"

def test_tag_model(db_session):
    tag = Tag(name="Test Tag")
    db_session.add(tag)
    db_session.commit()

    saved_tag = db_session.query(Tag).filter_by(name="Test Tag").first()
    assert saved_tag is not None

def test_user_tag_model(db_session):
    user = User(login="testuser", first_name="Test", last_name="User")
    tag = Tag(name="Test Tag")
    db_session.add(user)
    db_session.add(tag)
    db_session.commit()

    user_tag = UserTag(user_id=user.id, tag_id=tag.id)
    db_session.add(user_tag)
    db_session.commit()

    saved_user_tag = db_session.query(UserTag).filter_by(user_id=user.id, tag_id=tag.id).first()
    assert saved_user_tag is not None

def test_shelf_model(db_session):
    user = User(login="testuser", first_name="Test", last_name="User")
    db_session.add(user)
    db_session.commit()

    shelf = Shelf(name="Test Shelf", fk_user=user.id)
    db_session.add(shelf)
    db_session.commit()

    saved_shelf = db_session.query(Shelf).filter_by(name="Test Shelf").first()
    assert saved_shelf is not None
    assert saved_shelf.fk_user == user.id

def test_bookmark_model(db_session):
    bookmark = Bookmark(title="Test Bookmark")
    db_session.add(bookmark)
    db_session.commit()

    saved_bookmark = db_session.query(Bookmark).filter_by(title="Test Bookmark").first()
    assert saved_bookmark is not None

def test_bookmark_in_shelf_model(db_session):
    user = User(login="testuser", first_name="Test", last_name="User")
    db_session.add(user)
    db_session.commit()

    shelf = Shelf(name="Test Shelf", fk_user=user.id)
    bookmark = Bookmark(title="Test Bookmark")
    db_session.add(shelf)
    db_session.add(bookmark)
    db_session.commit()

    bookmark_in_shelf = BookmarkInShelf(fk_shelf=shelf.id, fk_bookmark=bookmark.id)
    db_session.add(bookmark_in_shelf)
    db_session.commit()

    saved_bookmark_in_shelf = db_session.query(BookmarkInShelf).filter_by(fk_shelf=shelf.id, fk_bookmark=bookmark.id).first()
    assert saved_bookmark_in_shelf is not None

# Тесты для tags

def test_update_user_tags_success(client, db_session, test_user):
    """Тест успешного добавления тегов."""
    headers = {"x-user-id": str(test_user.id)}
    payload = {"tags": ["tag1", "tag2"]}

    response = client.post("/tags/update", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Tags successfully saved"

    tags = db_session.query(Tag).all()
    assert len(tags) == 2
    assert set(tag.name for tag in tags) == {"tag1", "tag2"}

    user_tags = db_session.query(UserTag).filter_by(user_id=test_user.id).all()
    assert len(user_tags) == 2


def test_update_user_tags_empty_list(client, test_user):
    """Тест добавления пустого списка тегов."""
    headers = {"x-user-id": str(test_user.id)}
    payload = {"tags": []}

    response = client.post("/tags/update", json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Tags list cannot be empty or some tags is empty"


def test_update_user_tags_user_not_found(client):
    """Тест добавления тегов для несуществующего пользователя."""
    headers = {"x-user-id": "999"}
    payload = {"tags": ["tag1"]}

    response = client.post("/tags/update", json=payload, headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User with id 999 not found"


def test_get_user_tags_success(client, db_session, test_user, test_tags):
    """Тест успешного получения тегов пользователя."""
    user_tags = [UserTag(user_id=test_user.id, tag_id=tag.id) for tag in test_tags]
    db_session.add_all(user_tags)
    db_session.commit()

    headers = {"x-user-id": str(test_user.id)}
    response = client.get("/tags/get", headers=headers)
    assert response.status_code == 200
    assert set(response.json()["tags"]) == {"tag1", "tag2", "tag3"}


def test_get_user_tags_no_tags(client, test_user):
    """Тест получения тегов, когда у пользователя их нет."""
    headers = {"x-user-id": str(test_user.id)}

    response = client.get("/tags/get", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "No tags found for this user"


def test_get_user_tags_user_not_found(client):
    """Тест получения тегов для несуществующего пользователя."""
    headers = {"x-user-id": "999"}

    response = client.get("/tags/get", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User with id 999 not found"


def test_delete_user_tags_success(client, db_session, test_user, test_tags):
    """Тест успешного удаления тегов пользователя."""
    user_tags = [UserTag(user_id=test_user.id, tag_id=tag.id) for tag in test_tags]
    db_session.add_all(user_tags)
    db_session.commit()

    headers = {"x-user-id": str(test_user.id)}
    payload = {"tags": ["tag1", "tag2"]}

    response = client.post("/tags/delete", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Tags successfully deleted"

    remaining_tags = db_session.query(UserTag).filter_by(user_id=test_user.id).all()
    assert len(remaining_tags) == 1  # Остался только "tag3"


def test_delete_user_tags_empty_list(client, test_user):
    """Тест удаления тегов с пустым списком."""
    headers = {"x-user-id": str(test_user.id)}
    payload = {"tags": []}

    response = client.post("/tags/delete", json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Tags list cannot be empty"


def test_delete_user_tags_user_not_found(client):
    """Тест удаления тегов для несуществующего пользователя."""
    headers = {"x-user-id": "999"}
    payload = {"tags": ["tag1"]}

    response = client.post("/tags/delete", json=payload, headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User with id 999 not found"

# Тесты для files

def test_icon_upload(client):
    mock_s3 = MagicMock()
    app.dependency_overrides[get_s3] = lambda: mock_s3

    mock_s3.create_key.return_value = "icons/1"
    mock_s3.upload_file.return_value = "http://example.com/icons/1"

    response = client.post("/files/icon-upload",
                           headers={"x-user-id": "1"},
                           files={"file": ("avatar.png", b"test content", "image/png")})

    assert response.status_code == 200
    assert response.json() == "http://example.com/icons/1"

def test_icon_get_link(client):
    mock_s3 = MagicMock()
    app.dependency_overrides[get_s3] = lambda: mock_s3

    mock_s3.create_key.return_value = "icons/1"
    mock_s3.get_link.return_value = "http://example.com/icons/1"

    response = client.get("/files/icon-get-link",
                          headers={"x-user-id": "1"})

    assert response.status_code == 200
    assert response.json() == "http://example.com/icons/1"

    mock_s3.get_link.side_effect = FileNotFoundError()
    response = client.get("/files/icon-get-link",
                          headers={"x-user-id": "1"})

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"

# Тесты для s3

def test_create_key():
    key = S3Service.create_key("folder", "key")
    assert key == "folder/key"

def test_upload_file():
    mock_s3_client = MagicMock()
    mock_s3_service = S3Service()
    mock_s3_service.s3_client = mock_s3_client
    mock_s3_service.bucket_name = "test-bucket"

    file = MagicMock()
    file.file = b"test content"

    mock_s3_service.upload_file(file, "folder/key")
    mock_s3_client.upload_fileobj.assert_called_once()

def test_check_object_exists():
    mock_s3_client = MagicMock()
    mock_s3_service = S3Service()
    mock_s3_service.s3_client = mock_s3_client
    mock_s3_service.bucket_name = "test-bucket"

    mock_s3_client.head_object.return_value = {}
    exists = mock_s3_service.check_object_exists("folder/key")
    assert exists

    mock_s3_client.head_object.side_effect = ClientError({}, "HeadObject")
    exists = mock_s3_service.check_object_exists("folder/key")
    assert not exists

def test_get_link():
    mock_s3_client = MagicMock()
    mock_s3_service = S3Service()
    mock_s3_service.s3_client = mock_s3_client
    mock_s3_service.bucket_name = "test-bucket"

    mock_s3_client.generate_presigned_url.return_value = "http://example.com/folder/key"
    link = mock_s3_service.get_link("folder/key")
    assert link == "http://example.com/folder/key"

    mock_s3_service.check_object_exists = MagicMock(return_value=False)
    try:
        mock_s3_service.get_link("folder/key")
    except FileNotFoundError:
        assert True
