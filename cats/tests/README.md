# Test Definitions

This folder contains **Test Definitions** that constitute the **AWS Pre-Built Test Pack** for the LZA Universal Configuration.

Test Definitions are Python files (`.py`) that validate AWS Landing Zone Accelerator controls and configurations, including the test cases themselves and the supporting Pytest fixtures and hooks they rely on. Each file is licensed under the Apache License, Version 2.0 (see the repository's LICENSE.txt).

## Contents

```
tests/
├── conftest.py              # Test Definition: Pytest fixtures and hooks
├── test_*.py                # Test Definitions for LZA control validation
└── scp/
    └── test_scp_*.py        # Test Definitions for Service Control Policy enforcement
```

## Usage

Tests are based on a consistent LZA Universal Configuration, which is then targeted by a CATS yaml file.
