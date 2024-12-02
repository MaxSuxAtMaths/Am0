import math
import sys
import copy

# Piece values and basic positional bonuses
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
    'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000
}

class ChessEngine:
    def __init__(self):
        self.board = [
            ["r", "n", "b", "q", "k", "b", "n", "r"],
            ["p", "p", "p", "p", "p", "p", "p", "p"],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            ["P", "P", "P", "P", "P", "P", "P", "P"],
            ["R", "N", "B", "Q", "K", "B", "N", "R"]
        ]
        self.white_to_move = True

    def evaluate(self):
        """Evaluate the board position."""
        score = 0
        for row in self.board:
            for piece in row:
                score += PIECE_VALUES.get(piece, 0)
        return score

    def generate_legal_moves(self):
        """Generate all legal moves (simplified for now)."""
        moves = []
        for r, row in enumerate(self.board):
            for c, piece in enumerate(row):
                if piece.isupper() == self.white_to_move and piece != '.':
                    moves.extend(self.generate_piece_moves((r, c), piece))
        return moves

    def generate_piece_moves(self, pos, piece):
        """Generate moves for a single piece."""
        directions = []
        r, c = pos
        moves = []

        if piece.upper() == 'P':  # Pawn moves
            step = -1 if piece.isupper() else 1
            start_row = 6 if piece.isupper() else 1
            if self.board[r + step][c] == ".":
                moves.append(((r, c), (r + step, c)))
                if r == start_row and self.board[r + 2 * step][c] == ".":
                    moves.append(((r, c), (r + 2 * step, c)))
        # Add other piece moves (Rook, Knight, Bishop, Queen, King)...

        return moves

    def make_move(self, move):
        """Execute a move on the board."""
        from_pos, to_pos = move
        self.board[to_pos[0]][to_pos[1]] = self.board[from_pos[0]][from_pos[1]]
        self.board[from_pos[0]][from_pos[1]] = "."
        self.white_to_move = not self.white_to_move

    def undo_move(self, move, captured_piece):
        """Undo a move on the board."""
        from_pos, to_pos = move
        self.board[from_pos[0]][from_pos[1]] = self.board[to_pos[0]][to_pos[1]]
        self.board[to_pos[0]][to_pos[1]] = captured_piece
        self.white_to_move = not self.white_to_move

    def alpha_beta(self, depth, alpha, beta, maximizing_player):
        """Alpha-Beta pruning with depth control."""
        if depth == 0:
            return self.evaluate(), None

        legal_moves = self.generate_legal_moves()
        if not legal_moves:
            return -math.inf if maximizing_player else math.inf, None

        best_move = None

        if maximizing_player:
            max_eval = -math.inf
            for move in legal_moves:
                captured_piece = self.board[move[1][0]][move[1][1]]
                self.make_move(move)
                eval, _ = self.alpha_beta(depth - 1, alpha, beta, False)
                self.undo_move(move, captured_piece)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = math.inf
            for move in legal_moves:
                captured_piece = self.board[move[1][0]][move[1][1]]
                self.make_move(move)
                eval, _ = self.alpha_beta(depth - 1, alpha, beta, True)
                self.undo_move(move, captured_piece)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def get_best_move(self, depth):
        """Get the best move for the current position."""
        _, best_move = self.alpha_beta(depth, -math.inf, math.inf, True)
        return best_move


class UCIEngine:
    def __init__(self):
        self.engine = ChessEngine()
        self.running = True

    def send(self, message):
        """Send a message to the GUI."""
        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    def process_command(self, command):
        """Process a UCI command."""
        if command == "uci":
            self.send("id name AdvancedEngine")
            self.send("id author YourName")
            self.send("uciok")
        elif command.startswith("position"):
            self.handle_position(command)
        elif command.startswith("go"):
            self.handle_go(command)
        elif command == "quit":
            self.running = False
        elif command == "isready":
            self.send("readyok")
        elif command == "ucinewgame":
            pass  # Initialize for a new game if needed

    def handle_position(self, command):
        """Handle the position command."""
        parts = command.split(" ")
        if "startpos" in parts:
            self.engine = ChessEngine()  # Reset to start position
            moves_index = parts.index("moves") + 1 if "moves" in parts else len(parts)
            moves = parts[moves_index:]
            for move in moves:
                self.engine.make_move(self.uci_to_move(move))

    def handle_go(self, command):
        """Handle the go command."""
        best_move = self.engine.get_best_move(depth=8)  # Use desired depth
        move_str = self.move_to_uci(best_move)
        self.send(f"bestmove {move_str}")

    def uci_to_move(self, move_str):
        """Convert UCI move string to internal move format."""
        return ((8 - int(move_str[1]), ord(move_str[0]) - ord('a')),
                (8 - int(move_str[3]), ord(move_str[2]) - ord('a')))

    def move_to_uci(self, move):
        """Convert internal move format to UCI move string."""
        from_pos, to_pos = move
        return f"{chr(from_pos[1] + ord('a'))}{8 - from_pos[0]}{chr(to_pos[1] + ord('a'))}{8 - to_pos[0]}"

    def run(self):
        """Main loop for the UCI protocol."""
        while self.running:
            command = input().strip()
            self.process_command(command)


if __name__ == "__main__":
    UCIEngine().run()
