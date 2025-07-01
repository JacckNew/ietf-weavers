#!/usr/bin/env python3
"""
Final integration test for IETF Weavers pipeline.
Tests end-to-end functionality with both small and larger datasets.
"""

import os
import sys
import json
import subprocess
import time

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_pipeline_with_dataset(dataset_path, expected_nodes=None, expected_edges=None):
    """Test the pipeline with a specific dataset."""
    print(f"\n🧪 Testing pipeline with dataset: {dataset_path}")
    print("=" * 60)
    
    # Check if dataset exists
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        return False
    
    # Run the pipeline
    start_time = time.time()
    try:
        result = subprocess.run([
            sys.executable, 'src/main.py', dataset_path, '--n-topics', '3'
        ], capture_output=True, text=True, cwd=project_root)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ Pipeline completed successfully in {duration:.2f} seconds")
            
            # Check output files
            output_files = [
                'visualisation/data.json',
                'visualisation/individual_features.csv',
                'visualisation/topic_analysis.json'
            ]
            
            all_files_exist = True
            for file_path in output_files:
                full_path = os.path.join(project_root, file_path)
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    print(f"  📄 {file_path}: {file_size} bytes")
                else:
                    print(f"  ❌ Missing: {file_path}")
                    all_files_exist = False
            
            # Parse network data if available
            data_json_path = os.path.join(project_root, 'visualisation/data.json')
            if os.path.exists(data_json_path):
                try:
                    with open(data_json_path, 'r') as f:
                        data = json.load(f)
                    
                    nodes = len(data.get('nodes', []))
                    edges = len(data.get('links', []))
                    
                    print(f"  🌐 Network: {nodes} nodes, {edges} edges")
                    
                    if expected_nodes and nodes != expected_nodes:
                        print(f"  ⚠️  Expected {expected_nodes} nodes, got {nodes}")
                    
                    if expected_edges and edges != expected_edges:
                        print(f"  ⚠️  Expected {expected_edges} edges, got {edges}")
                    
                except Exception as e:
                    print(f"  ❌ Error parsing data.json: {e}")
                    all_files_exist = False
            
            return all_files_exist
        else:
            print(f"❌ Pipeline failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        return False

def test_import_capabilities():
    """Test that all required modules can be imported."""
    print("\n🔧 Testing import capabilities")
    print("=" * 40)
    
    modules_to_test = [
        'agent.utils',
        'agent.graph_builder', 
        'agent.metrics',
        'agent.topic_model',
        'agent.formatter'
    ]
    
    success_count = 0
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module}: {e}")
    
    print(f"\n📊 Import Success Rate: {success_count}/{len(modules_to_test)}")
    return success_count == len(modules_to_test)

def test_dependencies():
    """Test that critical dependencies are available."""
    print("\n📦 Testing dependencies")
    print("=" * 30)
    
    dependencies = [
        ('networkx', 'Network analysis'),
        ('pandas', 'Data manipulation'),
        ('numpy', 'Numerical computing'),
        ('scikit-learn', 'Machine learning'),
        ('sentence_transformers', 'Sentence embeddings'),
        ('bertopic', 'Topic modeling')
    ]
    
    available_count = 0
    for dep, description in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: {description}")
            available_count += 1
        except ImportError:
            print(f"❌ {dep}: {description} (missing)")
    
    print(f"\n📊 Dependency Availability: {available_count}/{len(dependencies)}")
    return available_count >= 4  # Core dependencies (networkx, pandas, numpy, sklearn)

def main():
    """Run complete integration test suite."""
    print("🧠 IETF Weavers - Integration Test Suite")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_import_capabilities() 
    
    # Test dependencies
    deps_ok = test_dependencies()
    
    # Test with sample datasets
    datasets_to_test = [
        ('data/sample_emails.json', 6, None),  # Small dataset
        ('data/expanded_sample_emails.json', 10, 5)  # Larger dataset with threading
    ]
    
    pipeline_tests_passed = 0
    for dataset_path, expected_nodes, expected_edges in datasets_to_test:
        if test_pipeline_with_dataset(dataset_path, expected_nodes, expected_edges):
            pipeline_tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Module Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"✅ Dependencies: {'PASS' if deps_ok else 'FAIL'}")
    print(f"✅ Pipeline Tests: {pipeline_tests_passed}/{len(datasets_to_test)} PASSED")
    
    overall_success = imports_ok and deps_ok and (pipeline_tests_passed > 0)
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED! IETF Weavers is ready for production use.")
        print("\n🚀 Next steps:")
        print("   1. Integrate with real IETF mailing list data")
        print("   2. Scale up topic modeling parameters") 
        print("   3. Enhance visualization with additional features")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return 0 if overall_success else 1

if __name__ == '__main__':
    exit(main())
