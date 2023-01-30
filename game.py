import pygame, attacks, sprites, copy, random
from pygameextras import draw_text, play_sound, load_image
from dataclasses import dataclass

pygame.mixer.pre_init(44100, -16, 1, 512)

pygame.init()

DISPLAY = pygame.display.set_mode((900, 600))
pygame.display.set_caption("Game!")
pygame.display.set_icon(pygame.image.load("media/favicon.ico"))
CLOCK = pygame.time.Clock()

BG = (122, 217, 255)

# the current BGM
PLAYING = None


# for BGM only
def play_music(directory, volume=0.7):
    global PLAYING
    if PLAYING != directory:
        pygame.mixer.music.set_volume(volume)
        PLAYING = directory
        pygame.mixer.music.load(directory)
        pygame.mixer.music.play(-1)


# container for all the assets, easier to pass them around
@dataclass
class Assets:
    # misc
    koishiIcon = load_image("media/icons/koishi.png")
    coin = load_image("media/items/coin.png", scale=0.15)
    flag = load_image("media/items/flag.png", scale=0.1)
    backgrounds = []
    blueDiamond = load_image("media/items/bluediamond.png", scale=0.4)
    blueDiamondFull = load_image("media/items/bluediamond.png")
    greenDiamond = load_image("media/items/greenDiamond.png")
    shield = load_image("media/items/shield.png")

    # bullets
    heartl = load_image("media/bullets/heartbullet.png", rotate=90, scale=0.7)
    heartr = load_image("media/bullets/heartbullet.png", rotate=-90, scale=0.7)
    pinkCircle = load_image("media/bullets/pinkcircle.png")
    greenCircle = load_image("media/bullets/greencircle.png")
    yellowCircle = load_image("media/bullets/yellowcircle.png")
    redCircle = load_image("media/bullets/redcircle.png")
    blueCircle = load_image("media/bullets/bluecircle.png")

    # sounds
    attack1 = pygame.mixer.Sound("media/sound/bleep1.wav")
    attack2 = pygame.mixer.Sound("media/sound/ATTACK4.wav")
    attack3 = pygame.mixer.Sound("media/sound/ATTACK5.wav")
    attack4 = pygame.mixer.Sound("media/sound/ATTACK.wav")
    warn = pygame.mixer.Sound("media/sound/GUN.wav")
    endSound = pygame.mixer.Sound("media/sound/BONUS.wav")
    hitSound = pygame.mixer.Sound("media/sound/hit.wav")
    dieSound = pygame.mixer.Sound("media/sound/DEAD.wav")
    bossDieSound = pygame.mixer.Sound("media/sound/DEFEATED.wav")
    coinCollectSound = pygame.mixer.Sound("media/sound/BONUS2.wav")
    enemyDieSound = pygame.mixer.Sound("media/sound/TWINKLE3.wav")
    powerUpSound = pygame.mixer.Sound("media/sound/BONUS3.wav")


# contains all sprite groups, it is passed around a lot.
@dataclass
class GroupOfGroups:
    # the player sprite, Koishi.
    koishi = pygame.sprite.GroupSingle()

    name = ""
    coins = 0
    bgi = None

    allSprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    koishiBullets = pygame.sprite.Group()
    shields = pygame.sprite.Group()
    items = pygame.sprite.Group()
    friendlies = pygame.sprite.Group()
    floorSprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    # on screen things in their own group, as this is all that
    # gets updated and drawn
    onScreenEnemies = pygame.sprite.Group()
    onScreenPlatforms = pygame.sprite.Group()
    onScreenItems = pygame.sprite.Group()
    onScreenAll = pygame.sprite.Group()
    onScreenGaps = pygame.sprite.Group()

    # dummy sprites covering the info displays for easy updating that
    # region
    dummies = pygame.sprite.Group()

    # Anything not in this group remains stationary on the screen
    moveableSprites = pygame.sprite.Group()

    bossSprites = pygame.sprite.Group()
    gaps = pygame.sprite.Group()
    enemyBullets = pygame.sprite.Group()


# draws the HP display bar on the screen
def display_hp(groups):
    hp = groups.koishi.sprite.hp
    pygame.draw.rect(DISPLAY, (255, 255, 255), [15, 35, 370, 20], width=5)
    pygame.draw.rect(DISPLAY, (0, 255, 0), [20, 40, 60 * hp, 10])
    # rect [15, 35, 370, 20]


