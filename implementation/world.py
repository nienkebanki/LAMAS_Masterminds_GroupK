
class World:

    def __init__(self, name, assignment):
        self.name = name
        self.assignment = assignment

    def __eq__(self, other):
        return self.name == other.name and self.assignment == other.assignment

    def __str__(self):
        return "(" + self.name + ',' + str(self.assignment) + ')'


class PublicAnnouncements:
    def __init__(self, actions, equivs):
        self.announcements = actions
        self.equivs = equivs    

class Announcement:
    def __init__(self, name, pub):
        self.name = name
        self.pub = pub
