class GameSession:
    def __init__(self, config):
        self.taxa = config['taxa']
        self.type = config['type']
        self.questions = config['questions']
        self.score = 0
        self.current = 0
        self.expire = 0 # TODO: Time based expire