import math, random
import pygame
from sprites import EnemyBullet

from extramath import to_radians, to_degrees, sign
from pygameextras import play_sound


# module containing bullet generating functions, and enemy attack patterns


# fires a ring of n bullets from (x,y), offset rotates the ring,
# accel changes the bullets' speed over time
def fire_circle(groups, x, y, n, speed, image, accel=0, offset=0, gravity=0):
    angle = offset
    increment = 360 / n
    for a in range(n):
        EnemyBullet(groups, x, y, speed * math.cos(to_radians(angle)),
                    speed * math.sin(to_radians(angle)), image,
                    accelx=accel * math.cos(to_radians(angle)),
                    accely=gravity + accel * math.sin(to_radians(angle)))
        angle += increment


# fires a bullet from (x,y) in the direction of the player
def fire_at_player(groups, x, y, speed, image):
    targetx = groups.koishi.sprite.rect.centerx
    targety = groups.koishi.sprite.rect.centery
    try:
        angle = to_degrees(math.atan(math.fabs((targety - y) / (targetx - x))))
        if targetx - x < 0 and targety - y < 0:
            angle = 180 + angle
        elif targetx - x < 0 <= targety - y:
            angle = 180 - angle
        elif targetx - x > 0 > targety - y:
            angle = 360 - angle
    except ZeroDivisionError:
        angle = 180 + 90 * -sign(targety - y)

    fire_circle(groups, x, y, 1, speed, image, offset=angle, accel=0)


# generic attack patterns available for enemies in regular levels
# pattern is given as part of the level definition


# fires a circle of n bullets every *delay* ticks
def pattern1(firer, assets, image, n, offset, delay, bspeed):
    if firer.counter % delay == 0:
        play_sound(assets.attack1)
        firer.counter -= delay
        fire_circle(firer.groups, firer.rect.centerx, firer.rect.centery,
                    n, bspeed, image, offset=offset)


# fires a bullet at the player every *delay* ticks
def pattern2(firer, assets, image, bspeed, delay):
    if firer.counter % delay == 0:
        play_sound(assets.attack1)
        firer.counter -= delay
        fire_at_player(firer.groups, firer.rect.centerx, firer.rect.centery,
                       bspeed, image)


# fires bullets around a spiral
# set bangle = 0 for straight line firing
def pattern3(firer, assets, image, bspeed, bangle, rate):
    if firer.counter % rate == 0:
        fire_circle(firer.groups, firer.rect.centerx, firer.rect.centery,
                    1, bspeed, image, offset=bangle*firer.counter/rate)


# fires bullets indiscriminately
def pattern4(firer, assets, image, bspeed, rate, accel):
    if firer.counter % rate == 0:
        fire_circle(firer.groups, firer.rect.centerx, firer.rect.centery,
                    1, bspeed, image, offset=random.randint(0,360),accel=accel)
