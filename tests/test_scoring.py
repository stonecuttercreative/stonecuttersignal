# BEGIN stonecutter extension: scoring tests
import pytest
from src.stonecutter.scoring.index import compute_signal_scores

def test_high_consensus_scores():
    """Test that identical responses produce high consensus and low diversity."""
    # Identical provider responses
    panel_responses = [
        {
            "_provider_name": "provider1",
            "scores": {"cultural_fit": 80, "clarity": 85, "emotional_resonance": 75},
            "_telemetry": {"latency_ms": 100, "model": "test-model"}
        },
        {
            "_provider_name": "provider2", 
            "scores": {"cultural_fit": 80, "clarity": 85, "emotional_resonance": 75},
            "_telemetry": {"latency_ms": 150, "model": "test-model"}
        }
    ]
    
    final_scores = {"cultural_fit": 80, "clarity": 85, "emotional_resonance": 75}
    
    result = compute_signal_scores(panel_responses, final_scores)
    
    assert result["diversity"] <= 10, f"Expected low diversity, got {result['diversity']}"
    assert result["consensus"] >= 90, f"Expected high consensus, got {result['consensus']}"
    assert result["confidence"] >= 90, f"Expected high confidence, got {result['confidence']}"
    assert 0 <= result["confidence"] <= 100
    assert 0 <= result["diversity"] <= 100
    assert 0 <= result["consensus"] <= 100

def test_low_consensus_scores():
    """Test that divergent responses produce low consensus and high diversity."""
    # Divergent provider responses
    panel_responses = [
        {
            "_provider_name": "provider1",
            "scores": {"cultural_fit": 20, "clarity": 30, "emotional_resonance": 25},
            "_telemetry": {"latency_ms": 100, "model": "test-model"}
        },
        {
            "_provider_name": "provider2",
            "scores": {"cultural_fit": 90, "clarity": 95, "emotional_resonance": 85}, 
            "_telemetry": {"latency_ms": 150, "model": "test-model"}
        },
        {
            "_provider_name": "provider3",
            "scores": {"cultural_fit": 50, "clarity": 60, "emotional_resonance": 45},
            "_telemetry": {"latency_ms": 120, "model": "test-model"}
        }
    ]
    
    final_scores = {"cultural_fit": 53, "clarity": 62, "emotional_resonance": 52}
    
    result = compute_signal_scores(panel_responses, final_scores)
    
    assert result["diversity"] > 20, f"Expected high diversity, got {result['diversity']}"
    assert result["consensus"] < 80, f"Expected low consensus, got {result['consensus']}"
    assert 0 <= result["confidence"] <= 100
    assert 0 <= result["diversity"] <= 100
    assert 0 <= result["consensus"] <= 100

def test_single_provider():
    """Test single provider case returns expected defaults."""
    panel_responses = [
        {
            "_provider_name": "provider1",
            "scores": {"cultural_fit": 75, "clarity": 80},
            "_telemetry": {"latency_ms": 100, "model": "test-model"}
        }
    ]
    
    final_scores = {"cultural_fit": 75, "clarity": 80}
    
    result = compute_signal_scores(panel_responses, final_scores)
    
    assert result["confidence"] == 60
    assert result["diversity"] == 10
    assert result["consensus"] == 90
    assert result["notes"]["method"] == "single_provider"

def test_empty_input():
    """Test empty input returns expected defaults."""
    result = compute_signal_scores([], {})
    
    assert result["confidence"] == 60
    assert result["diversity"] == 10
    assert result["consensus"] == 90
    assert result["notes"]["method"] == "no_data"

def test_latency_downweighting():
    """Test that high latency providers are slightly downweighted."""
    # One fast provider, one very slow provider
    panel_responses = [
        {
            "_provider_name": "fast_provider",
            "scores": {"cultural_fit": 80},
            "_telemetry": {"latency_ms": 100, "model": "test-model"}
        },
        {
            "_provider_name": "slow_provider", 
            "scores": {"cultural_fit": 20},
            "_telemetry": {"latency_ms": 2000, "model": "test-model"}  # Very slow
        }
    ]
    
    final_scores = {"cultural_fit": 50}
    
    result = compute_signal_scores(panel_responses, final_scores)
    
    # Should have valid metrics despite large disagreement
    assert 0 <= result["confidence"] <= 100
    assert result["notes"]["method"] == "mad_based"
# END stonecutter extension