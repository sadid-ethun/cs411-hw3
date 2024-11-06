import pytest
from unittest.mock import patch
from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal


@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

@pytest.fixture
def mock_update_meal_stats(mocker):
    """Mock the update_meal_stats function for testing purposes."""
    return mocker.patch("meal_max.models.battle_model.update_meal_stats")

@pytest.fixture
def mock_get_random(mocker):
    """Mock the get_random function to control randomness in tests."""
    return mocker.patch("meal_max.models.battle_model.get_random", return_value=0.5)

"""Sample combatants"""
@pytest.fixture
def combatant_1():
    return Meal(id=1, meal="Meal 1", cuisine="Italian", price=15.0, difficulty="MED")

@pytest.fixture
def combatant_2():
    return Meal(id=2, meal="Meal 2", cuisine="Mexican", price=12.0, difficulty="LOW")

@pytest.fixture
def combatant_high_difficulty():
    return Meal(id=3, meal="High Difficulty Meal", cuisine="French", price=30.0, difficulty="HIGH")

@pytest.fixture
def combatant_low_difficulty():
    return Meal(id=4, meal="Low Difficulty Meal", cuisine="Chinese", price=8.0, difficulty="LOW")


##################################################
# BattleModel Method Tests
##################################################

def test_prep_combatant(battle_model, combatant_1):
    """Test adding a single combatant to the battle."""
    battle_model.prep_combatant(combatant_1)
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == "Meal 1"

def test_prep_combatant_two(battle_model, combatant_1, combatant_2):
    """Test adding two combatants to the battle successfully."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)
    assert len(battle_model.combatants) == 2
    assert battle_model.combatants[1].meal == "Meal 2"

def test_prep_combatant_full_list(battle_model, combatant_1, combatant_2):
    """Test attempting to add a third combatant raises an error."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(combatant_1)

def test_clear_combatants(battle_model, combatant_1, combatant_2):
    """Test clearing the list of combatants."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)
    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0, "Expected combatants list to be empty after clearing"

def test_clear_combatants_empty_list(battle_model):
    """Test clearing combatants when the list is already empty."""
    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0, "Expected combatants list to remain empty"

def test_get_combatants(battle_model, combatant_1, combatant_2):
    """Test retrieving the list of current combatants."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)
    combatants = battle_model.get_combatants()
    assert len(combatants) == 2
    assert combatants[0].meal == "Meal 1"
    assert combatants[1].meal == "Meal 2"

def test_get_combatants_empty_list(battle_model):
    """Test retrieving combatants when the list is empty."""
    combatants = battle_model.get_combatants()
    assert len(combatants) == 0, "Expected empty list of combatants"

##################################################
# Battle Execution Tests
##################################################

