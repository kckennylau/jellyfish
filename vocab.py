from utils import *
from print_parse import *
import sys
import math
import random
import itertools
from enum import Enum

func_defs = {}
oper_defs = {}

class Roles(Enum):
    function = 0
    operator = 1

def get_defs(role):
    if role == Roles.function:
        return func_defs
    else:
        return oper_defs

def defun(char, arity, role):
    def define_cmd(func):
        defs = get_defs(role)
        if char in defs:
            impl = list(defs[char])
        else:
            impl = [None, None]
        impl[arity-1] = func
        defs[char] = tuple(impl)
        return func
    return define_cmd

defun_unary = lambda char: defun(char, 1, Roles.function)
defun_binary = lambda char: defun(char, 2, Roles.function)
defop_unary = lambda char: defun(char, 1, Roles.operator)
defop_binary = lambda char: defun(char, 2, Roles.operator)

def mathy_unary(f):
    return lambda x: Atom(x.type, f(x.value))
    
def mathy_binary(f):
    return lambda x, y: Atom(x.type, f(x.value, y.value))

threaded_unary = lambda rank: lambda f: thread_unary(f, rank)
threaded_binary = lambda rank1, rank2: lambda f: thread_binary(f, rank1, rank2)

@defun_unary('{')
def func_left_id(a):
    return a

@defun_binary('{')
def func_left(a, b):
    return a

@defun_unary('}')
def func_right_id(a):
    return a

@defun_binary('}')
def func_right(a, b):
    return b

@defun_unary('j')
def func_input(a):
    return parse_value(input())[0]

@defun_binary('j')
@threaded_binary(0, -1)
def func_binary_input(a, b):
    if a.value > 0:
        string = "".join(chr(abs(int(item.value))) for item in flatten(b))
        return parse_value(string)[0]
    else:
        return [to_char_atom(c) for c in prettyprint(b)]

@defun_unary('J')
def func_raw_input(a):
    return [to_char_atom(c) for c in input()]

@defun_binary('J')
@threaded_binary(-1, 0)
def func_binary_raw_input(a, b):
    return [to_char_atom(c) for c in sys.stdin.read(int(b))]

@defun_unary('p')
def func_print(a):
    print(prettyprint(a))
    return a

@defun_binary('p')
def func_binary_print(a, b):
    raise Exception("Binary 'p' not implemented.")

@defun_unary('P')
def func_matrix_print(a):
    print(matrix_print(a))
    return a

@defun_binary('P')
def func_binary_matrix_print(a, b):
    raise Exception("Binary 'P' not implemented.")

@defun_unary('+')
@threaded_unary(0)
@mathy_unary
def func_abs(a): return abs(a)

@defun_binary('+')
@threaded_binary(0, 0)
@mathy_binary
def func_add(a, b): return a + b

@defun_unary('-')
@threaded_unary(0)
@mathy_unary
def func_negate(a): return -a

@defun_binary('-')
@threaded_binary(0, 0)
@mathy_binary
def func_subtract(a, b): return b - a

@defun_unary('*')
@threaded_unary(0)
@mathy_unary
def func_signum(a): return (a>0) - (a<0)

@defun_binary('*')
@threaded_binary(0, 0)
@mathy_binary
def func_multiply(a, b): return a * b

@defun_unary('%')
@threaded_unary(0)
@mathy_unary
def func_reciprocal(a):
    if a == 0:
        return 0 # TODO: give error?
    return 1/a

@defun_binary('%')
@threaded_binary(0, 0)
@mathy_binary
def func_divide(a, b):
    if a != 0 != b:
        if type(a) == int == type(b) and b % a == 0:
            return b // a
        return b / a
    return 0 # TODO: give errors?

@defun_unary('|')
@threaded_unary(0)
@mathy_unary
def func_round(a): return math.floor(a + 0.5)

@defun_binary('|')
@threaded_binary(0, 0)
@mathy_binary
def func_modulus(a, b):
    if a != 0 != b:
        return b % a
    return 0 # TODO: give errors?

@defun_unary('m')
@threaded_unary(0)
@mathy_unary
def func_floor(a): return math.floor(a)

@defun_binary('m')
def func_min(a, b): return min(a, b)

@defun_unary('M')
@threaded_unary(0)
@mathy_unary
def func_ceil(a): return math.ceil(a)

