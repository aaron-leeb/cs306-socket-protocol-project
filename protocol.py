import json
# Shared protocol constants and helpers for client and server

MSG_TYPE_CHAT = "chat"
MSG_TYPE_CONNECT = "connect"

# Protocol message types for lobby/game management
MSG_TYPE_START_GAME = "start_game"
MSG_TYPE_JOIN_GAME = "join_game"

# Protocol message types
MSG_TYPE_DISCOVER = "discover"
MSG_TYPE_ANNOUNCE = "announce"
MSG_TYPE_CONNECT = "connect"
MSG_TYPE_WAITING = "waiting"
MSG_TYPE_START = "start"
MSG_TYPE_MOVE = "move"
MSG_TYPE_BOARD = "board"
MSG_TYPE_ERROR = "error"
MSG_TYPE_GAME_OVER = "game_over"
MSG_TYPE_OPPONENT_DISCONNECTED = "opponent_disconnected"

# Error codes
ERROR_INVALID_JSON = "invalid_json"
ERROR_INVALID_MESSAGE = "invalid_message"
ERROR_GAME_NOT_STARTED = "game_not_started"
ERROR_GAME_FULL = "game_full"
ERROR_NOT_YOUR_TURN = "not_your_turn"
ERROR_INVALID_COORDINATES = "invalid_coordinates"
ERROR_CELL_OCCUPIED = "cell_occupied"
ERROR_GAME_OVER = "game_over"

# Game results
RESULT_X_WINS = "x_wins"
RESULT_O_WINS = "o_wins"
RESULT_DRAW = "draw"

# Server states
STATE_EMPTY = "EMPTY"
STATE_WAITING = "WAITING"
STATE_ACTIVE = "ACTIVE"
STATE_FINISHED = "FINISHED"

# Default ports
DEFAULT_TCP_PORT = 50555
DEFAULT_UDP_PORT = 50556

# Exit command for CLI
EXIT_COMMAND = "exit"


# Helper: encode a message as JSON line
def encode_message(message: dict) -> bytes:
	return (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")

# Helper: decode a JSON line message
def decode_message(data: bytes) -> dict:
	return json.loads(data.decode("utf-8"))
