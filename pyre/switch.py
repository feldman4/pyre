class Switch(object):
    def __init__(self, engine, world):
        self.engine = engine
        self.world = world
        self.world.switches.append(self)
        self.initialized = False
        self.initialize_on_activation = False

    def initialize(self):
        pass

    def evaluate(self):
        if not self.initialized:
            self.initialized = True
            self.initialize()

    def do(self):
        pass

    def remove(self):
        self.world.switches.remove(self)
        # individual scripts can use this to delete listeners, etc





class Counter(object):
    def __init__(self, value=0):
        self.value = value

    def __set__(self, instance, value):
        self.value = value

    def __get__(self, instance, owner):
        return self.value

    def __add__(self, other):
        return self.value + other

    def __repr__(self):
        return str(self.value)

    def increment(self):
        self.value += 1
        return self.value