def display_shield_timer(groups):
    time = groups.koishi.sprite.shieldCountdown
    pygame.draw.rect(DISPLAY, (255, 0, 0), [20, 52, int(360 * time / 900), 2])


# draws all player stats on screen
def update_stats(groups):
    display_hp(groups)
    display_shield_timer(groups)
    draw_text(DISPLAY, groups.name, 10, 10)
    draw_text(DISPLAY, f"Coins: {groups.koishi.sprite.score}/{groups.coins}", 10, 60)
    for boss in groups.bossSprites:
        boss.display_hp(DISPLAY)


# logic to see if player is landing on a platform or falling
# through a gap
def platform_collisions(groups):
    hits = pygame.sprite.spritecollide(groups.koishi.sprite, groups.onScreenGaps, False)

    for hit in hits:
        if hit.rect.left <= groups.koishi.sprite.rect.left and hit.rect.right >= groups.koishi.sprite.rect.right:
            hits = []
            if isinstance(groups.koishi.sprite.platform, sprites.DroppingPlatform):
                hits = [groups.koishi.sprite.platform]
            break
    else:
        hits = pygame.sprite.spritecollide(groups.koishi.sprite, groups.onScreenPlatforms, False)

    # if on any platform, set koishi.platform to it, and fix speed she will fall off
    # otherwise set it to None
    for hit in hits:
        if groups.koishi.sprite.yvel >= 0 and (hit.rect.top - groups.koishi.sprite.yvel - 2 <=
                                               groups.koishi.sprite.rect.bottom <=
                                               2 + hit.rect.top + groups.koishi.sprite.yvel):
            groups.koishi.sprite.platform = hit
            groups.koishi.sprite.rect.bottom = hit.rect.top + 1
            groups.koishi.sprite.yvel = 3
            break
    else:
        groups.koishi.sprite.platform = None


# logic for damage
def damage_collisions(groups, assets):
    # koishi cannot shoot through platforms
    pygame.sprite.groupcollide(groups.koishiBullets, groups.onScreenPlatforms, True, False)

    # koishi's bullets that are hitting enemies
    for hit in pygame.sprite.groupcollide(groups.onScreenEnemies, groups.koishiBullets, False, True):
        hit.hp -= 1
        if hit.hp <= 0 and hit in groups.bossSprites:
            play_sound(assets.bossDieSound)
            sprites.Coin(groups, assets, hit.rect.centerx, hit.rect.bottom - 10)
            sprites.run_dialogue(groups, CLOCK, DISPLAY, assets, update_stats, hit.dialogue, hit.icon)
            DISPLAY.blit(groups.bgi, (-(groups.koishi.sprite.delimiter - 200) / 20, 0))
            pygame.display.update()
            hit.kill()
            for bullet in groups.enemyBullets:
                bullet.kill()

    # non-boss enemies that are in contact with koishi do damage then die
    for hit in pygame.sprite.spritecollide(groups.koishi.sprite, groups.onScreenEnemies, False):
        if not (hit in groups.bossSprites) and not groups.koishi.sprite.shielded:
            groups.koishi.sprite.hp -= 1
            hit.kill()
            play_sound(assets.hitSound)

    for hit in pygame.sprite.spritecollide(groups.koishi.sprite, groups.enemyBullets, True):
        if not groups.koishi.sprite.shielded:
            groups.koishi.sprite.hp -= 1
            play_sound(assets.hitSound)

    if groups.koishi.sprite.hp <= 0:
        play_sound(assets.dieSound)
        groups.koishi.sprite.dead = "hit" + str(groups.level)


