#!/usr/local/bin/python3

# The Blessed library, created by Jeff Quast, provides an interface for terminal colors, positioning, and input.
# https://pypi.org/project/blessed/
from blessed import Terminal
from enum import Enum


# Enum representing the two piece colors, white and black
class Team(Enum):
    WHITE = 0
    BLACK = 1


# Enum representing the possible states of the game
class State(Enum):
    MAIN_MENU = 0
    SELECT_PIECE = 1
    MOVE_PIECE = 2
    GAME_OVER = 3


# Get an instance of the terminal, provided by the Blessed module
term = Terminal()

# The dimensions of the board, used for accurately drawing to the terminal
BOARD_HEIGHT = 8
BOARD_WIDTH = 8
BOARD_MARGIN = 1

# The coordinates of the currently selected square
selected_square = (0, 0)

# Default values for state variables
game_state = State.MAIN_MENU
active_player = Team.BLACK
selected_action_idx = 0

# gray square background color
square_bg_gray = term.black_on_gray88
# white square background color
square_bg_white = term.black_on_bright_white
# red highlighted square background color
square_bg_highlighted_r = term.black_on_red
# yellow highlighted square background color
square_bg_highlighted_y = term.black_on_lightgoldenrod1
# green highlighted square background color
square_bg_highlighted_g = term.black_on_green3
# dimmed square background color
square_bg_dimmed = term.black_on_gray


# A class representing a game piece, with properties for its position, team, whether it's a king, whether it's currently
# in a jump chain, and lists of the possible actions it can take
class Piece:
    def __init__(self, pos, team):
        self.pos = pos
        self.team = team
        self.in_jump_chain = False
        self.is_king = False
        # The regular (non-jump) actions available to a piece
        self.possible_moves = []
        # The jumps available to a piece
        self.possible_jumps = []

    # Get the list of directions that might be available based on the piece's team and whether it's a king
    def get_directions(self):
        if self.is_king:
            return (-1, -1), (1, -1), (1, 1), (-1, 1)
        if self.team == Team.BLACK:
            return (-1, -1), (1, -1)
        else:
            return (-1, 1), (1, 1)

    # Update the actions available to the piece
    def reset_possible_actions(self):
        # If the piece has reached the end of the board, make it a king
        if (self.team == Team.BLACK and self.pos[1] == 0) or \
                (self.team == Team.WHITE and self.pos[1] == BOARD_HEIGHT - 1):
            self.is_king = True

        # Clear the lists containing the available actions and update them based on adjacent pieces
        self.possible_moves = []
        self.possible_jumps = []

        for direction in self.get_directions():
            target = (self.pos[0] + direction[0], self.pos[1] + direction[1])
            double_target = (self.pos[0] + 2 * direction[0], self.pos[1] + 2 * direction[1])
            if not (0 <= target[0] < BOARD_WIDTH and 0 <= target[1] < BOARD_HEIGHT):
                continue

            piece_at_target = get_piece_at(target, pieces)
            piece_at_double_target = get_piece_at(double_target, pieces)
            if piece_at_target is None:
                self.possible_moves.append(direction)
            elif piece_at_target.team != self.team and piece_at_double_target is None:
                if 0 <= double_target[0] < BOARD_WIDTH and 0 <= double_target[1] < BOARD_HEIGHT:
                    self.possible_jumps.append(direction)

        # Clear the list of possible moves if there are any jumps available
        if len(self.possible_jumps) > 0:
            self.possible_moves = []

    # Get the icon that should be used to draw the piece
    def get_icon(self):
        if self.is_king:
            return '◇' if self.team == Team.WHITE else '◆'
        else:
            return '○' if self.team == Team.WHITE else '●'


# Print to the console at a certain coordinate
def echo(val, x, y, flush=True, add_margin=True):
    with(term.location(x, y + (BOARD_MARGIN if add_margin else 0))):
        print(val, end='', flush=flush)


# Get the piece at a certain coordinate position, or return None if the coordinate is empty
def get_piece_at(coords, piece_list):
    for piece in piece_list:
        if piece.pos == coords:
            return piece
    return None


# Reset the possible actions of all the pieces on the board
def reset_piece_actions():
    for piece in pieces:
        piece.reset_possible_actions()


# Get the list of all the pieces belonging to a specified team
def get_team_pieces(team):
    team_pieces = []
    for piece in pieces:
        if piece.team == team:
            team_pieces.append(piece)
    return team_pieces


# Get a list of pieces on a specified team that have jumps available (and are thus required to jump)
def get_jump_pieces(team):
    jump_pieces = []
    for piece in get_team_pieces(team):
        if piece.in_jump_chain:
            return [piece]
        elif len(piece.possible_jumps) > 0:
            jump_pieces.append(piece)
    return jump_pieces


# Get a list of pieces on a specified team that can complete any action (either a regular move or a jump)
def get_available_pieces(team):
    available_pieces = []
    jump_pieces = get_jump_pieces(team)
    if len(jump_pieces) > 0:
        available_pieces = jump_pieces
    else:
        for piece in get_team_pieces(team):
            if len(piece.possible_moves) > 0:
                available_pieces.append(piece)
    return available_pieces


