from enum import Enum

import pygame
import numpy
from simulation import Simulation

from typing import List, Dict


# Genes: (determine behaviour by influencing state transitions) (these have no energy cost)
#   Diet - how much energy an animal gets from eating plants vs other animals
#   Attention - how much an animal pays attention to its surroundings when not hunting or in danger
#   Restlessness - how quickly an animal gets bored
#   Friendliness - how similar another animal must be to be considered a friend
#   Predictability - how often an animal changes heading
#   Sleepiness - how often an animal sleeps
#   Courage - how likely an animal is to attack or run from another animal when under threat

#  Parameters:
#   Energy - how much energy an animal has
#   Health - how much damage an animal can take before dying
#   Hunger - how hungry an animal is
#   Thirst - how thirsty an animal is
#   Temperature - how hot or cold an animal is
#   Comfort - how comfortable an animal is - affected by temperature, hunger, thirst, and injury

# Stats: (similar to genes, but are dependent on genes and features (to prevent animals from just maxing out all stats,
#        so are properties of the animal, not the genome) (these have an energy cost)
#   Injury Threshold - how much damage an animal can take before being injured
#   Speed - how fast an animal can move
#   Defense - damage reduction when being attacked
#   Agility - how quickly an animal can turn
#   Movement Efficiency - how much energy an animal uses per unit of movement
#   Decisiveness - how quickly an animal makes decisions
#   Memory - for how long an animal remembers the location of food/water/predators
#   Perception - the accuracy at which an organism can sense an others stats
#   Cold Resistance - how much damage and energy an animal takes from cold
#   Heat Resistance - how much damage and energy an animal takes from heat
#   Water Resistance - how much damage and energy an animal takes in water
#   Land Speed - how fast an animal can move on land
#   Water Speed - how fast an animal can move in water
#   Air Speed - how fast an animal can move in air


# Features: (determine stats and appearance, each has a strength/prominence gene which influences energy cost)
#  Sensors:
#   Eyes - lens shape: FOV, range
#

#  Stat modifiers: (each value has a weight gene, influencing the distribution of the strength gene, negative values
#                   have discount, which reduces the negative effect the feature has on that particular stat)
#   Brain - +attention, +memory, +decisiveness
#   Legs - +speed, -injury resistance, +movement efficiency
#   Tail - +agility, +defense, -speed
#   Skin - +injury resistance, -speed, +cold resistance, -heat resistance
#   Gills - +water resistance,
#   Fins - +water resistance, +water speed, -land speed
#   Coat - +cold resistance, +heat resistance,
#   Teeth -
#   Wings -
#   Horns -

# all animals have all features, each on a continuum based on the feature's strength gene
# each feature has a cost, which is based on the features strength gene
# the higher the cost, the more energy the animal needs to survive
# there is no upper limit to the strength of a feature - it is only limited by the animal's energy
# each feature has a benefit and drawback, suited to different environments and situations
# some features are discrete, such as eyes, as these are directly simulated

# States:
#   Danger - being attacked
#   Bored - too much time spent hunting/searching without finding anything
#   Hunting - for food/water/predators
#   Sleeping - too tired
#   Searching - for food/water/predators
#   Injured - too much damage
#   Uncomfortable - too hot/cold/wet
#   Hibernate - too cold, too tired, too hungry,
#   Resting - no in any of the above states


class Gene:
    def randomize(self):
        raise NotImplementedError

    def mutate(self, variance):
        raise NotImplementedError

    def set_value(self, value):
        raise NotImplementedError

    def flatten(self):
        raise NotImplementedError


class GeneHider(type):
    """Metaclass that restricts access to genes which are part of a LinkedGene to that LinkedGene's methods"""

    def __new__(cls, name, bases, attrs):
        return super().__new__(cls, name, bases, attrs)


