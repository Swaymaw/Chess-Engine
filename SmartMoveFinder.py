import random
import numpy as np
import time
from math import inf as infinity

# todo need to add a simple sorting algorithm

global start_time, end_time, DEPTH, counter, white_cache, black_cache

# def end_game(gs):
#     pieces = 0
#     for row in range(len(gs.board)):
#         for col in range(len(gs.board[row])):
#             if gs.board[row, col] != "--":
#                 pieces += pieceScores[gs.board[row, col][1]]
#     return pieces <= 20

white_cache = {}
black_cache = {}
pieceScores = {"K": 0, "N": 3, "Q": 9, "B": 3.5, "R": 5, "P": 1}

knightScore_mg = np.array([[-5, -4, -3, -3, -3, -3, -4, -5],
                           [-4, -2, 0, 0, 0, 0, -2, -4],
                           [-3, 0, 1, 1.5, 1.5, 1, 0, -3],
                           [-3, 0.5, 1.5, 2, 2, 1.5, 0.5, -3],
                           [-3, 0, 1.5, 2, 2, 1.5, 0.5, -3],
                           [-3, 0.5, 1, 1.5, 1.5, 1, 0.5, -3],
                           [-4, -2, 0, 0.5, 0.5, 0, -2, -4],
                           [-5, -4, -3, -3, -3, -3, -4, 5]])

rookScore_mg = np.array([[0, 0, 0, 0.5, 0.5, 0, 0, 0],
                         [0.5, 1, 1, 1, 1, 1, 1, 0.5],
                         [-0.5, 0, 0, 0, 0, 0, 0, -0.5],
                         [-0.5, 0, 0, 0, 0, 0, 0, -0.5],
                         [-0.5, 0, 0, 0, 0, 0, 0, -0.5],
                         [-0.5, 0, 0, 0, 0, 0, 0, -0.5],
                         [-0.5, 1, 1, 1, 1, 1, 1, -0.5],
                         [0, 0, 0, 0.5, 0.5, 0, 0, 0]])

bishopScore_mg = np.array([[-2, -1, -1, -1, -1, -1, -1, -2],
                           [-1, 0.5, 0, 0, 0, 0, 0.5, -1],
                           [-1, 1, 1, 1, 1, 1, 1, -1],
                           [-1, 0, 1, 1, 1, 1, 0, -1],
                           [-1, 0, 1, 1, 1, 1, 0, -1],
                           [-1, 1, 1, 1, 1, 1, 1, -1],
                           [-1, 0.5, 0, 0, 0, 0, 0.5, -1],
                           [-2, -1, -1, -1, -1, -1, -1, -2]])

queenScore_mg = np.array([[-2, -1, -1, -0.5, -0.5, -1, -1, -2],
                          [-1, 0, 0, 0, 0, 0, 0, -1],
                          [-1, 0, 0.5, 0, 0, 0.5, 0, -1],
                          [-1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, -1],
                          [0, 0, 0.5, 0.5, 0.5, 0.5, 0, 0],
                          [-0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, -1],
                          [-1, 0, 0.5, 0, 0, 0.5, 0, -1],
                          [-2, -1, -1, -0.5, -0.5, -1, -1, -2]])

kingScore_mg = np.array([[-3, -4, -4, -5, -5, -4, -4, -3],
                         [-3, -4, -4, -5, -5, -4, -4, -3],
                         [-3, -4, -4, -5, -5, -4, -4, -3],
                         [-3, -4, -4, -5, -5, -4, -4, -3],
                         [-3, -4, -4, -5, -5, -4, -4, -3],
                         [-3, -4, -4, -5, -4, -4, -4, -3],
                         [-3, -4, -4, -5, -5, -4, -4, -3],
                         [-3, -4, -4, -5, -5, -4, -4, -3]])

pawnScore_mg = np.array([[90, 90, 90, 90, 90, 90, 90, 90],
                         [1, 1, 1, 1, 1, 1, 1, 1],
                         [1, 2, 2, 3, 3, 2, 2, 1],
                         [0.5, 0.5, 1, 2.5, 2.5, 1, 0.5, 0.5],
                         [0.5, 0.5, 1, 2.5, 2.5, 1, 0.5, 0.5],
                         [1, 2, 2, 3, 3, 2, 2, 1],
                         [1, 1, 1, 1, 1, 1, 1, 1],
                         [90, 90, 90, 90, 90, 90, 90, 90]])

def get_board_position(board):
    string = ""
    for r in range(len(board)):
        for c in range(len(board[r])):
            string += board[r, c]
    return string

