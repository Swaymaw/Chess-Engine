"""
This class is responsible for storing all the information about the current state of the chess game.
It will also be responsible for determining the valid moves at the current state. It will also keep
a move log.
"""
import copy
import numpy as np


class GameState():

    checkMate = False
    staleMate = False

    def __init__(self):
        self.board = np.array([
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ])
        self.moveFunctions = {'P':self.getPawnMoves, 'R':self.getRookMoves, 'N':self.getKnightMoves, 'B':self.getBishopMoves,
                              'Q':self.getQueenMoves, 'K':self.getKingMoves
                              }
        self.whiteToMove = True
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.moveLog = []
        self.inCheck = False
        self.pins = []
        self.checks = []
        self.enpassantPossible = () #coordinates of the square where an enpassant capture is available
        self.enpassantPossibleLog = [self.enpassantPossible]
        #castling rights
        self.currentCastlingRights = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                             self.currentCastlingRights.wqs, self.currentCastlingRights.bqs)]

        '''
        Takes a move as a parameter and executes it (it will not work for castling, pawn promotion, and en-passant)
        '''

    def makeMove(self, move, board=np.zeros((8, 8))):

        if board[1][1] == 0:
            board = self.board

        board[move.endRow, move.endCol] = move.pieceMoved
        board[move.startRow, move.startCol] = "--"
        self.moveLog.append(move) #log the move so that we can review it later
        self.whiteToMove = not self.whiteToMove #swap players
        #update the kings location
        if move.pieceMoved == "wK":
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == "bK":
            self.blackKingLocation = (move.endRow, move.endCol)
        #if pawn moves twice, next move can capture enpassant
        if move.pieceMoved[1] == 'P' and abs(move.startRow-move.endRow) == 2:
            self.enpassantPossible = ((move.endRow+move.startRow)//2, move.endCol)
        else:
            self.enpassantPossible = ()

        #update board to capture the pawn
        if move.enPassant:
            board[move.startRow, move.endCol] = '--'  # capturing the pawn

        #pawn promotion with change piece
        if move.pawnPromotion:
            promotedPiece = "Q"   # we can ask for what to promote to and also make this part of the ui later
            board[move.endRow, move.endCol] = move.pieceMoved[0] + promotedPiece

        #castle move
        if move.castle:
            if move.endCol - move.startCol == 2: #kingside castle
                board[move.endRow, move.endCol - 1] = board[move.endRow, move.endCol + 1]
                board[move.endRow, move.endCol + 1] = "--"
            else:
                board[move.endRow, move.endCol + 1] = board[move.endRow, move.endCol - 2]
                board[move.endRow, move.endCol - 2] = "--"
        self.enpassantPossibleLog.append(self.enpassantPossible)
        # update castling rights
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                                 self.currentCastlingRights.wqs, self.currentCastlingRights.bqs))
    '''
    Undo the last move made
    '''

    def undoMove(self, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            board[move.startRow, move.startCol] = move.pieceMoved
            board[move.endRow, move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove #switch turns back
            #update kings location for undo also
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == "bK":
                self.blackKingLocation = (move.startRow, move.startCol)

            #undo the enpassant move
            if move.enPassant:
                board[move.endRow, move.endCol] = '--' #leave landing square blank
                board[move.startRow, move.endCol] = move.pieceCaptured
            self.enpassantPossibleLog.pop()
            self.enpassantPossible = copy.deepcopy(self.enpassantPossibleLog[-1])

            #give back castling rights if move took them away
            self.castleRightsLog.pop() # remove last moves updates
            castleRights = copy.deepcopy(self.castleRightsLog[-1])
            self.currentCastlingRights = castleRights
            #undo castle moves
            if move.castle:
                if move.endCol - move.startCol == 2:
                    board[move.endRow, move.endCol + 1] = board[move.endRow, move.endCol-1]
                    board[move.endRow, move.endCol - 1] = "--"
                else:
                    board[move.endRow, move.endCol - 2] = board[move.endRow, move.endCol + 1]
                    board[move.endRow, move.endCol + 1] = "--"
            GameState.checkMate = False
            GameState.staleMate = False
    '''
    All moves considering checks
    '''
    def getValidMoves(self, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        #advanced algorithm method:
        moves = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whiteToMove:
            self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
        if self.inCheck:
            if len(self.checks) == 1: #only 1 check block check or capture checking piece or move king
                moves = self.getAllPossibleMoves(self.board)
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = board[checkRow, checkCol]
                validSquares = []
                if pieceChecking[1] == 'N':
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i)
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:
                            break
                #get rid of any moves that dont block the check move the king out of check or kill the attacking piece
                for i in range(len(moves)-1, -1, -1):
                    if moves[i].pieceMoved[1] != 'K':
                        if not(moves[i].endRow, moves[i].endCol) in validSquares:
                            moves.remove(moves[i])
            else:
                self.getKingMoves(kingRow, kingCol, moves)
        else:
            moves = self.getAllPossibleMoves(self.board)

        if len(moves) == 0:
            if self.inCheck:
                GameState.checkMate = True
            else:
                GameState.staleMate = True
        else:
            GameState.checkMate = False
            GameState.staleMate = False
        if self.whiteToMove:
            self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
        else:
            self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)
        return moves

    '''
    All moves without considering checks
    '''
    def getAllPossibleMoves(self, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        moves = []
        for r in range(len(board)): #no. of rows
            for c in range(len(board[r])): # no. of cols
                turn = board[r, c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = board[r, c][1]
                    self.moveFunctions[piece](r, c, moves) #calls the appropriate function based on the piece type
        return moves
    '''
    Get all the pawn moves for the pawn located at row, col and add these moves to the list
    '''
    def getPawnMoves(self,r,c,moves,board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        piecePinned = False
        pinDirection=()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        if self.whiteToMove:
            moveAmount = -1
            startRow = 6
            backRow = 0
            enemyColor = 'b'
            kingRow, kingCol = self.whiteKingLocation
        else:
            moveAmount = 1
            startRow = 1
            backRow = 7
            enemyColor = 'w'
            kingRow, kingCol = self.blackKingLocation
        pawnPromotion = False

        if board[r+moveAmount, c] == "--": #1 square move
            if not piecePinned or pinDirection == (moveAmount,0):
                if r+moveAmount == backRow:
                    pawnPromotion = True
                moves.append(Move((r, c), (r+moveAmount, c), board, pawnPromotion=pawnPromotion))
                if r == startRow and board[r+2*moveAmount, c] == "--":#2 square moves
                    moves.append(Move((r, c), (r+2*moveAmount, c), board))
        if c-1 >= 0: #capture to the left
            if not piecePinned or pinDirection == (moveAmount, -1):
                if board[r + moveAmount, c - 1][0] == enemyColor:
                    if r + moveAmount == backRow:
                        pawnPromotion = True
                    moves.append(Move((r, c), (r+moveAmount, c-1), board, pawnPromotion=pawnPromotion))
                if (r+moveAmount, c-1) == self.enpassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c: #king column is less than the columns of the pawn
                            #between the king and the pawn; outside range will be between the king and the border
                            insideRange = range(kingCol+1, c-1)
                            outsideRange = range(c + 1, 8)
                        else:
                            insideRange = range(kingCol-1, c, -1)
                            outsideRange = range(c-2, -1, -1)
                        for i in insideRange:
                            if board[r, i]!="--": #some other piece than enpassant piece blocks
                                blockingPiece = True
                        for i in outsideRange:
                            square = board[r, i]
                            if (square[0] == enemyColor and (square[1] == 'R' or square[1] == 'Q')): #attacking piece
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r+moveAmount, c-1), board, enPassant=True))
        if c+1 <= 7: #capture to the right
            if not piecePinned or pinDirection == (moveAmount, 1):
                if board[r+moveAmount, c + 1][0] == enemyColor:
                    if r + moveAmount == backRow:
                        pawnPromotion = True
                    moves.append(Move((r, c), (r + moveAmount, c + 1), board, pawnPromotion=pawnPromotion))
                if (r+moveAmount, c+1) == self.enpassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:  # king column is less than the columns of the pawn
                            # between the king and the pawn; outside range will be between the king and the border
                            insideRange = range(kingCol + 1, c)
                            outsideRange = range(c + 2, 8)
                        else:
                            insideRange = range(kingCol - 1, c+1, -1)
                            outsideRange = range(c - 1, -1, -1)
                        for i in insideRange:
                            if board[r, i] != "--":  # some other piece than enpassant piece blocks
                                blockingPiece = True
                        for i in outsideRange:
                            square = board[r, i]
                            if (square[0] == enemyColor and (square[1] == 'R' or square[1] == 'Q')):  # attacking piece
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r + moveAmount, c + 1), board, enPassant=True))

    '''
    Get all the rook moves for the rook located at the row, col and add these moves to the list
    '''
    def getRookMoves(self,r,c,moves, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if board[r, c][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1)) #up, #left, #down, #right
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0],-d[1]):
                        endPiece = board[endRow, endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), board))
                            break
                        else:
                            break
                else:  # off-board square
                    break


    '''
        Get all the knight moves for the pawn located at row, col and add these moves to the list
       '''

    def getKnightMoves(self, r, c, moves, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = "w" if self.whiteToMove else "b"
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                if not piecePinned:
                    endPiece = board[endRow,endCol]
                    if endPiece[0] != allyColor:
                        moves.append(Move((r, c), (endRow, endCol), board))


    '''
       Get all the bishop moves for the pawn located at row, col and add these moves to the list
       '''

    def getBishopMoves(self, r, c, moves, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if (0 <= endRow <= 7) and (0 <= endCol <= 7):
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = board[endRow,endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), board))
                            break
                        else:  # friendly piece capture invalid
                            break
                else:  # off-board scenario
                    break
    '''
    Get all the queen moves for the pawn located at row, col and add these moves to the list
    '''
    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    '''
    Get all the king moves for the pawn located at row, col and add these moves to the list
    '''

    def getKingMoves(self, r, c, moves, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                endPiece = board[endRow,endCol]
                if endPiece[0] != allyColor:
                    if allyColor == "w":
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), board))
                    if allyColor == 'w':
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c)

    def getCastleMoves(self, r, c, moves):
        if self.squareUnderAttack(r, c):
            return  # cant castle when in check
        if (self.whiteToMove and self.currentCastlingRights.wks) or (
                not self.whiteToMove and self.currentCastlingRights.bks):
            self.getKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRights.wqs) or (
                not self.whiteToMove and self.currentCastlingRights.bqs):
            self.getQueensideCastleMoves(r, c, moves)

    def getKingsideCastleMoves(self, r, c, moves, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        if board[r,c + 1] == "--" and board[r,c + 2] == "--":
            if not self.squareUnderAttack(r, c + 1) and not self.squareUnderAttack(r, c + 2):
                moves.append(Move((r, c), (r, c + 2), board, castle=True))

    def getQueensideCastleMoves(self, r, c, moves, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        if board[r,c - 1] == "--" and board[r,c - 2] == "--" and board[r,c - 3] == "--":
            if not self.squareUnderAttack(r, c - 1) and not self.squareUnderAttack(r, c - 2):
                moves.append(Move((r, c), (r, c - 2), board, castle=True))
    '''
    Returns if square is under attack
    '''
    def squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:
                return True
        return False
    '''
    Returns if the player is in check, a list of pins and a list of checks.
    '''
    def checkForPinsAndChecks(self, board=np.zeros((8, 8))):
        if board[1][1] == 0:
            board = self.board
        pins = []  # squares where the allied pinned piece is and direction it is pinned from
        checks = []  # squares where enemy is applying a check
        inCheck = False
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]
        # check outwards from king all the checks and pins and keep a track of the pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = ()  # reset possible pins
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                    endPiece = board[endRow,endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:  # 2nd allied piece so no pin or check possible on this one
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]

                        if (0 <= j <= 3 and type == 'R') or \
                                (4 <= j <= 7 and type == 'B') or \
                                (i == 1 and type == 'P' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                                (type == 'Q') or (i == 1 and type == 'K'):
                            if possiblePin == ():
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:  # piece blocking so no check but a pin
                                pins.append(possiblePin)
                                break
                        else:  # enemy piece not applying any check
                            break
                else:
                    break  # off-board condition
        # checks for knight checks
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                endPiece = board[endRow,endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N':
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks

    '''
    Update the castle rights
    '''
    def updateCastleRights(self, move):
        if move.pieceMoved == "wK":
            self.currentCastlingRights.wks = False
            self.currentCastlingRights.wqs = False
        elif move.pieceMoved == "bK":
            self.currentCastlingRights.bks = False
            self.currentCastlingRights.bqs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 7:
                if move.startCol == 0:
                    self.currentCastlingRights.wqs = False
                elif move.startCol == 7:
                    self.currentCastlingRights.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0:
                    self.currentCastlingRights.bqs = False
                elif move.startCol == 7:
                    self.currentCastlingRights.bks = False
        # if a rook is captured
        if move.pieceCaptured == "wR":
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRights.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRights.wks = False
        elif move.pieceCaptured == "bR":
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRights.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRights.bks = False


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs

class Move():
    #map keys to values
    #key : value
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()} # a method to quickly reverse a dictionary
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6,"h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, enPassant = False, pawnPromotion = False, castle=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow, self.startCol]
        self.pieceCaptured = board[self.endRow, self.endCol]
        #pawn promotion
        self.pawnPromotion = pawnPromotion
        #en passant
        self.enPassant = enPassant
        if enPassant:
            self.pieceCaptured = 'bP' if self.pieceMoved == "wP" else "wP"
        #castle move
        self.castle = castle

        self.moveID = self.startRow*1000 + self.startCol*100 + self.endRow*10 + self.endCol #impressive idea
    '''
    Overriding the equals method
    '''
    def __eq__(self, other): # so that python can compare properly and make a move if it is available in the .getValidMoves() list.
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def isCapture(self):
        return self.pieceCaptured != "--"

    def getChessNotation(self):
        #you can make it more like real chess notation if necessary
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    #overriding the str() function
    def __str__(self):
        #castle move
        if self.castle:
            return "O-O"if self.endCol == 6 else "O-O-O"

        #will not add check and checkmate moves and if 2 of the same type pieces can move
        #to a single square we will not be able to denote it perfectly
        #can add this notation features later
        startSquare = self.getRankFile(self.startRow, self.startCol)
        endSquare = self.getRankFile(self.endRow, self.endCol)

        #pawn moves
        if self.pieceMoved[1]=='P':
            if self.isCapture():
                return self.colsToFiles[self.startCol] + "x" + endSquare
            else:
                return endSquare
            #leaving pawn promotions for now

        #two of the same type of piece capable of moving to the same square
        #also adding + for a check move and # for a checkmate move

        #piece moves
        moveString = self.pieceMoved[1] + startSquare
        if self.isCapture():
            moveString += 'x'
        return moveString + endSquare
