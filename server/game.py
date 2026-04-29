class Game:
    def __init__(self, game_id):
        self.game_id = game_id
        self.players = []
        self.turn = 0
        self.state = "waiting"  # Possible states: waiting, in_progress, finished
        self.board = [[0 for _ in range(3)] for _ in range(3)]
        self.winner = None

    def add_player(self, player):
        if self.state == "waiting":
            self.players.append(player)
            if len(self.players) == 2:
                self.start_game()
        else:
            raise Exception("Cannot join a game that has already started.")

    def start_game(self):
        self.state = "in_progress"

    def end_game(self):
        self.state = "finished"
        

    def make_move(self, player, position):
        if self.state != "in_progress":
            raise Exception("Game is not in progress.")
        if player != self.players[self.turn % len(self.players)]:
            raise Exception("It's not this player's turn.")
        row, col = position
        if self.board[row][col] != 0:
            raise Exception("Position already taken.")

        self.board[row][col] = 1 if player == self.players[0] else -1
        self.turn += 1

        winner = self.check_win_condition()
        if winner != 0:
            self.winner = self.players[0] if winner == 1 else self.players[1]
            self.end_game()
    
    def check_win_condition(self):
        for i in range(3):
            score = sum(self.board[i])
            if score == 3:
                return 1
            if score == -3:
                return -1
        
        for j in range(3):
            score = sum(self.board[i][j] for i in range(3))
            if score == 3:
                return 1
            if score == -3:
                return -1

        # Check diagonals
        diag1 = sum(self.board[i][i] for i in range(3))
        diag2 = sum(self.board[i][2 - i] for i in range(3))
        if diag1 == 3 or diag2 == 3:
            return 1
        if diag1 == -3 or diag2 == -3:
            return -1

        return 0  # No winner yet
    

g = Game("game1")
