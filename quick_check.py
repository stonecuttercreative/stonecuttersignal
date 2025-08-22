#!/usr/bin/env python3
"""
Quick validation script for Stonecutter Signal extensions.
Tests the new optional audience/channels intake and scoring behavior.
"""

import json
from stonecutter import run_signal_engine

def test_legacy_string_input():
    """Test 1: Legacy plain string input"""
    print("Test 1: Legacy plain string input...")
    
    brief = "Brand: Nike\nCategory: Athletic Apparel\nConcept: Just Do It campaign focusing on athletic achievement\nMode: Real-time"
    
    result = run_signal_engine(brief, interactive_mode=False)
    
    # Check conversation_fit is present
    scores = result.get('signal_scores', {}).get('scores', {})
    assert 'conversation_fit' in scores, "conversation_fit missing from scores"
    
    # Check distribution_fit is absent
    assert 'distribution_fit' not in scores, "distribution_fit should be absent for legacy input"
    
    # Check notes about distribution_fit
    notes = result.get('signal_scores', {}).get('notes', {})
    assert 'distribution_fit' in notes, "distribution_fit note missing"
    assert "not evaluated" in notes['distribution_fit'].lower(), "Missing 'not evaluated' message"
    
    print("✓ Test 1 passed")
    return True

def test_dict_input_audience_only():
    """Test 2: Dict input with audience only"""
    print("Test 2: Dict input with audience only...")
    
    brief = {
        "brand": "Apple",
        "category": "Technology", 
        "concept": "Privacy-focused iPhone campaign highlighting user data protection",
        "mode": "real-time",
        "audience": "privacy-conscious millennials"
    }
    
    result = run_signal_engine(brief, interactive_mode=False)
    
    # Check conversation_fit is present
    scores = result.get('signal_scores', {}).get('scores', {})
    assert 'conversation_fit' in scores, "conversation_fit missing from scores"
    
    # Check distribution_fit is absent
    assert 'distribution_fit' not in scores, "distribution_fit should be absent when channels not provided"
    
    # Check audience shows up in output
    audience_found = (
        'audience_note' in result or 
        any('privacy-conscious millennials' in str(v) for v in result.values())
    )
    assert audience_found, "Audience information not found in output"
    
    print("✓ Test 2 passed")
    return True

def test_dict_input_audience_and_channels():
    """Test 3: Dict input with audience and channels"""
    print("Test 3: Dict input with audience and channels...")
    
    brief = {
        "brand": "Tesla",
        "category": "Automotive",
        "concept": "Sustainable transport revolution campaign featuring Model Y",
        "mode": "real-time", 
        "audience": "eco-conscious professionals",
        "channels": "TV, YouTube, Instagram, Tesla website"
    }
    
    result = run_signal_engine(brief, interactive_mode=False)
    
    # Check conversation_fit is present
    scores = result.get('signal_scores', {}).get('scores', {})
    assert 'conversation_fit' in scores, "conversation_fit missing from scores"
    
    # Check distribution_fit is present and in valid range
    assert 'distribution_fit' in scores, "distribution_fit missing when channels provided"
    dist_fit = scores['distribution_fit']
    assert 0 <= dist_fit <= 100, f"distribution_fit {dist_fit} not in range 0-100"
    
    print("✓ Test 3 passed")
    return True

def main():
    """Run all validation checks"""
    print("Running Stonecutter Signal validation checks...\n")
    
    try:
        test_legacy_string_input()
        test_dict_input_audience_only()
        test_dict_input_audience_and_channels()
        
        print("\n🎉 All checks passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Check failed: {e}")
        return False

if __name__ == "__main__":
    main()