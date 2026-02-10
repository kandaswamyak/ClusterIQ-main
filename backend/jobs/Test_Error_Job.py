# Databricks notebook source
# Test Error Job - Intentionally causes failure for testing auto-healing

def process_data(data):
    """Process data with intentional error."""
    result = 0
    for item in data:
        # BUG: Division by zero error will occur
        result += 100 / item  # This will fail when item = 0
    return result

def calculate_metrics(values):
    """Calculate metrics with error."""
    total = sum(values)
    count = len(values)
    # BUG: Will fail if count is 0
    average = total / count
    return average

# TESTING - These will cause failures
print("=== Test Error Job Started ===")

# Test 1: Division by zero
test_data = [10, 5, 0, 2]  # Contains zero - will cause error
try:
    result = process_data(test_data)
    print(f"Result: {result}")
except Exception as e:
    print(f"ERROR: {e}")
    raise  # Re-raise to fail the job

print("=== Job should not reach here ===")
