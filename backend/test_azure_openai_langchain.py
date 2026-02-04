"""Test script to verify Azure OpenAI and LangChain integration."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test if LangChain packages can be imported."""
    print("=" * 60)
    print("TEST 1: Testing LangChain Imports")
    print("=" * 60)
    
    try:
        from langchain_openai import ChatOpenAI, AzureChatOpenAI
        print("[PASS] Successfully imported ChatOpenAI and AzureChatOpenAI")
        return True
    except ImportError as e:
        print(f"[FAIL] Failed to import LangChain OpenAI: {e}")
        print("   Make sure langchain-openai is installed: pip install langchain-openai")
        return False

def test_langchain_version():
    """Test LangChain version."""
    print("\n" + "=" * 60)
    print("TEST 2: Checking LangChain Versions")
    print("=" * 60)
    
    try:
        import langchain
        import langchain_openai
        print(f"[PASS] LangChain version: {langchain.__version__}")
        print(f"[PASS] LangChain OpenAI version: {langchain_openai.__version__}")
        return True
    except Exception as e:
        print(f"[FAIL] Error checking versions: {e}")
        return False

def test_azure_openai_config():
    """Test Azure OpenAI configuration."""
    print("\n" + "=" * 60)
    print("TEST 3: Checking Azure OpenAI Configuration")
    print("=" * 60)
    
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    
    print(f"Azure Endpoint: {'[SET]' if azure_endpoint else '[NOT SET]'}")
    print(f"Azure API Key: {'[SET]' if azure_api_key else '[NOT SET]'}")
    print(f"Azure Deployment: {'[SET]' if azure_deployment else '[NOT SET]'}")
    
    if azure_endpoint and azure_api_key and azure_deployment:
        print("\n[PASS] Azure OpenAI configuration is complete")
        return True, "azure"
    else:
        print("\n[WARN] Azure OpenAI configuration is incomplete")
        return False, None

def test_openai_config():
    """Test standard OpenAI configuration."""
    print("\n" + "=" * 60)
    print("TEST 4: Checking Standard OpenAI Configuration")
    print("=" * 60)
    
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    print(f"OpenAI API Key: {'[SET]' if openai_api_key else '[NOT SET]'}")
    
    if openai_api_key:
        print("\n[PASS] Standard OpenAI configuration is complete")
        return True, "openai"
    else:
        print("\n[WARN] Standard OpenAI configuration is incomplete")
        return False, None

