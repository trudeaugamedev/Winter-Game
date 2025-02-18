from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scene import Scene

from .sprite import VisibleSprite, Layers
# from .storm import Storm, StormAnim
from .constants import VEC

import pytweening as tween
from random import randint, uniform, choice
from math import cos, sin, pi
from pygame.locals import *
from uuid import uuid4
import pygame
import time

class Swirl(VisibleSprite):
    def __init__(self, scene: Scene, layer: Layers, size: int, density: int = 6, dot_sizes=[1, 2, 2]) -> None:
        super().__init__(scene, layer)
        self.size = size
        self.pos = VEC(0, 0)

        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((255, 255, 255))
        self.dots = []
        for _ in range(density):
            size = self.size / 2
            b = uniform(size / 3, size * 2 / 3)
            rot = uniform(0, 2 * pi)
            self.dots.append([
                # late binding GAHHHHHH
                lambda t, sc, b=b, rot=rot: cos(rot) * ((size - 2) * cos(t)) * sc - sin(rot) * (b * sin(t)) * sc + size,
                lambda t, sc, b=b, rot=rot: sin(rot) * ((size - 2) * cos(t)) * sc + cos(rot) * (b * sin(t)) * sc + size,
                (randint(90, 160),) * 3, # color
                uniform(0, 2 * pi), # phase
                uniform(7, 12), # speed
                choice(dot_sizes), # radius
                0, # scale
                uniform(0.3, 0.7) # scale speed
            ])
        self.visible = True
        self.alpha = 255

    def update(self) -> None:
        for dot in self.dots:
            real_scale = tween.easeOutExpo(dot[6])
            pos = VEC(dot[0](time.time() * dot[4] + dot[3], real_scale), dot[1](time.time() * dot[4] + dot[3], real_scale))
            pygame.draw.aacircle(self.image, (140, 140, 140), pos, dot[5])
            dot[6] += dot[7] * self.manager.dt
            if dot[6] > 1:
                dot[6] = 1

    def draw(self) -> None:
        if not self.visible: return
        self.image.fill((2, 2, 2), special_flags=BLEND_ADD)
        self.scene.manager.screen.blit(self.image, self.pos - self.scene.player.camera.offset, special_flags=BLEND_MULT)

class VortexSwirl(Swirl):
    instances = {}

    def __init__(self, scene: Scene, layer: Layers, pos: VEC, size: int, density: int = 6, suck: bool = False) -> None:
        super().__init__(scene, layer, size, density, range(2, 4))
        # self.storm = storm
        self.pos = pos
        self.timer = time.time()
        self.startTime = time.time()
        self.maxTime = 12
        self.orig_img = self.image.copy()
        self.suck = suck

        self.id = uuid4().hex
        __class__.instances[self.id] = self

    def update(self) -> None:
        # if getattr(self, "storm", None) is None: return
        super().update()

        # sucking is on the thrower's side?????
        if self.suck and not self.scene.eliminated:
            if (dist := self.scene.player.pos.distance_to(self.pos + (self.size / 2,) * 2)) < 250:
                vel = (1 - dist / 250) * (self.pos + (self.size / 2,) * 2 - self.scene.player.pos).normalize() * 20
                vel.y *= 0.5
                self.scene.player.vel += vel
        for snowball in self.scene.player.snowballs.values():
            if (dist := snowball.pos.distance_to(self.pos + (self.size / 2,) * 2)) < 250 and dist > 0:
                snowball.vel *= ((dist + 10) / 260) ** self.manager.dt # more friction the closer to center the snowball gets
                snowball.vel += (1 - dist / 250) * (self.pos + (self.size / 2, self.size / 2) - snowball.pos).normalize() * 150 # normal accel (toward center)
                snowball.vel += (1.1 - dist / 250) * (self.pos + (self.size / 2, self.size / 2) - snowball.pos).normalize().rotate(-90) * 10 # tangent accel (perp. to normal)
                snowball.follow = False # don't mess with people's camera if snowball gets stuck

        self.image.fill((0, 0, 0), special_flags=BLEND_ADD)

        if time.time() - self.startTime > self.maxTime:
            self.kill()
        if time.time() - self.startTime > self.maxTime - 1:
            for dot in self.dots:
                dot[6] -= 4.5 * dot[7] * self.manager.dt
                if dot[6] < 0:
                    dot[6] = 0

    def draw(self) -> None:
        super().draw()

    def kill(self) -> None:
        try:
            __class__.instances.pop(self.id)
        except KeyError:
            pass
        super().kill()
