class GameSession:
    def __init__(self, taxa_results, question_num, diff='easy'):
        self.taxa_results = taxa_results
        self.taxon = None
        self.question_num = question_num
        self.diff = diff
        self.type = None
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.message = None
        self.result_embed = None
    
    def reset(self):
        self.score = 0
        self.current_index = 0