def test_azure_openai_connection():
    """Test Azure OpenAI connection via LangChain."""
    print("\n" + "=" * 60)
    print("TEST 5: Testing Azure OpenAI Connection")
    print("=" * 60)
    
    try:
        from langchain_openai import AzureChatOpenAI
        
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip('/')
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
        
        if not all([azure_endpoint, azure_api_key, azure_deployment]):
            print("[SKIP] Azure OpenAI credentials not configured. Skipping connection test.")
            return False
        
        print(f"Initializing AzureChatOpenAI...")
        print(f"  Endpoint: {azure_endpoint}")
        print(f"  Deployment: {azure_deployment}")
        
        llm = AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment,
            openai_api_version="2024-02-15-preview",
            api_key=azure_api_key,
            temperature=0,
            model=azure_deployment,
        )
        
        print("[PASS] AzureChatOpenAI initialized successfully")
        
        # Test a simple invocation
        print("\nTesting simple invocation...")
        response = llm.invoke("Say 'Azure OpenAI is working!' in one sentence.")
        
        # Handle response
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)
        
        print(f"[PASS] Response received: {content[:100]}...")
        print("\n[PASS] Azure OpenAI connection test PASSED")
        return True
        
    except Exception as e:
        print(f"[FAIL] Azure OpenAI connection test FAILED: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return False

def test_openai_connection():
    """Test standard OpenAI connection via LangChain."""
    print("\n" + "=" * 60)
    print("TEST 6: Testing Standard OpenAI Connection")
    print("=" * 60)
    
    try:
        from langchain_openai import ChatOpenAI
        
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        if not openai_api_key:
            print("[SKIP] OpenAI API key not configured. Skipping connection test.")
            return False
        
        print("Initializing ChatOpenAI...")
        print("  Model: gpt-4-turbo-preview")
        
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4-turbo-preview",
            api_key=openai_api_key,
        )
        
        print("[PASS] ChatOpenAI initialized successfully")
        
        # Test a simple invocation
        print("\nTesting simple invocation...")
        response = llm.invoke("Say 'OpenAI is working!' in one sentence.")
        
        # Handle response
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)
        
        print(f"[PASS] Response received: {content[:100]}...")
        print("\n[PASS] Standard OpenAI connection test PASSED")
        return True
        
    except Exception as e:
        print(f"[FAIL] Standard OpenAI connection test FAILED: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return False

def test_clusteriq_agent():
    """Test ClusterIQAgent initialization and basic functionality."""
    print("\n" + "=" * 60)
    print("TEST 7: Testing ClusterIQAgent")
    print("=" * 60)
    
    try:
        from ai_agent import ClusterIQAgent
        
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Try Azure OpenAI first, then standard OpenAI
        if azure_endpoint and azure_api_key and azure_deployment:
            print("Initializing ClusterIQAgent with Azure OpenAI...")
            agent = ClusterIQAgent(
                azure_endpoint=azure_endpoint,
                azure_api_key=azure_api_key,
                azure_deployment_name=azure_deployment,
                model="gpt-4-turbo-preview"
            )
            print("[PASS] ClusterIQAgent initialized with Azure OpenAI")
        elif openai_api_key:
            print("Initializing ClusterIQAgent with standard OpenAI...")
            agent = ClusterIQAgent(
                api_key=openai_api_key,
                model="gpt-4-turbo-preview"
            )
            print("[PASS] ClusterIQAgent initialized with standard OpenAI")
        else:
            print("[SKIP] No OpenAI credentials configured. Cannot test ClusterIQAgent.")
            return False
        
        # Test with minimal data
        print("\nTesting agent with sample data...")
        test_jobs = [{"job_id": 1, "job_name": "Test Job"}]
        test_clusters = [{"cluster_id": "test-123", "cluster_name": "Test Cluster", "state": "RUNNING"}]
        
        recommendations = agent.analyze_jobs_and_clusters(
            jobs=test_jobs,
            clusters=test_clusters,
            job_runs={}
        )
        
        print(f"[PASS] Agent analysis completed: {len(recommendations)} recommendations generated")
        if recommendations:
            print(f"   Sample recommendation: {recommendations[0].get('title', 'N/A')[:50]}...")
        
        print("\n[PASS] ClusterIQAgent test PASSED")
        return True
        
    except Exception as e:
        print(f"[FAIL] ClusterIQAgent test FAILED: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ClusterIQ - Azure OpenAI & LangChain Integration Test")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Imports
    results['imports'] = test_imports()
    if not results['imports']:
        print("\n[CRITICAL] LangChain imports failed. Please install dependencies.")
        print("   Run: pip install langchain langchain-openai")
        return
    
    # Test 2: Versions
    results['versions'] = test_langchain_version()
    
    # Test 3 & 4: Configuration
    azure_configured, azure_type = test_azure_openai_config()
    openai_configured, openai_type = test_openai_config()
    results['azure_config'] = azure_configured
    results['openai_config'] = openai_configured
    
    # Test 5: Azure OpenAI Connection
    if azure_configured:
        results['azure_connection'] = test_azure_openai_connection()
    else:
        results['azure_connection'] = False
        print("\n[SKIP] Skipping Azure OpenAI connection test (not configured)")
    
    # Test 6: Standard OpenAI Connection
    if openai_configured:
        results['openai_connection'] = test_openai_connection()
    else:
        results['openai_connection'] = False
        print("\n[SKIP] Skipping standard OpenAI connection test (not configured)")
    
    # Test 7: ClusterIQAgent
    if azure_configured or openai_configured:
        results['agent'] = test_clusteriq_agent()
    else:
        results['agent'] = False
        print("\n[SKIP] Skipping ClusterIQAgent test (no OpenAI credentials)")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    print(f"LangChain Imports:        {'[PASS]' if results['imports'] else '[FAIL]'}")
    print(f"LangChain Versions:       {'[PASS]' if results['versions'] else '[FAIL]'}")
    print(f"Azure OpenAI Config:      {'[PASS]' if results['azure_config'] else '[NOT CONFIGURED]'}")
    print(f"Standard OpenAI Config:   {'[PASS]' if results['openai_config'] else '[NOT CONFIGURED]'}")
    print(f"Azure OpenAI Connection:  {'[PASS]' if results['azure_connection'] else '[FAIL/SKIP]'}")
    print(f"Standard OpenAI Connect:  {'[PASS]' if results['openai_connection'] else '[FAIL/SKIP]'}")
    print(f"ClusterIQAgent Test:      {'[PASS]' if results['agent'] else '[FAIL/SKIP]'}")
    
    # Overall status
    critical_tests = ['imports', 'versions']
    connection_tests = ['azure_connection', 'openai_connection']
    
    critical_passed = all(results.get(k, False) for k in critical_tests)
    any_connection_works = any(results.get(k, False) for k in connection_tests)
    
    print("\n" + "=" * 60)
    if critical_passed and any_connection_works:
        print("[PASS] OVERALL STATUS: PASSED")
        print("   LangChain is working and at least one OpenAI connection is functional.")
    elif critical_passed:
        print("[PARTIAL] OVERALL STATUS: PARTIAL")
        print("   LangChain is working but OpenAI connections need configuration.")
    else:
        print("[FAIL] OVERALL STATUS: FAILED")
        print("   Critical tests failed. Please check your setup.")
    print("=" * 60)

if __name__ == "__main__":
    main()