piecePositionScores_mg = {"N": knightScore_mg, "B": bishopScore_mg, "K": kingScore_mg, "Q": queenScore_mg, "R": rookScore_mg, "P": pawnScore_mg}
CHECKMATE = infinity
STALEMATE = 0


# black is trying to make a board as negative as possible and white
# is trying to make the board as positive as possible.


'''
Picks and returns a random move.
'''


def findRandomMove(validMoves):
    #random.randint(a, b) #inclusive of both a and b
    return random.choice(validMoves)


'''
Helper method to make the first recursive call
'''


def findBestMove(gs, validMoves):
    global nextMove, start_time, DEPTH
    DEPTH = 3
    start_time = time.time()
    random.shuffle(validMoves)
    # findMinMaxMoveRecursively(gs, validMoves, DEPTH, gs.whiteToMove)
    #findMoveNegaMax(gs, validMoves, DEPTH, 1 if gs.whiteToMove else -1)
    findMoveNegaMaxAlphaBeta(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)
    end_time = time.time()
    return nextMove


'''
Is just a shorter and easier implementation of minmax it does the same thing as minmax.
'''


# makes it a bit faster than before huge difference
def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier): #alpha is the max bound, beta is the lower bound
    global nextMove, counter, start_time, end_time, DEPTH
    sorted_list = []
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)
    # move ordering - checks-> captures->attacks implement later for even more efficiecy and faster
    maxScore = -CHECKMATE
    for move in validMoves:
    #     gs.makeMove(move)
    #     sorted_list.append((move, scoreBoard(gs)))
    #     gs.undoMove()
    # sorted(sorted_list, key=lambda x:x[1], reverse=True)
    # for i in sorted_list:
    #     move = i[0]
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undoMove()
        if maxScore > alpha:  # pruning happens
            alpha = maxScore
        if alpha >= beta:
            break
    return maxScore


'''
A positive score from this is good for white and vice versa. 
'''

def scoreBoard(gs):
    # caches the score evaluated for a position making it a bit faster
    global white_cache, black_cache
    if gs.whiteToMove:
        if get_board_position(gs.board) not in white_cache.keys():
            score = scoring_position(gs)
            white_cache[get_board_position(gs.board)] = score
        else:
            score = white_cache[get_board_position(gs.board)]
    else:
        if get_board_position(gs.board) not in black_cache.keys():
            score = scoring_position(gs)
            black_cache[get_board_position(gs.board)] = score
        else:
            score = black_cache[get_board_position(gs.board)]
    return score


def get_board_coordinates(start_square):
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    board_coordinates = (ranksToRows[start_square[1]], filesToCols[start_square[0]])
    return board_coordinates


def scoring_position(gs):
    global white_space, black_space, piecePositionScore
    focusOnPosition = 0.1

    if gs.checkMate:
        if gs.whiteToMove:
            return -CHECKMATE  # black wins
        else:
            return CHECKMATE  # white wins
    if gs.staleMate:
        return STALEMATE

    score = 0
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row, col]
            if square != "--":
                # score it positionally
                piecePositionScore = piecePositionScores_mg[square[1]][row, col]
                if square[0] == 'w':
                    score += (pieceScores[square[1]] + (piecePositionScore * focusOnPosition))
                elif square[0] == 'b':
                    score -= (pieceScores[square[1]] + (piecePositionScore * focusOnPosition))
    return score


def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScores[square[1]]
            elif square[0] == 'b':
                score -= pieceScores[square[1]]
    return score


def monte_carlo_search(gs, validMoves):
    original_board = gs.board.copy()
    moves = validMoves
    w_l_move = {}
    for move in moves:
        wins = 0
        losses = 0
        draws = 0
        gs.makeMove(move)
        game = True
        for i in range(20):
            counter = 0
            while game:
                if gs.checkMate or gs.staleMate or counter == 100:
                    if gs.checkMate:
                        if gs.whiteToMove:
                            losses += 1
                        else:
                            wins += 1
                    else:
                        draws += 1
                    game = False
                    break
                if not gs.whiteToMove:
                    current_move = findRandomMove(gs.getValidMoves())
                else:
                    current_move = findBestMove(gs, gs.getValidMoves())
                counter += 1
                gs.makeMove(current_move)
            while not (gs.board == original_board).all():
                gs.undoMove()
        w_l_ratio = wins / 20
        w_l_move[w_l_ratio] = move
        print("{:.2f}".format(w_l_ratio))

    best_ratio = -infinity
    best_move = None
    for ratio, move in w_l_move.items():
        if best_move == None or ratio > best_ratio:
            best_ratio = ratio
            best_move = move
    print(best_ratio)
    print(best_move)
    return best_move








