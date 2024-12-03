import chess
import chess.engine
import chess.polyglot
import threading
import time
import math
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# Constants for evaluation
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

PIECE_SQUARE_TABLES = {
    chess.PAWN: [
        0, 5, 5, 0, 5, 10, 50, 0,
        0, 10, -5, 0, 5, 10, 50, 0,
        0, 5, 5, 10, 20, 30, 50, 0,
        5, 5, 10, 25, 35, 40, 50, 0,
        5, 5, 10, 25, 35, 40, 50, 0,
        0, 5, 5, 10, 20, 30, 50, 0,
        0, 10, -5, 0, 5, 10, 50, 0,
        0, 5, 5, 0, 5, 10, 50, 0
    ],
    chess.KNIGHT: [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    chess.BISHOP: [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    # Add other piece-square tables for rook, queen, king...
}

class AiymaChessZero:
    def __init__(self, depth=10, threads=4):
        self.depth = depth
        self.threads = threads
        self.transposition_table = {}
        self.lock = threading.Lock()

    def evaluate_board(self, board):
        """Evaluates the board with material and positional heuristics."""
        if board.is_checkmate():
            return -math.inf if board.turn else math.inf
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        eval_score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = PIECE_VALUES[piece.piece_type]
                pst_value = PIECE_SQUARE_TABLES.get(piece.piece_type, [0] * 64)[square]
                eval_score += (value + pst_value) if piece.color == board.turn else -(value + pst_value)
        return eval_score

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning and multi-threading."""
        with self.lock:
            key = (board.fen(), depth)
            if key in self.transposition_table:
                return self.transposition_table[key]

        if depth == 0 or board.is_game_over():
            score = self.evaluate_board(board)
            with self.lock:
                self.transposition_table[key] = score
            return score

        legal_moves = list(board.legal_moves)
        if maximizing_player:
            max_eval = -math.inf
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            with self.lock:
                self.transposition_table[key] = max_eval
            return max_eval
        else:
            min_eval = math.inf
            for move in legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            with self.lock:
                self.transposition_table[key] = min_eval
            return min_eval

    def get_best_move(self, board):
        """Gets the best move by searching the tree with multi-threading."""
        best_move = None
        best_eval = -math.inf
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for move in board.legal_moves:
                board.push(move)
                future = executor.submit(self.minimax, board, self.depth - 1, -math.inf, math.inf, False)
                futures.append((move, future))
                board.pop()
            for move, future in futures:
                eval = future.result()
                if eval > best_eval:
                    best_eval = eval
                    best_move = move
        return best_move

    def play_game(self):
        """Plays a full game as White."""
        board = chess.Board()
        while not board.is_game_over():
            if board.turn:
                best_move = self.get_best_move(board)
                board.push(best_move)
            else:
                # Opponent plays random move; replace with user input for interactive play.
                board.push(next(iter(board.legal_moves)))
            print(board)
            print("\nEvaluation:", self.evaluate_board(board))
            time.sleep(1)
        print("Game Over:", board.result())

# Usage Example
if __name__ == "__main__":
    engine = AiymaChessZero(depth=10, threads=4)
    engine.play_game()
