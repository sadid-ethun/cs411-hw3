import pytest
import requests
from meal_max.utils.random_utils import get_random

# Mocked response values
RANDOM_DECIMAL = 0.42

@pytest.fixture
def mock_random_org(mocker):
    """Fixture to mock the response from random.org."""
    # Create a mock response object with the expected random number as text
    mock_response = mocker.Mock()
    mock_response.text = f"{RANDOM_DECIMAL}"
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

def test_get_random_success(mock_random_org):
    """Test retrieving a random decimal number from random.org."""
    result = get_random()

    # Assert that the result matches the mocked random decimal
    assert result == RANDOM_DECIMAL, f"Expected random decimal {RANDOM_DECIMAL}, but got {result}"

    # Verify that the correct URL was called
    requests.get.assert_called_once_with(
        "https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new", timeout=5
    )

def test_get_random_request_failure(mocker):
    """Simulate a request failure."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    # Expect RuntimeError with a specific message
    with pytest.raises(RuntimeError, match="Request to random.org failed: Connection error"):
        get_random()

def test_get_random_timeout(mocker):
    """Simulate a timeout."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    # Expect RuntimeError due to timeout
    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random()

def test_get_random_invalid_response(mock_random_org):
    """Simulate an invalid response (non-decimal)."""
    # Set the mocked response text to a non-decimal value
    mock_random_org.text = "invalid_response"

    # Expect ValueError with a specific message
    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_response"):
        get_random()
