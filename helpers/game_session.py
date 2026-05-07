class GameSession:
    def __init__(self, session_id, taxa_results, question_num, location=None, diff='easy', multi=True):
        self.id = session_id
        self.host_id = None
        self.taxa_results = taxa_results
        self.taxon = None
        self.question_num = question_num
        self.diff = diff
        self.type = None
        self.questions = []
        self.current_index = 0
        self.scores = {}
        self.message = None
        self.result_embed = None
        self.location = location
        self.multi = multi
        self.players = set()
        self.first_correct_user = None
        self.answered = False
        self.answered_users = set()
        self.first_correct_user = None
        self.question_locked = False

    def reset(self):
        self.score = 0
        self.current_index = 0