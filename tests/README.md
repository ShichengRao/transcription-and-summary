# Test Suite

This directory contains the test suite for the transcription and summary application.

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run with coverage report
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_config.py
```

### Run specific test
```bash
pytest tests/test_config.py::TestAudioConfig::test_default_values
```

## Test Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_config.py` - Tests for configuration module
- `test_audio_capture.py` - Tests for audio capture functionality
- `test_summarization.py` - Tests for summarization service

## Fixtures

Common fixtures available in all tests (defined in `conftest.py`):

- `temp_dir` - Temporary directory for test files
- `test_config` - Test configuration with safe defaults
- `sample_transcript_text` - Sample transcript for testing
- `sample_audio_data` - Generated audio data for testing
- `mock_audio_segment` - Mock audio segment with test file

## Writing New Tests

1. Create a new file `test_<module_name>.py`
2. Import the module you want to test
3. Create test classes with `Test` prefix
4. Create test methods with `test_` prefix
5. Use fixtures from `conftest.py` or create new ones

Example:
```python
import pytest
from src.my_module import MyClass

class TestMyClass:
    def test_something(self, test_config):
        obj = MyClass(test_config)
        assert obj.do_something() == expected_result
```

## Test Markers

Use markers to categorize tests:

```python
@pytest.mark.slow
def test_long_running_operation():
    pass

@pytest.mark.integration
def test_api_integration():
    pass
```

Run specific markers:
```bash
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Run only integration tests
```
