class GameSession:
    def __init__(self, taxa_results, question_num, mode='easy'):
        self.taxa_results = taxa_results
        self.taxon = None
        self.question_num = question_num
        self.mode = mode
        self.type = None
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.message = None
    
    def reset(self):
        self.score = 0
        self.current_index = 0