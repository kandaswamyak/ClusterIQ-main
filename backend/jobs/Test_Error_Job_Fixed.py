# Databricks notebook source
# Test Error Job - FIXED VERSION (Applied by AI Auto-Healing)

def process_data(data):
    """Process data with error handling."""
    result = 0
    for item in data:
        # FIXED: Added check for zero division
        if item != 0:
            result += 100 / item
        else:
            print(f"Warning: Skipping zero value in data")
    return result

def calculate_metrics(values):
    """Calculate metrics with error handling."""
    if not values or len(values) == 0:
        print("Warning: Empty values list, returning 0")
        return 0
    
    total = sum(values)
    count = len(values)
    average = total / count
    return average

# TESTING - All operations are now safe
print("=== Test Error Job Started (FIXED) ===")

# Test 1: Division by zero (now handled)
test_data = [10, 5, 0, 2]  # Contains zero - now handled safely
result = process_data(test_data)
print(f"Result: {result}")

# Test 2: Calculate metrics
metrics = calculate_metrics(test_data)
print(f"Average: {metrics}")

print("=== Test Error Job Completed Successfully ===")
