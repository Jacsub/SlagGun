def clamp(val:float, min:float, max:float): # the math library didn't have a function to do this so 
    if val > max:                           # have to pick up their slack
        return max
    elif val < min:
        return min
    else:
        return val