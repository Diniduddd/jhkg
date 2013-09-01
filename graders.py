# Graders.
# They each take 2 args. First is input, second is received output.
# Return True iff the user gave us the right output.

# The "YOLO" grader. Any answer is right because YOLO.
def yolo(data, output):
    return 100

# The "split sum" grader. Sums the space-separated integers.
def splitsum(data, output):
    if str(sum(map(int, data.split()))) == output:
        return 100
    else:
        return 0
