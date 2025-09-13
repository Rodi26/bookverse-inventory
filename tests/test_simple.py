"""Simple test that doesn't require complex dependencies."""

def test_basic_functionality():
    """Test basic Python functionality."""
    assert 1 + 1 == 2
    assert "hello" == "hello"
    print("✅ Basic functionality test passed")

def test_imports():
    """Test that we can import basic modules."""
    import sys
    import os
    import json
    assert sys.version_info.major == 3
    print("✅ Basic imports test passed")
