# coding=utf-8
# Input generators.
import random

# The "YOLO" problem. Generates nonsensical Japanese.
def yolo():
    hiragana = u'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
    crap = ''.join(random.choice(hiragana) for i in range(random.randint(40, 60)))
    return crap

# The "split sum" problem. Generates 100 space-separated integers. Requires the sum.
def splitsum():
    return ' '.join(map(str, [random.randint(1000, 99999) for i in range(100)]))
