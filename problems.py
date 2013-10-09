# coding=utf-8

# Problems.
# Each problem is represented with a class. The class must have
# methods:
# - generate() which generates and returns a pair (data, seed)
# - - seed is any data that can help with verifying the problem but that we
# - verify(data, seed, output) which verifies a user's output and returns their score

import random
import string

problem_list = [
        "yolo",
        "splitsum",
        "ascii_triangle",
        "viking_olympics"
        ]

#words = open('cracklib-small').read().split()

# The "YOLO" problem. Data is nonsensical Japanese. Solution is anything.
class yolo:
    title = "YOLO"
    desc = "Just do anything. You'll get a free 100 points."
    url = "yolo"

    @staticmethod
    def generate():
        hiragana = u'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
        crap = ''.join(random.choice(hiragana) for i in range(random.randint(40, 60)))
        return crap, ""

    @staticmethod
    def verify(data, seed, output):
        return 100


# The "split sum" problem. Generates 100 space-separated integers. Requires the sum.
class splitsum:
    title = "Sums"
    desc = """You will be given 100 space-separated integers. Get their sum."""
    url = "sums"

    @staticmethod
    def generate():
        return ' '.join(map(str, [random.randint(1000, 99999) for i in range(100)])), ""
    
    @staticmethod
    def verify(data, seed, output):
        if str(sum(map(int, data.split()))) == output:
            return 100
        else:
            return 0


# Ascii triangle.
# Input 3
# ..#..
# .###.
# #####
# Input 4
# ...#...
# ..###..
# .#####.
# #######
class ascii_triangle:
    title = "ASCII Triangle"
    url = "ascii-triangle"

    @staticmethod
    def generate():
        N = 15
        triangles = list(range(1, 16))
        random.shuffle(triangles)
        return '\n'.join(map(str, [N]+triangles)) + '\n', ""

    @staticmethod
    def solve(data):
        nums = list(map(int, data.split()))
        N = nums[0]
        # It works. Just trust me.
        answer = '\n'.join('\n'.join('.'*(h-i) + '#'*(i*2-1) + '.'*(h-i) for i in range(1, h+1)) for h in nums[1:])
        return answer
    
    @staticmethod
    def verify(data, seed, output):
        answer = ascii_triangle.solve(data)
        if output.strip() == answer.strip():
            return 100
        else:
            return 0

class viking_olympics:
    title = "Viking Olympics"
    url = "viking-olympics"

    @staticmethod
    def generate():
        def make_word():
            return ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(5, 10)))
        data = ""
        N = random.randint(6, 8)
        data += str(N) + "\n"
        data += '\n'.join(random.sample(string.ascii_lowercase, N)) + '\n'
        M = random.randint(100, 200)
        data += str(M) + "\n"
        data += '\n'.join(make_word() for i in range(M)) + '\n'
        return data, ""

    @staticmethod
    def solve(data):
        datum = data.split()
        N = int(datum[0])
        disallowed_letters = set(datum[1:N+1])
        words = datum[N+2:]
        return '\n'.join(w for w in words if len(set(w).intersection(disallowed_letters)) == 0)
    
    @staticmethod
    def verify(data, seed, output):
        answer = viking_olympics.solve(data)
        if output.strip() == answer.strip():
            return 100
        else:
            return 0