# initialises all the required objects as defined in a level file
def load_level(level, groups, assets):
    with open(f"media/levels/{level}.txt") as file:
        groups.name = file.readline()[:-1]
        groups.coins = int(file.readline())

        # the default platforms to use for the level
        defaultPlatform = "grass.png"
        defaultFallingPlatform = "fallinggrass.png"

        # the game over screens
        # hit = load_image(f"media/ends/{file.readline()[:-1]}")

        while True:
            try:  # fails iff a line is unusable/reached end of file
                line = file.readline()
                line[1]
            except Exception as e:
                break

            # identifies what the line is defining
            code = line[0]

            # extracts the data, may be a string, a list, etc, to be
            # used in generating the object
            content = eval(line[1:])

            if code == "b":
                if content == "satori":
                    sprites.Satori(groups)
                elif content == "kisume":
                    sprites.Kisume(groups)
                    groups.koishi.sprite.rect.bottom = 540
                    groups.koishi.sprite.delimiter = 800

            # sets image for platforms in this level
            if code == "p":
                defaultPlatform = content

            elif code == "d":
                defaultFallingPlatform = content

            # sets BGM
            elif code == "m":
                play_music(f"media/music/{content}")

            # platform
            elif code == "P":
                sprites.Platform(groups, content[0], content[1],
                                 load_image(f"media/platforms/{defaultPlatform}", width=content[2], height=30))

            elif code == "F":
                for i in range(0, 3600, 900):
                    sprites.Platform(groups, i, 570,
                                     load_image(f"media/platforms/{content}", width=900, height=30))

            elif code == "B":
                groups.bgi = load_image(f"media/bg/{content}", bg=True)

            elif code == "D":
                sprites.DroppingPlatform(groups, content[0], content[1], content[2],
                                         load_image(f"media/platforms/{defaultFallingPlatform}", width=content[3],
                                                    height=30))

            elif code == "G":
                sprites.Gap(groups, content[0], load_image("media/platforms/hole.png", width=content[1], height=30))

            elif code == "l":
                sprites.Gap(groups, content[0], load_image("media/platforms/lava.png", width=content[1], height=30))

            elif code == "e":
                sprites.BaseEnemy(groups, content[0], content[1], content[2],
                                  hp=content[3], func=content[4])

            elif code == "J":
                sprites.JumpBoost(groups, assets, content[0], content[1], content[2])

            elif code == "C":
                sprites.Coin(groups, assets, content[0], content[1])

            elif code == "L":
                sprites.LevelEnd(groups, assets, content[0], content[1])

            elif code == "H":
                sprites.Health(groups, assets, content[0], content[1])

            elif code == "Z":
                g = sprites.Gap(groups, content[0], load_image("media/platforms/hole.png", width=content[1], height=30))
                sprites.Deleter(groups, assets, content[2], content[3], g)

            elif code == "z":
                g = sprites.Gap(groups, content[0], load_image("media/platforms/lava.png", width=content[1], height=30))
                sprites.Deleter(groups, assets, content[2], content[3], g)

            elif code == "O":
                p = sprites.Platform(groups, content[0], content[1],
                                     load_image(f"media/platforms/{defaultPlatform}",
                                                width=content[2], height=30))
                sprites.PatrollingEnemy(groups, 0, 0, content[3], p, content[4], content[5], content[6])

            elif code == "f":
                sprites.Friendly(groups, content[0], content[1], content[2], content[3])

        return 1, 2


def update_sprites(groups, assets, events):
    groups.onScreenPlatforms.empty()
    groups.onScreenEnemies.empty()
    groups.onScreenGaps.empty()
    groups.onScreenItems.empty()
    groups.onScreenAll.empty()

    for plat in groups.platforms:
        if plat.rect.right >= 0 and plat.rect.left <= 900:
            plat.add(groups.onScreenPlatforms, groups.onScreenAll)

    for item in groups.items:
        if item.rect.right >= 0 and item.rect.left <= 900:
            item.add(groups.onScreenItems, groups.onScreenAll)

    for friend in groups.friendlies:
        if friend.rect.right >= 0 and friend.rect.left <= 900:
            friend.add(groups.onScreenAll)

    for gap in groups.gaps:
        if gap.rect.right >= 0 and gap.rect.left <= 900:
            gap.add(groups.onScreenGaps, groups.onScreenAll)

    for bullet in groups.koishiBullets:
        bullet.add(groups.onScreenAll)

    for bullet in groups.enemyBullets:
        bullet.add(groups.onScreenAll)

    for enemy in groups.enemies:
        if enemy.rect.right >= -20 and enemy.rect.left <= 920 or isinstance(enemy, sprites.Boss):
            enemy.add(groups.onScreenAll, groups.onScreenEnemies)

    for shield in groups.shields:
        groups.onScreenAll.add(shield)

    groups.onScreenAll.add(groups.koishi.sprite)

    groups.shields.update()
    groups.koishi.sprite.update(DISPLAY, assets)
    groups.onScreenPlatforms.update()
    groups.koishiBullets.update()
    groups.enemyBullets.update()
    groups.onScreenEnemies.update(assets)
    groups.items.update(assets)

    groups.friendlies.update(events, CLOCK, DISPLAY, assets, update_stats)