# Checks if the sum of two numbers, usually coordinate positions, is an odd number
def is_sum_odd(x, y):
    return (x + y) % 2 == 1


# At the start of the game, draw a border around the board
def draw_border(width, height):
    for border_y in range(height - 2):
        echo('║', 0, border_y + 1)
        echo('║', width - 1, border_y + 1)
    for border_x in range(width - 2):
        echo('═', border_x + 1, 0)
        echo('═', border_x + 1, height - 1)
    echo('╔', 0, 0)
    echo('╗', width - 1, 0)
    echo('╚', 0, height - 1)
    echo('╝', width - 1, height - 1)


# Draw the board, including pieces and colored squares
def draw_board(highlighted_squares, piece_list):
    for x in range(BOARD_WIDTH):
        for y in range(BOARD_HEIGHT):
            background_color = square_bg_white if is_sum_odd(x, y) else square_bg_gray
            for highlight_color in highlighted_squares.keys():
                if (x, y) in highlighted_squares[highlight_color]:
                    background_color = highlight_color
            piece = get_piece_at((x, y), piece_list)
            if piece is not None:
                icon = piece.get_icon()
                echo(background_color(' ' + icon + ' '), x * 3 + 2, y + 1)
            else:
                echo(background_color('   '), x * 3 + 2, y + 1)


# Depending on the state of the game, print the actions available to the player
def print_available_inputs(state):
    available_inputs = ''
    if state == State.MAIN_MENU:
        available_inputs = '[press any key to start!]'
    elif state == State.SELECT_PIECE:
        available_inputs = 'move:  ▲\tselect: [z]' + term.move_down() + term.move_right(5) + '◄ ▼ ►'
    elif state == State.MOVE_PIECE:
        available_inputs = 'select: [z]\tcancel: [x]' + term.move_down() + 'cycle actions: ◄ ►'
    elif state == State.GAME_OVER:
        available_inputs = 'quit: [q]'

    echo(term.clear_eos + available_inputs, 0, BOARD_HEIGHT + 2)


# Every time the user presses a valid key on the keyboard, perform a function based on the game's current state
def update_inputs(last_key):
    global selected_square
    global game_state
    global selected_action_idx
    global active_player

    # If the main menu is active, start the game as soon as a key is pressed.
    if game_state == State.MAIN_MENU:
        game_state = State.SELECT_PIECE

    # If the game is in its default state:
    # Calculate the direction to move the selection based on the user's inputs
    # If the user presses the 'z' key and the selected piece can be moved, change the state to MOVE_PIECE
    elif game_state == State.SELECT_PIECE:
        # Key codes: left = 260, up = 259, down = 258, right = 261
        move_h = (last_key.code == 261) - (last_key.code == 260)
        move_v = (last_key.code == 258) - (last_key.code == 259)
        selected_square = ((selected_square[0] + move_h) % BOARD_WIDTH, (selected_square[1] + move_v) % BOARD_HEIGHT)

        if last_key == 'z' and get_piece_at(selected_square, pieces) in get_available_pieces(active_player):
            game_state = State.MOVE_PIECE
            selected_action_idx = 0
            return

    # If a piece has been chosen:
    # Cancel the piece selection and return to the default state if the player presses the 'x' key
    # Cycle through the possible movement options based on the user's inputs
    # If the user presses the 'z' key, execute the selected move, removing any piece that was jumped over and ending
    # the game if necessary
    elif game_state == State.MOVE_PIECE:
        selected_piece = get_piece_at(selected_square, pieces)

        if last_key == 'x':
            game_state = State.SELECT_PIECE
            update_inputs(last_key)
            return

        cycle = (last_key.code == 261) - (last_key.code == 260)
        # Get the total number of possible moves OR jumps (works because the two lists are mutually exclusive)
        total_num_actions = len(selected_piece.possible_moves) + len(selected_piece.possible_jumps)
        selected_action_idx = (selected_action_idx + cycle) % total_num_actions

        if last_key == 'z':
            pos = selected_piece.pos

            if len(selected_piece.possible_jumps) > 0:
                # Move the selected piece, and find and remove the one that was jumped over
                sel_action = selected_piece.possible_jumps[selected_action_idx]
                pieces.remove(get_piece_at((sel_action[0] + pos[0], sel_action[1] + pos[1]), pieces))
                selected_piece.pos = (sel_action[0] * 2 + pos[0], sel_action[1] * 2 + pos[1])

                reset_piece_actions()

                # End the game if the opponent has no remaining pieces they can move
                if len(get_available_pieces(Team.BLACK if active_player == Team.WHITE else Team.WHITE)) == 0:
                    game_state = State.GAME_OVER
                    return

                # Enter a jump chain if another jump can be performed by the same piece
                if len(selected_piece.possible_jumps) > 0:
                    selected_piece.in_jump_chain = True
                    selected_square = selected_piece.pos
                    game_state = State.SELECT_PIECE
                    return
                else:
                    selected_piece.in_jump_chain = False
            else:
                # For regular moves, simply move the piece and reset the available piece actions
                sel_action = selected_piece.possible_moves[selected_action_idx]
                selected_piece.pos = (sel_action[0] + pos[0], sel_action[1] + pos[1])
                reset_piece_actions()

            # If the move didn't result in a jump chain or the end of the game, return to the DEFAULT state and begin
            # the opponent's turn
            selected_square = selected_piece.pos
            game_state = State.SELECT_PIECE
            active_player = Team.BLACK if active_player == Team.WHITE else Team.WHITE
            return

    elif game_state == State.GAME_OVER:
        pass


