import math

# a few maths things used often


def to_radians(degrees):
    return degrees * math.pi / 180


def sign(number):
    if number >= 0:
        return 1
    else:
        return - 1


def to_degrees(radians):
    return radians * 180 / math.pi
