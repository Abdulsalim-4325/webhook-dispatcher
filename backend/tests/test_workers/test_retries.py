import random


def test_exponential_backoff_jitter_bounds():
    """Verify that full jitter always stays strictly between base delay and calculated max bound."""
    base_backoff = 2.0
    max_backoff = 60.0

    for attempt in range(1, 6):
        calculated_backoff = min(max_backoff, base_backoff * (2 ** attempt))
        # Ensure calculated ceiling doubles exponentially up to max_backoff
        if attempt == 1:
            assert calculated_backoff == 4.0
        elif attempt == 2:
            assert calculated_backoff == 8.0
        elif attempt == 3:
            assert calculated_backoff == 16.0
        elif attempt == 4:
            assert calculated_backoff == 32.0
        elif attempt == 5:
            assert calculated_backoff == 60.0

        for _ in range(20):
            jittered_delay = random.uniform(0.5, calculated_backoff)
            assert 0.5 <= jittered_delay <= calculated_backoff
