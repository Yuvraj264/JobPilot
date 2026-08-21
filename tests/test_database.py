from app.database.connection import engine, check_db_connection


def test_db_engine_created():
    """
    Test that SQLAlchemy engine is created successfully.
    """
    assert engine is not None


def test_db_connection_check_returns_dict():
    """
    Test that check_db_connection returns a dictionary containing status.
    """
    result = check_db_connection()
    assert isinstance(result, dict)
    assert "status" in result
