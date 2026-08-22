"""
Quick validation test script
Run with: python manage.py shell < test_validation.py
"""
from rest_framework.test import APIRequestFactory
from apps.students.serializers import (
    AcademicResultSerializer, 
    StudentProfileSerializer,
    StudentAttributeSerializer
)
from apps.users.serializers import RegisterSerializer

factory = APIRequestFactory()

print("="*70)
print("VALIDATION TESTS")
print("="*70)

# Test 1: Invalid Grade
print("\n[Test 1] Invalid grade 'F'")
serializer = AcademicResultSerializer(data={'subject': 1, 'grade': 'F'})
if not serializer.is_valid():
    print("✅ Correctly rejected:", serializer.errors)
else:
    print("❌ Should have failed!")

# Test 2: Invalid KCSE Year
print("\n[Test 2] Invalid KCSE year (1900)")
serializer = StudentProfileSerializer(data={'kcse_year': 1900, 'kcse_index_number': 'TEST123'})
if not serializer.is_valid():
    print("✅ Correctly rejected:", serializer.errors)
else:
    print("❌ Should have failed!")

# Test 3: Invalid Weight
print("\n[Test 3] Invalid weight (15)")
serializer = StudentAttributeSerializer(data={'attribute_type': 'SKILL', 'name': 'Test', 'weight': 15})
if not serializer.is_valid():
    print("✅ Correctly rejected:", serializer.errors)
else:
    print("❌ Should have failed!")

# Test 4: Short Password
print("\n[Test 4] Short password (5 chars)")
serializer = RegisterSerializer(data={'username': 'test', 'email': 'test@test.com', 'password': '12345'})
if not serializer.is_valid():
    print("✅ Correctly rejected:", serializer.errors)
else:
    print("❌ Should have failed!")

# Test 5: Valid Grade (should pass)
print("\n[Test 5] Valid grade 'A'")
serializer = AcademicResultSerializer(data={'subject': 1, 'grade': 'A'})
if serializer.is_valid():
    print("✅ Correctly accepted")
else:
    print("❌ Should have passed! Errors:", serializer.errors)

print("\n" + "="*70)
print("VALIDATION TESTS COMPLETE")
print("="*70)