@defun_binary('M')
def func_max(a, b): return max(a, b)

@defun_unary('x')
@threaded_unary(0)
def func_factorize(a):
    n = int(a)
    if n == 0:
        return [to_num_atom(0)]
    if n > 0:
        fact = []
    else:
        n = -n
        fact = [to_num_atom(-1)]
    div = 2
    while n > 1:
        if n % div == 0:
            n //= div
            fact.append(to_num_atom(div))
        else:
            div += 1
    return fact
    

@defun_binary('x')
@threaded_binary(0, 0)
@mathy_binary
def func_xor(a, b): return a ^ b

@defun_unary('b')
def func_base2(a):
    return func_base(to_num_atom(2), a)

@defun_binary('b')
@threaded_binary(1, 0)
def func_base(a, b):
    if is_atom(a):
        base = a.value
        num = b.value
        digits = []
        while abs(num) >= abs(base):
            digits = [to_num_atom(num % base)] + digits
            if type(num) is int and type(base) is int:
                num = num // base
            else:
                num /= base
        return [to_num_atom(num)] + digits
    else:
        num = b.value
        digits = []
        for item in reversed(a):
            base = item.value
            digits = [to_num_atom(num % base)] + digits
            if type(num) is int and type(base) is int:
                num = num // base
            else:
                num /= base
        return digits

@defun_unary('d')
def func_antibase2(a):
    return func_antibase(to_num_atom(2), a)

@defun_binary('d')
@threaded_binary(1, 1)
def func_antibase(a, b):
    if is_atom(b):
        return b
    if is_atom(a):
        a = [a]*len(b)
    total = 0
    old_base = 1
    for base, n in reversed(list(zip(a, b))):
        total += n.value * old_base
        old_base *= base.value
    return to_num_atom(total)
        

@defun_unary('=')
def func_unary_eq(a):
    raise Exception("Unary '=' not implemented.")

@defun_binary('=')
def func_equals(a, b):
    if is_atom(a) != is_atom(b):
        return to_num_atom(0)
    else:
        return to_num_atom(int(a == b))

@defun_unary('<')
def func_head_dec(a):
    if is_atom(a):
        return Atom(a.type, a.value-1)
    else:
        return a[0]

@defun_binary('<')
def func_less_than(a, b):
    if is_atom(a):
        if is_atom(b):
            return to_num_atom(int(a < b))
        else:
            return to_num_atom(1)
    elif is_atom(b):
        return to_num_atom(0)
    else:
        return to_num_atom(int(a < b))

@defun_unary('>')
def func_tail_inc(a):
    if is_atom(a):
        return Atom(a.type, a.value+1)
    else:
        return a[1:]

@defun_binary('>')
def func_greater_than(a, b):
    if is_atom(a):
        if is_atom(b):
            return to_num_atom(int(a > b))
        else:
            return to_num_atom(0)
    elif is_atom(b):
        return to_num_atom(1)
    else:
        return to_num_atom(int(a > b))

@defun_unary('^')
def func_init_sqr(a):
    if is_atom(a):
        return Atom(a.type, a.value * a.value)
    else:
        return a[:-1]

@defun_binary('^')
@threaded_binary(0, -1)
def func_take_pow(a, b):
    n = a.value
    if is_atom(b):
        return Atom(a.type, b.value ** n)
    elif n >= 0:
        return b[:int(n)]
    else:
        return b[int(n):]

@defun_unary('v')
def func_last_sqrt(a):
    if is_atom(a):
        return Atom(a.type, math.sqrt(a.value))
    else:
        return a[-1]

@defun_binary('v')
@threaded_binary(0, -1)
def func_drop_root(a, b):
    n = a.value
    if is_atom(b):
        return Atom(a.type, b.value ** (1/n))
    elif n >= 0:
        return b[int(n):]
    else:
        return b[:int(n)]

@defun_unary('!')
def func_permutations(a):
    if is_atom(a):
        return Atom(a.type, math.factorial(int(a.value)))
    else:
        return [list(p) for p in itertools.permutations(a)]

