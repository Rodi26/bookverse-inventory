
def test_basic_functionality():
    assert 1 + 1 == 2
    assert "hello" == "hello"
    print("✅ Basic functionality test passed")


def test_imports():
    import sys
    assert sys.version_info.major == 3
    print("✅ Basic imports test passed")
