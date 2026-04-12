class GameSession:
    def __init__(self, config):
        self.taxa = config['taxa']
        self.type = config['type']
        self.question_num = config['questions']
        self.questions = []
        self.score = 0
        self.current = 0
        self.expire = 0 # TODO: Time based expire