# Update the variables used to display the board, including lists of which pieces should be highlighted which color
# The display will change based on the game's current state
def update_display():
    # Key: the terminal color the squares should be highlighted with
    # Value: a list of squares to be highlighted with that color
    # Colors are drawn in the order of the keys, first to last
    highlighted_squares = {
        square_bg_highlighted_y: [],
        square_bg_highlighted_r: [],
        square_bg_highlighted_g: [],
        square_bg_dimmed: [],
    }

    # If the game is on the main menu, dim the white squares
    if game_state == State.MAIN_MENU:
        # This list comprehension is based on a StackOverflow solution:
        # https://stackoverflow.com/questions/3633140/nested-for-loops-using-list-comprehension
        highlighted_squares[square_bg_dimmed] = [(x, y) for x in range(0, 8) for y in range(0, 8) if is_sum_odd(x, y)]

    # If the game is in its default state:
    # Highlight any pieces that have jumps available with yellow
    # Highlight the currently selected square green if it contains a movable piece, otherwise highlight it red
    elif game_state == State.SELECT_PIECE:
        selected_piece = get_piece_at(selected_square, pieces)
        jump_pieces = get_jump_pieces(active_player)
        movable_pieces = get_available_pieces(active_player)

        selection_hl_color = square_bg_highlighted_g if selected_piece in movable_pieces else square_bg_highlighted_r
        highlighted_squares[selection_hl_color] = [selected_square]
        highlighted_squares[square_bg_highlighted_y] = [piece.pos for piece in jump_pieces]

    # If a piece has been chosen:
    # Dim the square containing the selected piece
    # Highlight the currently selected move green, and all other available moves yellow
    # If there are jumps available, highlight any pieces that will be eliminated red
    elif game_state == State.MOVE_PIECE:
        selected_piece = get_piece_at(selected_square, pieces)
        pos = selected_piece.pos
        if len(selected_piece.possible_jumps) > 0:
            for i, action in enumerate(selected_piece.possible_jumps):
                target_color = square_bg_highlighted_g if i == selected_action_idx else square_bg_highlighted_y
                highlighted_squares[target_color].append((action[0] * 2 + pos[0], action[1] * 2 + pos[1]))

            highlighted_squares[square_bg_highlighted_r] = [
                (action[0] + pos[0], action[1] + pos[1]) for action in selected_piece.possible_jumps
            ]
        else:
            for i, action in enumerate(selected_piece.possible_moves):
                target_color = square_bg_highlighted_g if i == selected_action_idx else square_bg_highlighted_y
                highlighted_squares[target_color].append((action[0] + pos[0], action[1] + pos[1]))

        highlighted_squares[square_bg_dimmed] = [pos]

    # Draw the board and print information on the available inputs and game state
    draw_board(highlighted_squares, [] if game_state == State.MAIN_MENU else pieces)
    print_available_inputs(game_state)
    if game_state == State.MAIN_MENU:
        echo(term.clear_eol + "Welcome to CHECKERS!", 0, 0, add_margin=False)
    elif game_state == State.GAME_OVER:
        echo(term.clear_eol + active_player.name + " wins!", 0, 0, add_margin=False)
    else:
        echo(term.clear_eol + active_player.name + "'s turn...", 0, 0, add_margin=False)


# A list containing every piece currently in play
pieces = []

if __name__ == '__main__':
    # Instantiate the pieces at the correct locations
    for grid_x in range(BOARD_WIDTH):
        for grid_y in range(0, 3):
            if is_sum_odd(grid_x, grid_y):
                pieces.append(Piece((grid_x, grid_y), Team.WHITE))
        for grid_y in range(BOARD_HEIGHT - 3, BOARD_HEIGHT):
            if is_sum_odd(grid_x, grid_y):
                pieces.append(Piece((grid_x, grid_y), Team.BLACK))

    # Calculate the actions available to each piece
    reset_piece_actions()

    with term.cbreak(), term.hidden_cursor(), term.fullscreen():
        # Clear the screen and draw a border
        print(term.home + term.clear)
        draw_border(BOARD_WIDTH * 3 + 4, BOARD_HEIGHT + 2)

        # Start the game loop
        key_press = ''
        while key_press != 'q':
            update_display()
            key_press = term.inkey()
            update_inputs(key_press)
