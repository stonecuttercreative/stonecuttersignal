#!/usr/bin/env python3
"""
Test script to demonstrate the new provider arbitration system.
Shows how multiple LLM providers work together to generate consensus scores.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.stonecutter.providers.registry import load_panel
from src.stonecutter.arbitration.core import arbitrate

async def demo_provider_system():
    """Demonstrate the provider system working with mock responses."""
    print("🔧 Testing Provider System")
    print("=" * 50)
    
    # Load all enabled providers
    panel = load_panel()
    print(f"📊 Loaded {len(panel)} providers:")
    for provider in panel:
        print(f"  • {provider.name}")
    
    print("\n🎯 Running test prompt...")
    prompt = """
    Brand: Tesla
    Category: Automotive  
    Concept: Sustainable transport revolution
    Mode: Real-time
    Audience: eco-conscious professionals
    Channels: TV, YouTube, Instagram
    
    Analyze this campaign for cultural fit, clarity, emotional resonance, differentiation, conversation fit, and distribution fit.
    """
    
    # Call all providers
    responses = []
    for provider in panel:
        try:
            response = await provider.complete(prompt)
            response["_provider_name"] = provider.name
            responses.append(response)
            print(f"✅ {provider.name}: {response['scores']}")
        except Exception as e:
            print(f"❌ {provider.name}: {e}")
    
    if responses:
        print(f"\n🎲 Arbitrating {len(responses)} responses...")
        final_result = arbitrate(responses)
        
        print("📊 Final Arbitrated Scores:")
        for key, value in final_result['scores'].items():
            print(f"  {key}: {value}")
        
        print(f"\n🎯 Confidence: {final_result['confidence']}")
        print(f"🏷️  Cluster: {final_result['cluster']}")
        print(f"🎭 Archetype: {final_result['archetype']}")
        
        if final_result.get('contradictions'):
            print(f"⚠️  Contradictions: {final_result['contradictions']}")
    else:
        print("❌ No provider responses received")

if __name__ == "__main__":
    asyncio.run(demo_provider_system())