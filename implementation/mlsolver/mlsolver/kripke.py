"""Kripke module

Provides a tool to model Kripke structures and solve them in addition to a
modal logic formula.
"""

import copy

from itertools import chain, combinations


class KripkeStructure:
    """
    This class describes a Kripke Frame with it's possible worlds and their
    transition relation.
    """

    def __init__(self, worlds, relations):
        if isinstance(worlds, list) or isinstance(worlds, dict):
            # MODIFIED: self.worlds is now a dictionary nstead of a list
            self.worlds = {w.name: w for w in worlds}
            self.relations = relations
        else:
            raise TypeError

    def solve(self, formula):
        """Returns a Kripke structure with minimum sub set of nodes, that each
        of it's nodes forces a given formula.
        """
        # MODIFIED to use dictionary of worlds
        for i, subset in enumerate(self.get_power_set_of_worlds()):
            ks = KripkeStructure(list(self.worlds.values()), copy.deepcopy(self.relations))
            print(subset)
            for element in subset:
                ks.remove_node_by_name(element)
            if ks.nodes_not_follow_formula(formula) == []:
                return ks

    def remove_node_by_name(self, node_name):
        """Removes ONE node of Kripke frame, therefore we can make knowledge
        base consistent with announcement.
        """
        self.worlds.pop(node_name)

        if isinstance(self.relations, set):
            for (start_node, end_node) in self.relations.copy():
                if start_node == node_name or end_node == node_name:
                    self.relations.remove((start_node, end_node))

        if isinstance(self.relations, dict):
            for key, value in self.relations.items():
                for (start_node, end_node) in value.copy():
                    if start_node == node_name or end_node == node_name:
                        value.remove((start_node, end_node))

    def get_power_set_of_worlds(self):
        """Returns a list with all possible sub sets of world names, sorted
        by ascending number of their elements.
        """
        # MODIFIED to use dictionary of worlds
        sub_set = [{}]
        worlds_by_name = []
        for w in self.worlds.values():
            worlds_by_name.append(w.name)
        for z in chain.from_iterable(
                combinations(worlds_by_name, r + 1)
                for r in range(len(worlds_by_name) + 1)):
            sub_set.append(set(z))
        return sub_set

    def nodes_not_follow_formula(self, formula):
        """Returns a list with all worlds of Kripke structure, where formula
         is not satisfiable
        """
        # MODIFIED to use dictionary of worlds
        nodes_not_follow_formula = []
        for nodes in self.worlds.values():
            if not formula.semantic(self, nodes.name):
                nodes_not_follow_formula.append(nodes.name)
        return nodes_not_follow_formula

    def __eq__(self, other):
        """Returns true iff two Kripke structures are equivalent
        """
        # MODIFIED to use dictionary of worlds
        if (self.worlds == {} and not other.worlds == {}) \
                or (not self.worlds == {} and other.worlds == {}):
            return False
        for (i, j) in zip(self.worlds.values(), other.worlds.values()):
            if not i.__eq__(j):
                return False

        if isinstance(self.relations, set):
            for (i, j) in zip(self.relations, other.relations):
                if not i == j:
                    return False

        if isinstance(self.relations, dict):
            for key, value in self.relations.items():
                try:
                    if not value == other.relations[key]:
                        return False
                except KeyError:
                    if not value == set():
                        return False
        return True

    def __str__(self):
        # MODIFIED to use dictionary of worlds
        worlds_str = "(W = {"
        for world in self.worlds.values():
            worlds_str += str(world)
        return worlds_str + '}, R = ' + str(self.relations) + ')'


class World:
    """
    Represents the nodes of Kripke and it extends the graph to Kripke
    Structure by assigning a subset of propositional variables to each world.
    """

    def __init__(self, name, assignment):
        self.name = name
        self.assignment = assignment

    def __eq__(self, other):
        return self.name == other.name and self.assignment == other.assignment

    def __str__(self):
        return "(" + self.name + ',' + str(self.assignment) + ')'