class SingleGene(Gene):
    """All genes are normalized to a range of 0 to 1, and then scaled to the appropriate range for the gene, so that if
    a gene is missed during crossover, the resulting gene will still be valid"""

    class Mode(Enum):
        CLIP = 0
        WRAP = 1
        BOUNCE = 2

    def __init__(self, name, min_value, max_value, dimension=1, mode: Mode = Mode.CLIP):
        self.name = name
        self.dimension = dimension
        self.min_value = min_value
        self.max_value = max_value
        self.mode = mode

        self.value = numpy.zeros(dimension)

    def clamp(self):
        if self.mode == SingleGene.Mode.CLIP:
            self.value = numpy.clip(self.value, 0, 1)
        elif self.mode == SingleGene.Mode.WRAP:
            self.value = numpy.mod(self.value, 1)
        elif self.mode == SingleGene.Mode.BOUNCE:
            self.value = numpy.mod(self.value, 1)
            self.value = numpy.where(self.value > 1 / 2, 1 - self.value, self.value)

    def randomize(self):
        self.value = numpy.random.uniform(0, 1, self.dimension)

    def set_value(self, value):
        assert len(value) == self.dimension, f"Value must have {self.dimension} dimensions for gene {self.name}," \
                                             f" but has {len(value)} dimensions"
        self.value = value
        self.clamp()

    def mutate(self, variance):
        self.value += numpy.random.normal(0, variance, self.dimension)
        self.clamp()

    def __repr__(self):
        return f"{self.name}: {self.value}"


class LinkedGene(Gene):
    """A collection of genes that are inversely proportional to one another"""
    MINIMUM_WEIGHT = 0.001
    MAXIMUM_WEIGHT = 0.999

    def __init__(self, *genes: SingleGene):
        for gene in genes:
            assert gene.mode == SingleGene.Mode.CLIP, "Linked genes must have mode CLIP"

        self.strength = 1  # coefficient for the total strength of the linked genes

        self.genes = genes
        self.weights = numpy.ones(len(genes))
        self.normalize()

    def normalize(self):
        """Normalizes the weights so that they sum to 1 * self.strength"""
        self.weights = numpy.clip(self.weights, LinkedGene.MINIMUM_WEIGHT, LinkedGene.MAXIMUM_WEIGHT)
        self.weights = self.weights / numpy.sum(self.weights)

    def randomize(self):
        self.weights = numpy.random.uniform(0, 1, len(self.genes))
        self.normalize()

    def update_genes(self):
        for i, gene in enumerate(self.genes):
            gene.set_value(self.weights[i] * (gene.max_value - gene.min_value) + gene.min_value)

    def mutate(self, variance):
        for weight in self.weights:
            weight += numpy.random.normal(0, variance)
        self.normalize()
        self.update_genes()


class Feature:
    def __init__(self):
        self.COST_PER_UNIT_PER_SECOND = 1  # the energy cost of each unit of this feature
        self.strength = 1  # the total strength of this feature - can increase or decrease
        self.max_strength = 10  # the maximum number of units this feature can have

        self.genes = list()  # the genes that control this feature


class Sensor(Feature):
    """Discrete feature, """
    pass


class Organism:
    class Stats(Enum):
        SPEED = 0
        STRENGTH = 1
        AGILITY = 2
        INJURY_RESISTANCE = 3
        COLD_RESISTANCE = 4
        HEAT_RESISTANCE = 5
        PREDICTABILITY = 6
        MEMORY = 7

    def __init__(self, sim: "Simulation"):
        self.genes: List[Gene] = []
        self.flat_genes = []
        self.features: Dict[str, Feature] = {}
        self.energy = 0
        self.max_energy = 100
        self.sim = sim

    @classmethod
    def from_parents(cls, parent1: "Organism", parent2: "Organism"):
        """Creates a new animal from two parents"""
        # average genes, mutate genes, create new animal
        pass

    def sense_environment(self, environment):
        """Returns a list of all objects that this animal can sense"""
        pass

    def similarity(self, other: "Organism"):
        """Returns a value between 0 and 1 indicating how similar this animal is to another animal"""
        pass

    def get_genome(self):
        """Returns a numpy array of all genes in this animal"""
        pass


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Genetic Evolution")

    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    gene1 = SingleGene("gene1", 0, 10)
    gene2 = SingleGene("gene2", 0, 10)
    gene1.randomize()
    gene2.randomize()
    print(gene1)
    print(gene2)
    gene1.mutate(0.05)
    gene2.mutate(0.05)
    print(gene1)
    print(gene2)
