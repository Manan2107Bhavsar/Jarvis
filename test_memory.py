#!/usr/bin/env python3
"""Test script to verify memory system functionality"""

from memory_engine import load_profile, update_profile, search_history, memory_context

print("=== Testing Memory System ===\n")

# Test 1: Load Profile
print("1. Testing profile loading...")
profile = load_profile()
print(f"   Current profile: {profile}\n")

# Test 2: Update Profile
print("2. Testing profile update...")
update_profile("study", "Computer Science")
update_profile("location", "Canada")
profile = load_profile()
print(f"   Updated profile: {profile}\n")

# Test 3: Search History
print("3. Testing history search...")
results = search_history("chatgpt", limit=3)
print(f"   Found {len(results)} results for 'chatgpt':")
for i, result in enumerate(results, 1):
    print(f"   {i}. {result[:100]}...")
print()

# Test 4: Memory Context
print("4. Testing memory context...")
context = memory_context("what is python")
print(f"   Context generated:\n{context}\n")

print("=== All Tests Complete ===")
