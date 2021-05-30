import matplotlib.pyplot as plt
from math import pow

def generate(nrows, power):
    return list(map(lambda i: pow(i, power) * (1 - (i % 2) * 2), range(1, nrows)))

def saveImage(nrows, power):
    X = list(range(1,16))
    Y = generate(nrows, power)
    plt.scatter(Y, X)
    plt.savefig('scatter.png')

if __name__ == '__main__':
    saveImage(16, 2)

