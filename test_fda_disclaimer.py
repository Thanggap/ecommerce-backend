#!/usr/bin/env python
"""Test chatbot FDA disclaimer compliance"""

from app.services.chat_service import ChatService

# Test with product recommendation
print('=== Testing FDA Disclaimer in Responses ===\n')

result = ChatService.chat([{'role': 'user', 'content': 'recommend vitamins for immunity'}])

print(f'Intent: {result["intent"]}')
print(f'Products found: {len(result["products"])}')
print(f'\nAI Response:\n{result["message"]}\n')

# Check if FDA disclaimer exists
fda_disclaimer = "These statements have not been evaluated by the FDA"
has_disclaimer = fda_disclaimer.lower() in result["message"].lower()

print(f'✓ FDA Disclaimer present: {has_disclaimer}')

if not has_disclaimer:
    print('⚠ WARNING: FDA disclaimer missing in response!')
else:
    print('✓ Compliance check passed!')
