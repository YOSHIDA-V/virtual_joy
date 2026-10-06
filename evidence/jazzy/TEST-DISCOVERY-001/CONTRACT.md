# TEST-DISCOVERY-001

`colcon test --packages-select virtual_joy` ran zero tests and exited 5.
The existing nine tests pass with explicit unittest discovery.
Inspected local Jazzy colcon_core/task/python/test/pytest.py selects pytest
only when has_test_dependency(setup_py_data, 'pytest') is true. setup.py
omits that test dependency and falls back to unittest discovery.

One cause/change: declare the existing test runner in package metadata.
Criteria: the ordinary colcon test command discovers and passes all nine
existing tests, junit XML contains nine tests and no failures/errors,
and colcon test-result succeeds. Runtime and tests remain unchanged.
