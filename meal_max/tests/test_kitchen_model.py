from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_meal_by_id,
    get_meal_by_name,
    get_leaderboard,
    update_meal_stats
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Create and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the database."""

    # Call the function to create a new meal
    create_meal(meal="Pizza", cuisine="Italian", price=10.99, difficulty="MED")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Pizza", "Italian", 10.99, "MED")
    actual_arguments = mock_cursor.execute.call_args[0][1]
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate name, raising an IntegrityError."""

    # Simulate IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Expect ValueError when handling IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Pizza' already exists"):
        create_meal(meal="Pizza", cuisine="Italian", price=10.99, difficulty="MED")
        
def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty level."""

    # Attempt to create a meal with an invalid difficulty level
    with pytest.raises(ValueError, match="Invalid difficulty level: EASY. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Pizza", cuisine="Italian", price=10.99, difficulty="EASY")

    # Attempt to create a meal with a completely unknown difficulty level
    with pytest.raises(ValueError, match="Invalid difficulty level: EXTREME. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Sushi", cuisine="Japanese", price=15.99, difficulty="EXTREME")

def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price (non-numeric or negative)."""

    # Attempt to create a meal with a negative price
    with pytest.raises(ValueError, match="Invalid price: -10.99. Price must be a positive number."):
        create_meal(meal="Pizza", cuisine="Italian", price=-10.99, difficulty="MED")

    # Attempt to create a meal with a price of zero
    with pytest.raises(ValueError, match="Invalid price: 0. Price must be a positive number."):
        create_meal(meal="Burger", cuisine="American", price=0, difficulty="LOW")

    # Attempt to create a meal with a non-numeric price
    with pytest.raises(ValueError, match="Invalid price: 'free'. Price must be a positive number."):
        create_meal(meal="Pasta", cuisine="Italian", price="free", difficulty="HIGH")

def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the database by meal ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the delete_meal function
    delete_meal(1)

    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Ensure the correct SQL queries were executed
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_select_sql == expected_select_sql
    assert actual_update_sql == expected_update_sql

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when attempting to delete a meal that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        delete_meal(999)

def test_clear_meals(mock_cursor, mocker):
    """Test clearing the entire meal catalog (removes all meals)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_meals function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()


######################################################
#
#    Leaderboard
#
######################################################

def test_get_leaderboard(mock_cursor):
    """Test retrieving the leaderboard of meals ordered by wins."""

    mock_cursor.fetchall.return_value = [
        (1, "Pizza", "Italian", 10.99, "MED", 5, 3, 0.6),
        (2, "Sushi", "Japanese", 15.99, "HIGH", 8, 6, 0.75)
    ]

    leaderboard = get_leaderboard(sort_by="wins")

    expected_result = [
        {'id': 1, 'meal': 'Pizza', 'cuisine': 'Italian', 'price': 10.99, 'difficulty': 'MED', 'battles': 5, 'wins': 3, 'win_pct': 60.0},
        {'id': 2, 'meal': 'Sushi', 'cuisine': 'Japanese', 'price': 15.99, 'difficulty': 'HIGH', 'battles': 8, 'wins': 6, 'win_pct': 75.0}
    ]

    assert leaderboard == expected_result

def test_get_leaderboard_win_pct(mock_cursor):
    """Test retrieving the leaderboard of meals ordered by win percentage."""

    mock_cursor.fetchall.return_value = [
        (1, "Pizza", "Italian", 10.99, "MED", 5, 3, 0.6),
        (2, "Sushi", "Japanese", 15.99, "HIGH", 8, 6, 0.75)
    ]

    leaderboard = get_leaderboard(sort_by="win_pct")

    expected_result = [
        {'id': 2, 'meal': 'Sushi', 'cuisine': 'Japanese', 'price': 15.99, 'difficulty': 'HIGH', 'battles': 8, 'wins': 6, 'win_pct': 75.0},
        {'id': 1, 'meal': 'Pizza', 'cuisine': 'Italian', 'price': 10.99, 'difficulty': 'MED', 'battles': 5, 'wins': 3, 'win_pct': 60.0}
    ]

    assert leaderboard == expected_result

def test_get_leaderboard_invalid_sort_by():
    """Test error when providing an invalid sort_by parameter for the leaderboard."""

    # Attempt to retrieve the leaderboard with an invalid sort_by parameter
    with pytest.raises(ValueError, match="Invalid sort_by parameter: 'invalid_sort'. Expected 'wins' or 'win_pct'."):
        get_leaderboard(sort_by="invalid_sort")


######################################################
#
#    Meal Retrieval
#
######################################################

def test_get_meal_by_id(mock_cursor):
    """Test retrieving a meal by its ID."""

    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.99, "MED", False)

    result = get_meal_by_id(1)
    expected_result = Meal(id=1, meal="Pizza", cuisine="Italian", price=10.99, difficulty="MED")

    assert result == expected_result

def test_get_meal_by_id_deleted(mock_cursor):
    """Test error when trying to retrieve a meal that's been marked as deleted."""

    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.99, "MED", True)

    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)

def test_get_meal_by_id_not_found(mock_cursor):
    """Test error when trying to retrieve a non-existent meal."""

    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_name(mock_cursor):
    """Test retrieving a meal by its name."""

    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.99, "MED", False)

    result = get_meal_by_name("Pizza")
    expected_result = Meal(id=1, meal="Pizza", cuisine="Italian", price=10.99, difficulty="MED")

    assert result == expected_result

def test_get_meal_by_name_deleted(mock_cursor):
    """Test error when trying to retrieve a meal that's been marked as deleted."""

    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.99, "MED", True)

    with pytest.raises(ValueError, match="Meal with name 'Pizza' has been deleted"):
        get_meal_by_name("Pizza")

def test_get_meal_by_name_not_found(mock_cursor):
    """Test error when trying to retrieve a non-existent meal."""

    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with name 'Sushi' not found"):
        get_meal_by_name("Sushi")


######################################################
#
#    Update Meal Stats
#
######################################################

def test_update_meal_stats_win(mock_cursor):
    """Test updating meal stats for a win result."""

    mock_cursor.fetchone.return_value = [False]  # Meal is not deleted
    meal_id = 1
    update_meal_stats(meal_id, result="win")

    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_query == expected_query
    assert mock_cursor.execute.call_args_list[1][0][1] == (meal_id,)

def test_update_meal_stats_loss(mock_cursor):
    """Test updating meal stats for a loss result."""

    mock_cursor.fetchone.return_value = [False]  # Meal is not deleted
    meal_id = 1
    update_meal_stats(meal_id, result="loss")

    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_query == expected_query
    assert mock_cursor.execute.call_args_list[1][0][1] == (meal_id,)

def test_update_meal_stats_invalid_result():
    """Test error when trying to update meal stats with an invalid result."""

    with pytest.raises(ValueError, match="Invalid result: 'draw'. Must be 'win' or 'loss'."):
        update_meal_stats(meal_id=1, result="draw")

def test_update_meal_stats_deleted(mock_cursor):
    """Test error when trying to update stats for a meal that's been marked as deleted."""

    mock_cursor.fetchone.return_value = [True]  # Meal is deleted

    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(meal_id=1, result="win")

def test_update_meal_stats_not_found(mock_cursor):
    """Test error when trying to update stats for a non-existent meal."""

    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        update_meal_stats(meal_id=999, result="win")
