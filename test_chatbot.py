#!/usr/bin/env python
"""Test chatbot with supplement queries"""

from app.services.chat_service import ChatService

# Test 1: Collagen query (previously broken)
print('=== TEST 1: Collagen Query ===')
result = ChatService.chat([{'role': 'user', 'content': 'show me collagen'}])
print(f'Intent: {result["intent"]}')
print(f'Products found: {len(result["products"])}')
for p in result['products']:
    print(f'  - {p["name"]} (${p["price"]}) - {p["category"]}')

print('\n=== TEST 2: Protein Query ===')
result = ChatService.chat([{'role': 'user', 'content': 'looking for protein powder'}])
print(f'Intent: {result["intent"]}')
print(f'Products found: {len(result["products"])}')
for p in result['products']:
    print(f'  - {p["name"]} (${p["price"]}) - {p["category"]}')

print('\n=== TEST 3: Vitamin Query ===')
result = ChatService.chat([{'role': 'user', 'content': 'need vitamin d'}])
print(f'Intent: {result["intent"]}')
print(f'Products found: {len(result["products"])}')
for p in result['products']:
    print(f'  - {p["name"]} (${p["price"]}) - {p["category"]}')

print('\n=== TEST 4: Omega-3 Query ===')
result = ChatService.chat([{'role': 'user', 'content': 'find omega-3'}])
print(f'Intent: {result["intent"]}')
print(f'Products found: {len(result["products"])}')
for p in result['products']:
    print(f'  - {p["name"]} (${p["price"]}) - {p["category"]}')

print('\n=== TEST 5: Probiotic Query ===')
result = ChatService.chat([{'role': 'user', 'content': 'probiotic supplements'}])
print(f'Intent: {result["intent"]}')
print(f'Products found: {len(result["products"])}')
for p in result['products']:
    print(f'  - {p["name"]} (${p["price"]}) - {p["category"]}')

print('\n=== TEST 6: Recommendations Query ===')
result = ChatService.chat([{'role': 'user', 'content': 'recommend something for immunity'}])
print(f'Intent: {result["intent"]}')
print(f'Products found: {len(result["products"])}')
for p in result['products']:
    print(f'  - {p["name"]} (${p["price"]}) - {p["category"]}')
