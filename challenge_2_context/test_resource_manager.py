import pytest
import sqlite3
import requests
import redis
from resource_manager import ResourceManager


class MockDatabase:
    """Simple mock database using sqlite3 in-memory."""

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        self.cursor.execute("INSERT INTO test VALUES (1, 'test_data')")
        self.connection.commit()

    def query(self, sql: str):
        return self.cursor.execute(sql).fetchall()

    def close(self):
        self.connection.close()


class PokeAPIClient:
    """Client for PokeAPI requests."""

    def __init__(self, base_url: str = "https://pokeapi.co/api/v2"):
        self.base_url = base_url
        self.session = requests.Session()

    def get_pokemon(self, name: str):
        response = self.session.get(f"{self.base_url}/pokemon/{name}")
        response.raise_for_status()
        return response.json()

    def close(self):
        self.session.close()


def is_redis_available():
    """Check if Redis is running."""
    try:
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        r.ping()
        r.close()
        return True
    except (redis.ConnectionError, redis.TimeoutError):
        return False


def test_basic_context_with_db():
    with ResourceManager("DBTest") as rm:
        db = MockDatabase("test_db")
        rm.add_resource("database", db)

        # Use the database
        result = db.query("SELECT * FROM test")
        assert result == [(1, 'test_data')]

    # After context, connection should be closed
    with pytest.raises(sqlite3.ProgrammingError):
        db.query("SELECT * FROM test")


def test_pokeapi_integration():
    with ResourceManager("PokeAPITest") as rm:
        api = PokeAPIClient()
        rm.add_resource("pokeapi", api)

        # Fetch Pikachu data
        pokemon = api.get_pokemon("pikachu")
        assert pokemon['name'] == 'pikachu'
        assert pokemon['id'] == 25


def test_nested_contexts():
    """Test nested context managers with DB and API."""
    with ResourceManager("OuterContext") as outer_rm:
        db = MockDatabase("outer_db")
        outer_rm.add_resource("database", db)

        with ResourceManager("InnerContext") as inner_rm:
            api = PokeAPIClient()
            inner_rm.add_resource("pokeapi", api)

            # Both resources should work
            db_result = db.query("SELECT * FROM test")
            api_result = api.get_pokemon("ditto")

            assert db_result == [(1, 'test_data')]
            assert api_result['name'] == 'ditto'


def test_exception_handling():
    """Test that resources are cleaned up even with exceptions."""
    db = None

    try:
        with ResourceManager("ExceptionTest") as rm:
            db = MockDatabase("exception_db")
            rm.add_resource("database", db)

            # Verify DB works before exception
            result = db.query("SELECT * FROM test")
            assert result == [(1, 'test_data')]

            # Trigger exception
            raise ValueError("Test exception")

    except ValueError:
        pass

    # DB should be closed despite exception
    with pytest.raises(sqlite3.ProgrammingError):
        db.query("SELECT * FROM test")


@pytest.mark.skipif(not is_redis_available(), reason="Redis is not running")
def test_redis_integration():
    """Test context manager with Redis (conditional on availability)."""
    with ResourceManager("RedisTest") as rm:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        rm.add_resource("redis", r)

        # Set and get a value
        r.set("test_key", "test_value")
        value = r.get("test_key")
        assert value == "test_value"

        # Cleanup test data
        r.delete("test_key")


def test_multiple_resources():
    """Test managing multiple different resources simultaneously."""
    with ResourceManager("MultiResourceTest") as rm:
        db1 = MockDatabase("db1")
        db2 = MockDatabase("db2")
        api = PokeAPIClient()

        rm.add_resource("database1", db1)
        rm.add_resource("database2", db2)
        rm.add_resource("pokeapi", api)

        # All resources should work
        assert db1.query("SELECT * FROM test") == [(1, 'test_data')]
        assert db2.query("SELECT * FROM test") == [(1, 'test_data')]
        assert api.get_pokemon("bulbasaur")['id'] == 1