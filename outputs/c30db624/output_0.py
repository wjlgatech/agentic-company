MAX_SAFE_INTEGER = 2**53 - 1  # JavaScript-like safe integer limit
if abs(minuend) > MAX_SAFE_INTEGER or abs(subtrahend) > MAX_SAFE_INTEGER:
    raise ValueError("Input values exceed safe computation limits")