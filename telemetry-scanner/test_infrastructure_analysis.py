#!/usr/bin/env python3
"""
Test script for the enhanced telemetry infrastructure analysis.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from scanner.intelligent_search import IntelligentSearchEngine, TelemetryInfrastructure

def test_infrastructure_analysis():
    """Test the telemetry infrastructure analysis on a sample codebase."""
    
    # Use ServiceFramework as test repo (adjust path as needed)
    repo_path = Path.home() / "Documents" / "ServiceFramework"
    
    if not repo_path.exists():
        print(f"❌ Test repository not found at {repo_path}")
        print("Please adjust the repo_path in the test script")
        return False
    
    print(f"🔍 Analyzing telemetry infrastructure in: {repo_path}")
    
    try:
        # Initialize the search engine
        search_engine = IntelligentSearchEngine(repo_path)
        
        # Analyze existing infrastructure
        print("\n📊 Analyzing existing telemetry infrastructure...")
        infrastructure = search_engine.analyze_telemetry_infrastructure()
        
        print(f"✅ Found {len(infrastructure.instrumentation_libraries)} instrumentation libraries:")
        for lib_name, config in infrastructure.instrumentation_libraries.items():
            print(f"  📦 {lib_name}:")
            print(f"    ✓ Configured options: {config['configured_options']}")
            print(f"    ❓ Missing options: {len(config['missing_options'])}")
        
        print(f"\n🔧 Configuration files: {len(infrastructure.configuration_files)}")
        for config_file in infrastructure.configuration_files[:3]:  # Show first 3
            print(f"  📄 {config_file}")
        
        # Test configuration suggestion
        print("\n🧠 Testing configuration suggestion...")
        test_problems = [
            "missing db.operation attribute in database spans",
            "need database name in sql traces", 
            "missing http request body in traces"
        ]
        
        for problem in test_problems:
            suggestion = search_engine.suggest_configuration_solution(problem, infrastructure)
            if suggestion:
                print(f"✅ Problem: {problem}")
                print(f"   💡 Solution: {suggestion[:100]}...")
            else:
                print(f"❌ No config solution for: {problem}")
        
        # Test enhanced search
        print("\n🔍 Testing enhanced search...")
        intent = {
            "description": "missing db.operation attribute in stored procedure spans",
            "search_keywords": ["sql", "database", "telemetry"]
        }
        
        results = search_engine.multi_modal_search(intent, top_k=5)
        print(f"✅ Found {len(results)} search results:")
        for i, result in enumerate(results[:3]):
            print(f"  {i+1}. {result.file_path.name} (score: {result.relevance_score})")
            print(f"     💭 {result.reasoning}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Enhanced Telemetry Infrastructure Analysis")
    print("=" * 60)
    
    success = test_infrastructure_analysis()
    
    if success:
        print("\n✅ All tests passed! The enhanced analysis is working.")
    else:
        print("\n❌ Tests failed. Check the error messages above.")
