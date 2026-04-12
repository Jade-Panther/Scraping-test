class GameSession:
    def __init__(self, taxa, question_num):
        self.taxa = taxa
        self.question_count = question_num
        self.type = None
        self.questions = []
        self.current_index = 0
        self.score = 0