def play(level):
    groups = GroupOfGroups()
    assets = Assets()
    groups.level = level
    groups.koishi.add(sprites.Koishi(groups))
    hit, fall = load_level(level, groups, assets)

    DISPLAY.blit(groups.bgi, (-(groups.koishi.sprite.delimiter - 200) / 20, 0))
    update_stats(groups)
    pygame.display.update()
    while not groups.koishi.sprite.dead:

        DISPLAY.blit(groups.bgi, (-(groups.koishi.sprite.delimiter - 200) / 10, 0))

        CLOCK.tick(60)
        events = pygame.event.get()

        update_sprites(groups, assets, events)

        platform_collisions(groups)
        damage_collisions(groups, assets)

        try:
            groups.onScreenAll.draw(DISPLAY)
        except TypeError:
            pass

        groups.onScreenGaps.draw(DISPLAY)
        groups.shields.draw(DISPLAY)

        update_stats(groups)

        pygame.display.update(pygame.Rect(0, 0, 900, 600))

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    groups.koishi.sprite.dead = "escape"

    code = groups.koishi.sprite.dead
    for s in groups.allSprites:
        s.kill()
    return code


def play_game(start):
    level = start
    returning = False  # set true only when player presses escape
    while not returning:
        code = play(level)
        if "escape" in code:
            returning = True
        else:
            if "end" in code:
                if level <= 4:
                    image = "e2.png"
                else:
                    image = "e1.png"
            elif level == 4:
                image = "hits.png"
            else:
                image = "hit.png"
            bg = load_image(f"media/ends/{image}")

            deciding = True
            while deciding and not returning:
                DISPLAY.fill(BG)
                DISPLAY.blit(bg, (172, 100))

                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        pygame.quit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            returning = True
                        elif "end" in code:
                            level += 1
                        deciding = False

                pygame.display.update()


def level_select():
    returning = False
    level = 1
    while not returning:
        DISPLAY.fill(BG)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    level += 1
                elif event.key == pygame.K_LEFT:
                    level -= 1
                elif event.key == pygame.K_UP:
                    level -= 4
                elif event.key == pygame.K_DOWN:
                    level += 4
                elif event.key == pygame.K_RETURN:
                    returning = True
                if level < 1:  # allow wrapping
                    level += 8
                elif level > 8:
                    level -= 8
                if event.key == pygame.K_RETURN:
                    play_game(level)

        for n in range(8):
            x = 180 * (1 + (n % 4))
            y = 200 * (1 + (n // 4))
            draw_text(DISPLAY, f"{n+1}", x, y, size=30, align="center")
            if level == n+1:  # store position of current level while we have it
                cx, cy = x, y

        pygame.draw.circle(DISPLAY, (255, 255, 0), (cx, cy), 50, 5)
        pygame.display.update()


def main_menu():
    bg = load_image("media/bg/menu.png")
    logo = load_image("media/bg/logo.png")
    play_music("media/music/menu.ogg")
    option = 1
    while True:
        DISPLAY.blit(bg, (0, 0))
        DISPLAY.blit(logo, (260, 200))
        pygame.draw.rect(DISPLAY, (0, 0, 0), [0, 0, 250, 600])
        draw_text(DISPLAY, "Start Game", 125, 150, align="center", size=30)
        draw_text(DISPLAY, "Level Select", 125, 300, align="center", size=30)
        draw_text(DISPLAY, "Quit", 125, 450, align="center", size=30)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    option -= 1
                elif event.key == pygame.K_DOWN:
                    option += 1
                if option < 1:
                    option += 3
                elif option > 3:
                    option -= 3
                if event.key == pygame.K_RETURN:
                    if option == 1:
                        play_game(1)
                        play_music("media/music/menu.ogg")
                    elif option == 2:
                        level_select()
                        play_music("media/music/menu.ogg")
                    else:
                        pygame.quit()

        # displays the selected option marker
        pygame.draw.ellipse(DISPLAY, (255, 255, 0), [30, 119 + 150 * (option - 1), 190, 70], width = 5)
        pygame.display.update()


if __name__ == "__main__":
    main_menu()