@defun_binary('!')
@threaded_binary(0, -1)
def func_binary_permutations(a, b):
    if is_atom(b):
        return Atom(a.type, math.factorial(int(b.value)) // math.factorial(int(b.value - a.value)))
    else:
        return [list(p) for p in itertools.permutations(b, int(a))]

@defun_unary('c')
@threaded_unary(0)
def func_to_char(a): return Atom(AtomType.char, a.value)

@defun_binary('c')
def func_elem(a, b):
    if is_atom(b):
        b = [b]
    return to_num_atom(int(a in b))

@defun_unary('C')
def func_subsequences(a):
    if is_atom(a):
        return Atom(a.type, 2**a.value)
    else:
        return [list(s)
                for i in range(len(a)+1)
                for s in itertools.combinations(a, i)]

@defun_binary('C')
@threaded_binary(0, -1)
def func_combinations(a, b):
    x = a.value
    if is_atom(b):
        y = b.value
        if y < x:
            return Atom(a.type, 0)
        z = math.factorial(int(y)) // math.factorial(int(x)) // math.factorial(int(y - x))
        return Atom(a.type, z)
    elif b:
        x = x % len(b)
        return [list(c) for c in itertools.combinations(b, x)]
    else:
        return []

@defun_unary('n')
@threaded_unary(0)
def func_to_num(a): return Atom(AtomType.num, a.value)

@defun_binary('n')
def func_intersection(a, b):
    if is_atom(a):
        a = [a]
    if is_atom(b):
        b = [b]
    return [x for x in a if x in b]

@defun_unary('u')
def func_uniques(a):
    if is_atom(a):
        return [a]
    else:
        return uniques(a)

@defun_binary('u')
def func_union(a, b):
    if is_atom(a):
        a = [a]
    if is_atom(b):
        b = [b]
    return a + [x for x in uniques(b) if x not in a]

@defun_unary('N')
def func_not(a):
    if is_truthy(a):
        return to_num_atom(0)
    else:
        return to_num_atom(1)

@defun_binary('N')
def func_without(a, b):
    if is_atom(a):
        a = [a]
    if is_atom(b):
        b = [b]
    return [x for x in a if x not in b]

@defun_unary('#')
def func_len(a):
    if is_atom(a):
        return to_num_atom(len(func_base(to_num_atom(10), a)))
    else:
        return to_num_atom(len(a))

@defun_binary('#')
@threaded_binary(1, -1)
def func_repeat(a, b):
    if is_atom(b):
        b = [b]
    if is_atom(a):
        a = [a]*len(b)
    else:
        return [y for (x,y) in zip(a,b) for _ in range(int(x))]

@defun_unary('R')
def func_reverse(a):
    if is_atom(a):
        return a
    else:
        return list(reversed(a))

@defun_binary('R')
@threaded_binary(0, -1)
def func_rotate(a, b):
    if is_atom(b) or not b:
        return b
    elif b:
        a = int(a) % len(b)
        return b[a:] + b[:a]

@defun_unary('k')
@threaded_unary(1)
def func_mask_to_indices(a):
    if is_atom(a):
        return [to_num_atom(0)]*int(a.value)
    else:
        return [to_num_atom(i) for (i, x) in enumerate(a) for _ in range(int(x.value))]

@defun_binary('k')
def func_binary_k(a, b):
    raise Error("Binary 'k' not implemented.")

@defun_unary('K')
@threaded_unary(1)
def func_indices_to_mask(a):
    if is_atom(a):
        a = [a]
    a = [int(n.value) for n in a]
    return [to_num_atom(a.count(i)) for i in range(max(a) + 1)]

@defun_binary('K')
def func_binary_K(a, b):
    raise Error("Binary 'K' not implemented.")

@defun_unary('o')
def func_sort(a):
    if is_atom(a):
        a = [a]
    return list(sorted(a))

@defun_binary('o')
def func_binary_sort(a, b):
    if is_atom(a) or not(a):
        a = [a]
    if is_atom(b):
        b = [b]
    a = (a*len(b))[:len(b)]
    return [x for (y, x) in sorted(zip(a, b))]

@defun_unary('r')
def func_unary_range(a):
    return un_range(a)

@defun_binary('r')
def func_binary_range(a, b):
    pairs = thread_binary(lambda x, y: [x, y], 0, 0)(a, b)
    return bin_range(pairs)

@defun_unary(',')
def func_flatten(a):
    return flatten(a)

@defun_binary(',')
def func_append(a, b):
    if is_atom(a):
        if is_atom(b):
            return [a, b]
        else:
            return [a] + b
    elif is_atom(b):
        return a + [b]
    else:
        return a + b

@defun_unary(';')
def func_singleton(a):
    return [a]

@defun_binary(';')
def func_pair(a, b):
    return [a, b]

@defun_unary('$')
def func_shape(a):
    return [to_num_atom(dim) for dim in shape(a)]

@defun_binary('$')
@threaded_binary(1, -1)
def func_reshape(a, b):
    if is_atom(a):
        a = [a]
    return reshape(b, a)

@defun_unary('@')
def func_indices(a):
    if is_atom(a):
        return to_num_atom(0)
    res = []
    for ind, item in enumerate(a):
        if is_atom(item):
            res.append([to_num_atom(ind)])
        else:
            for subind in func_indices(item):
                res.append([to_num_atom(ind)] + subind)
    return res

@defun_binary('@')
@threaded_binary(-2, -1)
def func_index(a, b):
    if is_atom(b):
        return b
    if is_atom(a):
        return b[int(a) % len(b)]
    for ind in flatten(a):
        b = b[int(ind) % len(b)]
        if is_atom(b):
            return b
    return b

@defun_unary('?')
def func_random_gen(a):
    if is_atom(a):
        x = a.value
        if type(x) == float:
            if x >= 0:
                res = random.uniform(0, x)
            else:
                res = random.uniform(x, 0)
        elif x == 0:
            res = random.random()
        elif x > 0:
            res = random.randrange(0, x)
        else:
            res = random.rangrange(x+1, 1)
        return Atom(a.type, res)
    else:
        res = a[:]
        random.shuffle(res)
        return res

@defun_binary('?')
@threaded_binary(1, -1)
def func_random_choice(a, b):
    if is_atom(b):
        b = func_unary_range(b)
    if is_atom(a):
        chosen = sorted(random.sample(range(len(b)), min(len(b), int(a))))
        return [b[i] for i in chosen]
    else:
        res = []
        for item in a:
            chosen = sorted(random.sample(range(len(b)), min(len(b), int(item))))
            res.append([b[i] for i in chosen])
            b = [val for (i, val) in enumerate(b) if i not in chosen]
        return res

def variadize(func, binary=None):
    if binary is None:
        unary, binary = func
    else:
        unary = func
    def variadic(a, b=None):
        if a is None:
            if b is None:
                return None
            else:
                return unary(b)
        elif b is None:
            return unary(a)
        else:
            return binary(a, b)
    return variadic

@defop_unary('_')
def oper_id(f):
    if is_value(f):
        raise Exception("Unary '_' on values not implemented.")
    return f

@defop_binary('_')
def oper_left(f, g):
    if is_value(f):
        if is_value(g):
            raise Exception("Binary '_' on values not implemented.")
        return oper_const_or_flip(g(f))
    if is_value(g):
        return oper_const_or_flip(f(g))
    return f

@defop_unary('~')
def oper_const_or_flip(f):
    if is_value(f):
        return variadize(lambda a: f,
                         lambda a, b: f)
    return variadize(lambda a: f(a),
                     lambda a, b: f(b, a))

@defop_binary('~')
def oper_curry_or_precompose(f, g):
    if is_value(f):
        if is_value(g):
            return variadize(lambda a: [f, g],
                             lambda a, b: [f, g])
        return variadize(lambda a: g(f, a),
                         lambda a, b: g(f, b))
    elif is_value(g):
        return variadize(lambda a: f(a, g),
                         lambda a, b: f(a, g))
    return variadize(lambda a: g(f(a)),
                     lambda a, b: f(g(a), g(b)))

@defop_unary('&')
def oper_swap_arity(f):
    return variadize(lambda a: f(a, a),
                     lambda a, b: f(b))

@defop_binary('&')
def oper_twosided_curry_or_postcompose(f, g):
    if is_value(f):
        if is_value(g):
            raise Exception("Binary '&' on values not implemented.")
        def two_sided(a):
            return g(f, g(a, f))
        return variadize(two_sided,
                         lambda a, b: iterate(two_sided, b, int(a)))
    elif is_value(g):
        def two_sided(a):
            return f(f(g, a), g)
        return variadize(two_sided,
                         lambda a, b: iterate(two_sided, b, int(a)))
    return variadize(lambda a: f(g(a)),
                     lambda a, b: f(g(a, b)))

@defop_unary('(')
def oper_left_unary_hook(f):
    return variadize(lambda a: [f(a), a],
                     lambda a, b: [f(a), b])

@defop_binary('(')
def oper_left_hook(f, g):
    return variadize(lambda a: g(f(a), a),
                     lambda a, b: g(f(a), b))

@defop_unary(')')
def oper_right_unary_hook(f):
    return variadize(lambda a: [a, f(a)],
                     lambda a, b: [a, f(b)])

@defop_binary(')')
def oper_right_hook(f, g):
    return variadize(lambda a: f(a, g(a)),
                     lambda a, b: f(a, g(b)))

@defop_unary('[')
def oper_left_unary_fork(f):
    return variadize(lambda a: [f(a), a],
                     lambda a, b: [f(a, b), b])

@defop_binary('[')
def oper_left_fork(f, g):
    return variadize(lambda a: g(f(a), a),
                     lambda a, b: g(f(a, b), b))

@defop_unary(']')
def oper_right_unary_fork(f):
    return variadize(lambda a: [a, f(a)],
                     lambda a, b: [a, f(a, b)])

@defop_binary(']')
def oper_right_fork(f, g):
    return variadize(lambda a: f(a, g(a)),
                     lambda a, b: f(a, g(a, b)))

@defop_unary('`')
def oper_unary_thread(f):
    if is_value(f):
        return variadize(thread_unary(lambda a: f, 0),
                         thread_binary(lambda a, b: f, 0, 0))
    return variadize(thread_unary(f, 0),
                     thread_binary(f, 0, 0))

@defop_binary('`')
def oper_binary_thread(f, g):
    if is_value(f):
        if is_value(g):
            sole, right, left = reshape(g, [3])
            return variadize(thread_unary(lambda a: f, int(sole)),
                             thread_binary(lambda a, b: f, int(left), int(right)))
        sole, right, left = reshape(f, [3])
        return variadize(thread_unary(g, int(sole)),
                         thread_binary(g, int(left), int(right)))
    elif is_value(g):
        sole, right, left = reshape(g, [3])
        return variadize(thread_unary(f, int(sole)),
                         thread_binary(f, int(left), int(right)))
    def dynamic_thread_unary(a):
        level = reshape(f(a), [])
        return thread_unary(g, int(level))(a)
    def dynamic_thread_binary(a, b):
        _, right, left = reshape(f(a, b), [3])
        return thread_binary(g, int(left), int(right))(a, b)
    return variadize(dynamic_thread_unary, dynamic_thread_binary)

@defop_unary('L')
def oper_unary_levels(f):
    if is_value(f):
        return oper_binary_levels(f, variadize(lambda a: a,
                                               lambda a, b: [a, b]))
    return oper_binary_levels(0, f)

@defop_binary('L')
def oper_binary_levels(f, g):
    if is_value(g):
        return oper_binary_levels(f, oper_const_or_flip(g))
    if is_value(f):
        def level_map(a):
            def map_at(level):
                return [g(x) for x in flatten(a, int(level))]
            return thread_unary(map_at, 0)(f)
        def level_zip(a, b):
            def zip_at(level):
                _, right, left = reshape(level, [3])
                return [g(x, y) for (x, y) in zip(flatten(a, int(left)), flatten(b, int(left)))]
            return thread_unary(zip_at, 1)(f)
        return variadize(level_map, level_zip)
    return variadize(lambda a: oper_binary_levels(f(a), g)(a),
                     lambda a, b: oper_binary_levels(f(a, b), g)(a, b))

@defop_unary('/')
def oper_join_or_fold(f):
    if is_value(f):
        return variadize(lambda a:
                         thread_unary(lambda times:
                                      join_times(a, int(times)),
                                      0)(f),
                         lambda a, b:
                         thread_unary(lambda times:
                                      join_times(intersperse(a, b),
                                                 int(times)),
                                      0)(f))
    def folded(a):
        if is_atom(a):
            return a
        if not a:
            return to_num_atom(0)
        x = a[0]
        for y in a[1:]:
            x = f(x, y)
        return x
    def folded_init(a, b):
        if is_atom(b):
            return f(a, b)
        for y in b:
            a = f(a, y)
        return a
    return variadize(folded, folded_init)

@defop_binary('/')
def oper_choice(f, g):
    if is_value(f):
        if is_value(g):
            return variadize(lambda a: f if is_truthy(a) else g,
                             lambda a, b: [f if is_truthy(a) else g, b])
        return variadize(lambda a: g(a) if is_truthy(f) else a,
                         lambda a, b: g(b) if is_truthy(f) else g(a))
    elif is_value(g):
        return variadize(lambda a: f(g) if is_truthy(a) else g,
                         lambda a, b: f(b) if is_truthy(a) else g)
    return variadize(lambda a: g(a) if is_truthy(f(a)) else a,
                     lambda a, b: f(b) if is_truthy(a) else g(b))

@defop_unary('\\')
def oper_substrings(f):
    if is_value(f):
        return variadize(lambda a: thread_unary(lambda b: infixes(a, int(b)), 0)(f),
                         lambda a, b: thread_binary(lambda u, v: u if is_atom(u) else u[int(v.value) % 2], 1, 0)
                                                   (thread_binary(lambda x, y: [x, y], -2, -2)(a, b), f))
    return variadize(lambda a: [f(p) for p in prefixes(a)],
                     thread_binary(lambda a, b: [f(p) for p in infixes(b, int(a))], 0, -1))

@defop_binary('\\')
def oper_iterate(f, g):
    if is_value(f):
        if is_value(g):
            raise Exception("Binary '\\' on values not implemented.")
        return variadize(lambda a: acc_iterate_until(g, a, lambda x, y: func_equals(y, f)),
                         lambda a, b: acc_iterate_until(lambda x: g(a, x), b, lambda x, y: func_equals(y, f)))
    if is_value(g):
        return variadize(lambda a: thread_unary(lambda n: iterate(f, a, int(n)), 0)(g),
                         lambda a, b: thread_unary(lambda n: iterate(lambda x: f(a, x), b, int(n)), 0)(g))
    return variadize(lambda a: iterate_until(f, a, g),
                     lambda a, b: iterate_until(lambda x: f(a, x), b, g))

@defop_unary('O')
def oper_prod_table(f):
    if is_value(f):
        return variadize(lambda a: thread_unary(lambda n: list(cartesian_product(a, int(n))), 0)(f),
                         lambda a, b: thread_unary(lambda n: list(cartesian_product(thread_binary(lambda x, y: [x, y], int(n), int(n))(a, b),
                                                                                    int(n)+1 if int(n) >= 0 else int(n))),
                                                   0)(f))
    return oper_binary_thread(f, [to_num_atom(-2), to_num_atom(-2), to_num_atom(-1)])

@defop_binary('O')
def oper_binary_O(f, g):
    raise Exception("Binary 'O' not implemented.")

@defop_unary('Z')
def oper_unary_Z(f):
    raise Exception("Unary 'Z' not implemented.")

@defop_binary('Z')
def oper_modify_indices(f, g):
    if is_value(f):
        return oper_modify_indices(oper_const_or_flip(f), g)
    if is_value(g):
        return oper_modify_indices(f, oper_const_or_flip(g))
    def modify_indices(ind, mod, a):
        indices = thread_unary(lambda x: x if is_value(x) else flatten(x), -2)(ind(a))
        new_items = mod(func_index(indices, a))
        if is_atom(indices):
            indices = [indices]
            new_items = [new_items]
        if is_atom(new_items):
            new_items = [new_items]*len(indices)
        a = full_copy(a)
        for index, item in zip(indices, new_items):
            if is_atom(a):
                a = item
                continue
            focus = old_focus = a
            old_coord = 0
            if is_atom(index):
                index = [index]
            for coord in index:
                new_focus = focus[int(coord) % len(focus)]
                old_coord = coord
                old_focus = focus
                if is_atom(new_focus):
                    break
                focus = new_focus
            old_focus[int(old_coord) % len(old_focus)] = item
        return a
    return variadize(lambda a: modify_indices(f, g, a),
                     lambda a, b: modify_indices(lambda x: f(a, x), lambda x: g(a, x), b))

func_defs = {c:variadize(f) for (c,f) in func_defs.items()}
oper_defs = {c:variadize(f) for (c,f) in oper_defs.items()}
