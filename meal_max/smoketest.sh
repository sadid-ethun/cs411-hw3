#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5001/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

check_health() {
  echo "Checking health status..."
  response=$(curl -s -X GET "$BASE_URL/health")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

check_db() {
  echo "Checking database connection..."
  response=$(curl -s -X GET "$BASE_URL/db-check")
  echo "Response: $response"
  echo "$response" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}


##########################################################
#
# Meal Management
#
##########################################################

clear_meals() {
  echo "Clearing the meal catalog..."
  response=$(curl -s -X DELETE "$BASE_URL/clear-meals")
  echo "Response from clear-meals: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to clear meals."
    exit 1
  fi
}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal - $cuisine, $price, $difficulty)..."
  response=$(curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to add meal."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1
  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_name() {
  meal_name=$1
  echo "Getting meal by name ($meal_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$meal_name")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to get meal by name ($meal_name)."
    exit 1
  fi
}

delete_meal_by_id() {
  meal_id=$1
  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}


##########################################################
#
# Battle Management
#
##########################################################

prep_combatant() {
  meal_name=$1
  echo "Preparing combatant ($meal_name)..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" -H "Content-Type: application/json" -d "{\"meal\":\"$meal_name\"}")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to prepare combatant ($meal_name)."
    exit 1
  fi
}

execute_battle() {
  echo "Executing battle..."
  response=$(curl -s -X GET "$BASE_URL/battle")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to execute battle."
    exit 1
  fi
}

clear_combatants() {
  echo "Clearing all combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to clear combatants."
    exit 1
  fi
}

get_combatants() {
  echo "Getting all combatants..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to get combatants."
    exit 1
  fi
}



############################################################
#
# Leaderboard
#
############################################################

get_leaderboard() {
  sort_by=$1
  echo "Getting leaderboard sorted by $sort_by..."
  response=$(curl -s -X GET "$BASE_URL/leaderboard?sort=$sort_by")
  echo "Response: $response"
  echo "$response" | grep -q '"status": "success"'
  if [ $? -ne 0 ]; then
    echo "Failed to get leaderboard sorted by $sort_by."
    exit 1
  fi
}


############################################################
#
# Test Sequence
#
############################################################

# Health checks
check_health
check_db

# Clear meals and combatants to start fresh
clear_meals
clear_combatants

# Create meals for testing
create_meal "Pizza" "Italian" 10.99 "MED"
create_meal "Burger" "American" 8.99 "LOW"
create_meal "Sushi" "Japanese" 15.99 "HIGH"

# Retrieve meals by ID and name
get_meal_by_id 1
get_meal_by_name "Pizza"

# Prepare meals for battle and execute a battle
prep_combatant "Pizza"
prep_combatant "Burger"

# Verify combatants are retrieved
get_combatants

# Execute a battle
execute_battle

# Test leaderboard retrieval by different sorting criteria
get_leaderboard "wins"
get_leaderboard "win_pct"

# Delete a meal and clean up
delete_meal_by_id 1
clear_meals

echo "All tests passed successfully!"
