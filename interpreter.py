from utils import *
from vocab import *
from enum import Enum
import math


class Dir(Enum):
    east = 0
    south = 1

class ItemType(Enum):
    data = 0
    function = 1
    operator = 2
    control = 3
    dummy = 4

class Item:
    "An item in the matrix"
    
    def __init__(self, type, content, filled=False, evald=False):
        self.type = type
        self.content = content
        self.filled = filled
        self.evald = evald
        self.value = None
        self.func = None
        self.l_arg = None
        self.r_arg = None

    def evaluate(self):
        if self.type in [ItemType.function, ItemType.operator] and not self.evald:
            self.value = self.func(self.l_arg, self.r_arg)
            self.evald = True
        return self.value

class Connection:
    "A connection to an item, possibly blocking some fields."
    
    def __init__(self, pos, has_value, has_func, has_args):
        self.pos = pos
        self.has_value = has_value
        self.has_func = has_func
        self.has_args = has_args

def find_item(items, max_x, max_y, x, y, direction):
    "Returns a Connection object."
    has_value = has_func = has_args = True
    while x <= max_x and y <= max_y:
        if (x,y) in items:
            item = items[(x,y)]
            if item.type == ItemType.data:
                return Connection((x,y), has_value, False, has_args)
            elif item.type == ItemType.function or item.type == ItemType.operator:
                return Connection((x,y), has_value, has_func, has_args)
            elif item.type == ItemType.control:
                char = item.content
                if char == 'B': # Block all
                    return Connection(None, False, False, False)
                elif char == 'V': # Block value
                    has_value = False
                elif char == 'F': # Block function
                    has_func = False
                elif char == 'A': # Block arguments
                    has_args = False
                elif char == 'X': # Switch direction
                    if direction == Dir.east:
                        direction = Dir.south
                    else:
                        direction = Dir.east
                elif char == 'S': # Turn south
                    direction = Dir.south
                elif char == 'E': # Turn east
                    direction = Dir.east
        if direction == Dir.east:
            x += 1
        else:
            y += 1
    return Connection(None, False, False, False)

def parse(matrix):
    "Parse a code matrix into a graph of items."
    items = {}
    digits = "0123456789"
    control_chars = "BVFAESX"
    for y in range(len(matrix)):
        # Parse a row
        x = 0
        while x < len(matrix[y]):
            char = matrix[y][x]
            if char == "'":
                # Parse a character
                if x == len(matrix[y]) - 1:
                    parsed_char = '\n'
                else:
                    parsed_char = matrix[y][x+1]
                item = Item(ItemType.data, to_char_atom(parsed_char))
                items[(x,y)] = item
                x += 2
            elif char == '"':
                # Parse a string
                i = x + 1
                chars = []
                while i < len(matrix[y]) and matrix[y][i] != '"':
                    parsed_char = matrix[y][i]
                    if parsed_char == '\\':
                        if i == len(matrix[y]) - 1:
                            parsed_char = '\n'
                        else:
                            parsed_char = matrix[y][i+1]
                            if parsed_char == 'n':
                                parsed_char = '\n'
                        i += 2
                    else:
                        i += 1
                    chars.append(parsed_char)
                item = Item(ItemType.data, [to_char_atom(c) for c in chars])
                items[(x,y)] = item
                x = i + 1
            elif char in digits:
                # Parse a number
                num = ""
                i = x
                while i < len(matrix[y]) and matrix[y][i] in digits:
                    num += matrix[y][i]
                    i += 1
                item = Item(ItemType.data, to_num_atom(int(num)))
                items[(x,y)] = item
                x = i
            elif char == 'i':
                # Parse input
                input_value = parse_value(input())[0]
                item = Item(ItemType.data, input_value)
                items[(x,y)] = item
                x += 1
            elif char == 'I':
                # Parse raw string input
                input_string = input()
                input_value = [to_char_atom(char) for char in input_string]
                item = Item(ItemType.data, input_value)
                items[(x,y)] = item
                x += 1
            elif char in func_defs:
                # Parse a function
                item = Item(ItemType.function, func_defs[char])
                items[(x,y)] = item
                x += 1
            elif char in oper_defs:
                # Parse a operator
                item = Item(ItemType.operator, oper_defs[char])
                items[(x,y)] = item
                x += 1
            elif char in control_chars:
                # Parse a control character
                item = Item(ItemType.control, char)
                items[(x,y)] = item
                x += 1
            else:
                x += 1
    triples = {}
    max_x = max(len(row) for row in matrix)
    max_y = len(matrix)
    for ((x, y), item) in items.items():
            l_conn = find_item(items, max_x, max_y, x, y+1, Dir.south)
            r_conn = find_item(items, max_x, max_y, x+1, y, Dir.east)
            triples[(x,y)] = (item, l_conn, r_conn)
    triples[None] = (Item(ItemType.dummy, "Dummy"), None, None)
    return triples

def fill(items, pos=(0,0), level=0):
    "Fill in the fields of the given items."
    item, l_conn, r_conn = items[pos]
    if item.filled or item.type == ItemType.dummy:
        return item
    if item.type == ItemType.data:
        item.value = item.content
        item.r_arg = item.content
    else:
        l_nbor = fill(items, l_conn.pos, level+1)
        r_nbor = fill(items, r_conn.pos, level+1)
        if item.type == ItemType.function:
            item.func = item.content
            item.l_arg = l_nbor.evaluate() if l_conn.has_value else None
            item.r_arg = r_nbor.evaluate() if r_conn.has_value else None
        elif item.type == ItemType.operator:
            oper = item.content
            if l_conn.has_func and l_nbor.func is not None:
                l_input = l_nbor.func
            else:
                l_input = l_nbor.evaluate() if l_conn.has_value else None
            if r_conn.has_func and r_nbor.func is not None:
                r_input = r_nbor.func
            else:
                r_input = r_nbor.evaluate() if r_conn.has_value else None
            item.func = oper(l_input, r_input)
            r_l_arg = r_nbor.l_arg if r_conn.has_args else None
            r_r_arg = r_nbor.r_arg if r_conn.has_args else None
            if r_l_arg is None and r_r_arg is None:
                item.l_arg = l_nbor.l_arg if l_conn.has_args else None
                item.r_arg = l_nbor.r_arg if l_conn.has_args else None
            else:
                item.l_arg, item.r_arg = r_l_arg, r_r_arg
    item.filled = True
    return item

def interpret(matrix):
    "Interpret a program, returning the top left value."
    items = parse(matrix)
    corner = fill(items)
    return corner.evaluate()
