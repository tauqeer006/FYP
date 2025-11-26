"""
Quick test script to verify chatbot service is working
Run this from Django shell: python manage.py shell < test_chatbot.py
"""

from main.services.chatbot_service import get_chatbot_service

# Initialize service
service = get_chatbot_service()

# Test 1: Check if routes loaded
print("=" * 80)
print("TEST 1: Routes Loading")
print("=" * 80)
if service.routes_data:
    print(f"✓ Routes loaded successfully")
    print(f"  Total routes: {len(service.routes_data.get('routes', {}))}")
else:
    print("✗ Failed to load routes")

# Test 2: Check routes context formatting
print("\n" + "=" * 80)
print("TEST 2: Routes Context Formatting")
print("=" * 80)
context = service.format_routes_for_context()
print(f"✓ Context generated: {len(context)} characters")
print(f"  First 300 chars:\n{context[:300]}")

# Test 3: Check fallback route
print("\n" + "=" * 80)
print("TEST 3: Fallback Route")
print("=" * 80)
fallback = service.get_fallback_route()
print(f"✓ Fallback route: {fallback['route_id']} -> {fallback['path']}")

# Test 4: Check route info retrieval
print("\n" + "=" * 80)
print("TEST 4: Route Info Retrieval")
print("=" * 80)
route_info = service.get_route_info('homepage')
if route_info:
    print(f"✓ Retrieved route info for 'homepage'")
    print(f"  Description: {route_info.get('description')}")
else:
    print("✗ Failed to retrieve route info")

print("\n" + "=" * 80)
print("All tests completed!")
print("=" * 80)