def test_battle(battle_model, combatant_1, combatant_2, mock_update_meal_stats, mock_get_random):
    """Test executing a battle and determining a winner."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)

    winner = battle_model.battle()

    assert winner in ["Meal 1", "Meal 2"], "Expected one of the meals to be the winner"

    assert mock_update_meal_stats.call_count == 2, "Expected update_meal_stats to be called twice"

    mock_update_meal_stats.assert_any_call(combatant_1.id, "win")
    mock_update_meal_stats.assert_any_call(combatant_2.id, "loss")

    assert len(battle_model.combatants) == 1, "Expected only one combatant to remain after battle"


def test_battle_insufficient_combatants(battle_model, combatant_1):
    """Test that a battle cannot start with less than two combatants."""
    battle_model.prep_combatant(combatant_1)
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_battle_no_combatants(battle_model):
    """Test that a battle cannot start with zero combatants."""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_battle_edge_case_for_delta(battle_model, combatant_1, combatant_2, mock_update_meal_stats, mocker):
    """Test battle outcome when delta is exactly equal to the random number."""
    battle_model.prep_combatant(combatant_1)
    battle_model.prep_combatant(combatant_2)
    
    score_1 = battle_model.get_battle_score(combatant_1)
    score_2 = battle_model.get_battle_score(combatant_2)
    delta = abs(score_1 - score_2) / 100

    mocker.patch("meal_max.models.battle_model.get_random", return_value=delta)

    winner = battle_model.battle()
    assert winner in ["Meal 1", "Meal 2"], "Expected one of the meals to be the winner when delta equals random value"

    
    mock_get_random = mocker.patch("meal_max.models.battle_model.get_random", return_value=0.1)
    
    score_1 = battle_model.get_battle_score(combatant_1)
    score_2 = battle_model.get_battle_score(combatant_2)
    delta = abs(score_1 - score_2) / 100
    assert delta == 0.1, "Expected delta to be equal to mocked random value 0.1"

    winner = battle_model.battle()
    assert winner in ["Meal 1", "Meal 2"], "Expected one of the meals to be the winner when delta equals random value"

##################################################
# Battle Score Calculation Tests
##################################################

def test_get_battle_score_high_difficulty(battle_model, combatant_high_difficulty):
    """Test calculating battle score for a combatant with difficulty 'HIGH'."""
    score = battle_model.get_battle_score(combatant_high_difficulty)
    expected_score = (combatant_high_difficulty.price * len(combatant_high_difficulty.cuisine)) - 1
    assert score == expected_score, f"Expected score to be {expected_score}, but got {score}"

def test_get_battle_score_med_difficulty(battle_model, combatant_1):
    """Test calculating battle score for a combatant with difficulty 'MED'."""
    score = battle_model.get_battle_score(combatant_1)
    expected_score = (combatant_1.price * len(combatant_1.cuisine)) - 2
    assert score == expected_score, f"Expected score to be {expected_score}, but got {score}"

def test_get_battle_score_low_difficulty(battle_model, combatant_low_difficulty):
    """Test calculating battle score for a combatant with difficulty 'LOW'."""
    score = battle_model.get_battle_score(combatant_low_difficulty)
    expected_score = (combatant_low_difficulty.price * len(combatant_low_difficulty.cuisine)) - 3
    assert score == expected_score, f"Expected score to be {expected_score}, but got {score}"

def test_get_battle_score_high_price(battle_model):
    """Test calculating battle score with a very high price."""
    high_price_combatant = Meal(id=5, meal="Expensive Meal", cuisine="Japanese", price=100.0, difficulty="MED")
    score = battle_model.get_battle_score(high_price_combatant)
    expected_score = (high_price_combatant.price * len(high_price_combatant.cuisine)) - 2
    assert score == expected_score, f"Expected score to be {expected_score}, but got {score}"

def test_get_battle_score_long_cuisine(battle_model):
    """Test calculating battle score with a long cuisine string."""
    long_cuisine_combatant = Meal(id=6, meal="Long Cuisine Meal", cuisine="VeryLongCuisineType", price=10.0, difficulty="LOW")
    score = battle_model.get_battle_score(long_cuisine_combatant)
    expected_score = (long_cuisine_combatant.price * len(long_cuisine_combatant.cuisine)) - 3
    assert score == expected_score, f"Expected score to be {expected_score}, but got {score}"

def test_get_battle_score_zero_price(battle_model):
    """Test calculating battle score for a combatant with a price of zero."""
    zero_price_combatant = Meal(id=7, meal="Free Meal", cuisine="American", price=0.0, difficulty="MED")
    score = battle_model.get_battle_score(zero_price_combatant)
    expected_score = (zero_price_combatant.price * len(zero_price_combatant.cuisine)) - 2
    assert score == expected_score, f"Expected score to be {expected_score}, but got {score}"

def test_get_battle_score_negative_price(battle_model):
    """Test calculating battle score for a combatant with a negative price."""
    negative_price_combatant = Meal(id=8, meal="Discount Meal", cuisine="Thai", price=-10.0, difficulty="HIGH")

    with pytest.raises(ValueError, match="Price must be a positive value"):
        battle_model.get_battle_score(negative_price_combatant)

