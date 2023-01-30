import pygame


# module adding required, often used functions

# draws text on the given surface. Align controls where the supplied coordinates
# are relative to the text box (the coordinates define the top left of the box
# if no argument is supplied)
def draw_text(surface, text, x, y,
              colour=(255, 255, 255),
              size=20, align="topleft"):
    font = pygame.font.Font("media/cooprblk.ttf", size)
    text_surface = font.render(text, False, colour)
    text_rect = text_surface.get_rect()

    if align == "topleft":
        text_rect.topleft = (x, y)
    elif align == "topright":
        text_rect.topright = (x, y)
    elif align == "center":
        text_rect.center = (x, y)

    surface.blit(text_surface, text_rect)


# loads an image with options to resize (scale or give dimensions), rotate, and
# convert if the image will contain no alpha (eg background) for efficiency.
def load_image(filepath, width=None, height=None,
               rotate=0, bg=False, scale=None):
    image = pygame.transform.rotate(pygame.image.load(filepath), rotate)

    if (not width or not height) and not scale:
        if not bg:
            return image.convert_alpha()
        else:
            return image.convert()
    elif scale:
        return pygame.transform.rotozoom(image, 0, scale).convert_alpha()
    else:
        return pygame.transform.scale(image, (width, height)).convert_alpha()


def play_sound(sound, volume=1):
    sound.set_volume(volume)
    sound.play()


# splits a string into lines that are no longer than
# length, without splitting words (delimited by spaces)
# eg split("tests a test tests", 6) -> ["tests", "a test", "tests"]
def split(text, length):

    new = text.split(" ")
    new.reverse()
    result = []
    while len(new) > 0:
        current = ""
        try:
            while len(current + " " + new[-1]) <= length:
                current = current + new.pop() + " "
        except IndexError:
            pass

        result.append(current[:-1])

    return result
