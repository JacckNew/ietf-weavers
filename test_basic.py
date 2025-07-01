#!/usr/bin/env python3
"""
Simple test runner for IETF Weavers to check basic functionality
without requiring all dependencies.
"""

import sys
import os
import json

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_basic_imports():
    """Test basic imports without heavy dependencies."""
    print("Testing basic imports...")
    
    try:
        from agent.utils import EmailParser, PersonIdentityResolver, ThreadAnalyzer
        print("✅ Utils imported successfully")
    except Exception as e:
        print(f"❌ Utils import failed: {e}")
        return False
    
    try:
        from agent.graph_builder import SocialGraphBuilder
        print("✅ Graph builder imported successfully")
    except Exception as e:
        print(f"❌ Graph builder import failed: {e}")
        return False
    
    try:
        from agent.formatter import D3Formatter
        print("✅ Formatter imported successfully")
    except Exception as e:
        print(f"❌ Formatter import failed: {e}")
        return False
    
    return True

def test_email_parsing():
    """Test email parsing functionality."""
    print("\nTesting email parsing...")
    
    try:
        from agent.utils import EmailParser, PersonIdentityResolver
        
        parser = EmailParser()
        resolver = PersonIdentityResolver()
        
        # Test email normalization
        test_email = "Alice Smith <alice@example.com>"
        normalized = parser.normalize_email(test_email)
        print(f"✅ Email normalization: {test_email} -> {normalized}")
        
        # Test email classification
        classification = parser.classify_email_type(normalized)
        print(f"✅ Email classification: {normalized} -> {classification}")
        
        # Test person mapping
        person_id = resolver.add_email_mapping(normalized, "Alice Smith")
        print(f"✅ Person mapping: {normalized} -> {person_id}")
        
        return True
    except Exception as e:
        print(f"❌ Email parsing test failed: {e}")
        return False

def test_sample_data():
    """Test loading sample data."""
    print("\nTesting sample data loading...")
    
    sample_file = os.path.join(project_root, 'data', 'sample_emails.json')
    if not os.path.exists(sample_file):
        print(f"❌ Sample data file not found: {sample_file}")
        return False
    
    try:
        with open(sample_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Sample data loaded: {len(data)} emails")
        
        # Test first email structure
        if data:
            first_email = data[0]
            required_fields = ['from', 'to', 'date', 'message_id', 'subject', 'content']
            missing_fields = [field for field in required_fields if field not in first_email]
            
            if missing_fields:
                print(f"❌ Missing fields in sample data: {missing_fields}")
                return False
            else:
                print("✅ Sample data structure is valid")
        
        return True
    except Exception as e:
        print(f"❌ Sample data loading failed: {e}")
        return False

def test_basic_pipeline():
    """Test basic pipeline functionality."""
    print("\nTesting basic pipeline...")
    
    try:
        from agent.utils import EmailParser, PersonIdentityResolver, ThreadAnalyzer
        
        # Load sample data
        sample_file = os.path.join(project_root, 'data', 'sample_emails.json')
        with open(sample_file, 'r') as f:
            emails = json.load(f)
        
        # Initialize components
        parser = EmailParser()
        resolver = PersonIdentityResolver()
        thread_analyzer = ThreadAnalyzer()
        
        # Process emails
        processed_count = 0
        for email in emails:
            from_email = email.get('from', '')
            if parser.classify_email_type(from_email) == 'individual':
                person_id = resolver.add_email_mapping(from_email)
                thread_analyzer.add_message(
                    email.get('message_id', ''),
                    email.get('in_reply_to', ''),
                    from_email,
                    email.get('date', ''),
                    email.get('subject', '')
                )
                processed_count += 1
        
        print(f"✅ Processed {processed_count} individual emails")
        print(f"✅ Identified {len(resolver.person_to_emails)} unique persons")
        
        # Test thread analysis
        interactions = thread_analyzer.extract_interactions()
        print(f"✅ Extracted {len(interactions)} interactions")
        
        return True
    except Exception as e:
        print(f"❌ Basic pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧠 IETF Weavers - Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_email_parsing,
        test_sample_data,
        test_basic_pipeline
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All basic tests passed! You can try running the full pipeline.")
        print("To run with sample data: python src/main.py data/sample_emails.json")
    else:
        print("❌ Some tests failed. Check the error messages above.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
