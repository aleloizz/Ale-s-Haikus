#!/usr/bin/env python3
"""
Test script per verificare che tutte le funzionalità principali del sito siano intatte
dopo le modifiche CLS.
"""
import requests
import json
import time
import urllib3

# Disabilita i warning SSL per il test locale
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "http://127.0.0.1:5000"

def test_homepage():
    """Test che la homepage si carichi senza errori"""
    print("🔍 Testing homepage...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        assert response.status_code == 200, f"Homepage failed with status {response.status_code}"
        
        # Verifica che elementi critici siano presenti nell'HTML
        content = response.text
        critical_elements = [
            'id="patternDisplay"',
            'id="poemText"',
            'id="poemType"',
            'id="submitBtn"',
            'class="card"'
        ]
        
        for element in critical_elements:
            assert element in content, f"Missing critical element: {element}"
            
        print("✅ Homepage loads correctly with all critical elements")
        return True
    except Exception as e:
        print(f"❌ Homepage test failed: {e}")
        return False

def test_static_files():
    """Test che i file statici si carichino"""
    print("🔍 Testing static files...")
    try:
        static_files = [
            "/static/css/main.css",
            "/static/css/critical.css", 
            "/static/js/main.js",
            "/static/js/patterns.js",
            "/static/js/form.js"
        ]
        
        for file_path in static_files:
            response = requests.get(BASE_URL + file_path, timeout=5)
            assert response.status_code == 200, f"Static file {file_path} failed with status {response.status_code}"
            
        print("✅ All critical static files load correctly")
        return True
    except Exception as e:
        print(f"❌ Static files test failed: {e}")
        return False

def test_api_analyze():
    """Test dell'API di analisi"""
    print("🔍 Testing API analyze endpoint...")
    try:
        # Test haiku valido
        haiku_data = {
            "type": "haiku",
            "text": "Fiori che cadono\nSul sentiero di montagna\nSilenzio profondo",
            "use_tolerance": False
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/analyze", 
                               data=json.dumps(haiku_data), 
                               headers=headers, timeout=10)
        
        assert response.status_code == 200, f"API failed with status {response.status_code}"
        
        result = response.json()
        assert "results" in result, "Missing results in API response"
        assert "valid" in result, "Missing valid field in API response"
        assert len(result["results"]) == 3, "Wrong number of verses in haiku analysis"
        
        print("✅ API analyze endpoint works correctly")
        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_bacheca_page():
    """Test che la pagina bacheca si carichi"""
    print("🔍 Testing bacheca page...")
    try:
        response = requests.get(f"{BASE_URL}/bacheca", timeout=10)
        assert response.status_code == 200, f"Bacheca failed with status {response.status_code}"
        print("✅ Bacheca page loads correctly")
        return True
    except Exception as e:
        print(f"❌ Bacheca test failed: {e}")
        return False

def main():
    """Esegue tutti i test"""
    print("🚀 Starting comprehensive functionality tests...")
    print("=" * 50)
    
    # Attendi che l'app sia completamente avviata
    print("⏳ Waiting for app to be ready...")
    time.sleep(2)
    
    tests = [
        test_homepage,
        test_static_files,
        test_api_analyze,
        test_bacheca_page
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! The site functionality is intact.")
        print("✅ Safe to commit CLS optimizations.")
    else:
        print("⚠️  Some tests failed. Review before committing.")
    
    return failed == 0

if __name__ == "__main__":
    main()
