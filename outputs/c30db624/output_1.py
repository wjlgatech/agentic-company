if math.isinf(minuend) and math.isinf(subtrahend) and minuend == subtrahend:
    raise ValueError("Cannot subtract infinity from infinity (indeterminate result)")