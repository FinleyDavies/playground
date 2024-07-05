import pygame
import math
import random
from shapely.geometry import Polygon, Point


def get_tangents(x1, y1, r1, x2, y2, r2):
    # translated to python with chatgpt from:
    # https://en.wikibooks.org/wiki/Algorithm_Implementation/Geometry/Tangents_between_two_circles
    d_sq = (x1 - x2) ** 2 + (y1 - y2) ** 2
    if d_sq <= (r1 - r2) ** 2:
        return []

    d = math.sqrt(d_sq)
    vx = (x2 - x1) / d
    vy = (y2 - y1) / d

    res = []
    for sign1 in [1, -1]:
        c = (r1 - sign1 * r2) / d

        if c * c > 1.0:
            continue
        h = math.sqrt(max(0.0, 1.0 - c * c))

        for sign2 in [1, -1]:
            nx = vx * c - sign2 * h * vy
            ny = vy * c + sign2 * h * vx

            res.append([x1 + r1 * nx, y1 + r1 * ny, x2 + sign1 * r2 * nx, y2 + sign1 * r2 * ny])

    return res


def circle_line_intersection(cx, cy, cr, x1, y1, x2, y2, lb=True, ub=True):
    dx, dy = x2 - x1, y2 - y1
    A = dx ** 2 + dy ** 2
    B = 2 * (dx * (x1 - cx) + dy * (y1 - cy))
    C = (x1 - cx) ** 2 + (y1 - cy) ** 2 - cr ** 2
    det = B ** 2 - 4 * A * C

    if det < 0:
        # No real intersection
        return []
    elif det == 0:
        # One intersection
        t = -B / (2 * A)
        if (not lb or t >= 0) and (not ub or t <= 1):
            x = x1 + t * dx
            y = y1 + t * dy
            return [[x, y]]
        else:
            return []
    else:
        # Two intersections
        intersections = []
        for sign in [-1, 1]:
            t = (-B + sign * math.sqrt(det)) / (2 * A)
            if (not lb or t >= 0) and (not ub or t <= 1):
                x = x1 + t * dx
                y = y1 + t * dy
                intersections.append([x, y])
        return intersections


def get_first_intersection(circles, ray):
    # get the first circle to be intersected by the ray
    first_intersection = None
    for c in circles:
        intersections = circle_line_intersection(c[0], c[1], c[2], ray[0], ray[1], ray[2], ray[3], ub=False)
        if intersections:
            for i in intersections:
                if not first_intersection:
                    first_intersection = (i, c)
                else:
                    if abs(i[0] - ray[0]) < abs(first_intersection[0][0] - ray[0]):
                        first_intersection = (i, c)
    return first_intersection

def is_visible(target, source, obstacles):
    # calculate all tangents from source to target:
    tangents = get_tangents(source[0], source[1], 0, target[0], target[1], 0)
    # check if the target is visible
    for t in tangents:
        hit = get_first_intersection(obstacles, t)
        if hit:
            return False
    return True

def main():
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    running = True
    radius = 100
    position = (200, 200)
    # create list of 10 random circles:
    circles = []
    for i in range(10):
        x = random.randint(0, 800)
        y = random.randint(0, 600)
        r = random.randint(10, 100)
        circles.append((x, y, r))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4 and radius < 200:
                    radius += 10
                if event.button == 5 and radius > 10:
                    radius -= 10

        screen.fill((30, 30, 30))
        position = pygame.mouse.get_pos()

        # draw circles
        pygame.draw.circle(screen, (255, 0, 0), (200, 200), 100, 2)
        pygame.draw.circle(screen, (0, 255, 0), position, radius, 2)

        # get tangents
        tangents = get_tangents(position[0], position[1], radius, 200, 200, 100)
        poly = Polygon(((tangents[0][0], tangents[0][1]), (tangents[1][0], tangents[1][1]),
                        (tangents[1][2], tangents[1][3]), (tangents[0][2], tangents[0][3])))
        pygame.draw.polygon(screen, (255, 255, 255), poly.exterior.coords, 2)
        for c in circles:

            circle = Point(c[0], c[1]).buffer(c[2])
            if poly.intersects(circle):
                pygame.draw.circle(screen, (255, 0, 255), (c[0], c[1]), c[2], 2)
            else:
                pygame.draw.circle(screen, (0, 255, 255), (c[0], c[1]), c[2], 2)

        for t in tangents:
            pygame.draw.line(screen, (255, 255, 255), (t[0], t[1]), (t[2], t[3]), 2)
            hit = get_first_intersection(circles, t)
            if hit:
                pygame.draw.circle(screen, (255, 255, 0), (hit[0][0], hit[0][1]), 5)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()