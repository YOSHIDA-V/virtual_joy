# SHUTDOWN-TK-SIGINT-001
Observed: normal launch SIGINT interrupts Tk _refresh_ui -> redraw -> delete('all'), producing KeyboardInterrupt callback traceback. Children returning zero does not satisfy clean shutdown.
Target: Ubuntu 24.04 / ROS 2 Jazzy / domain 100, local-only discovery, private namespace, no hardware or user input.
Baseline runtime: virtual_joy 1f0e33ebb5378af7c3e841edd1cd9bffc98d2051; docs checkpoint efc8f59872644dc390f7fa200b876232d0dc1e28 has identical production code.
Reproducer: test_sigint_during_tk_redraw_has_no_callback_exception sends SIGINT to itself during a real Tk redraw callback; requires callback errors=[] and signal delivered.
Allowed production change: virtual_joy_node.py shutdown/signal lifecycle only. Preserve UI, Joy mappings/rates, rover converter and Humble/main.
Acceptance: reproducer passes, existing tests pass, ordinary launch SIGINT and restart have no traceback/escalation/residual child and unchanged idle publication criteria.
State: REPRODUCED by preserved runtime; deterministic test execution is recorded separately before production edit.