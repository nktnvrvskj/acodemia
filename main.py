import numpy as np
s = eval(input("ведите 1 вектор в виде [x,y,z] : "))
d = eval(input("ведите 2 вектор в виде [x,y,z] : "))

def chec(array):
    if len(array) == 3:
        return array
    print("неправельно вектор использовани стандартная [1,2,3]")
    return [1, 2, 3]

def calc(array1, array2):
    print(array1, array2)
    a = np.array(array1)
    b = np.array(array2)

    print(a+b)
    print(a @ b)
    print(np.cross(a,b))

    cos = a @ b /(np.linalg.norm(a)*np.linalg.norm(b))
    print(cos)

calc(chec(s),chec(d))