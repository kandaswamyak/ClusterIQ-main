# Databricks notebook source
def divide(a, b):
    return a / b if b != 0 else 0

print(divide(10, 0))   # ❌ causes failure
