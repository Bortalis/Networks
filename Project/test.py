import threading
import time
print("hi")
x = threading.Event()
def delay():
    print("1")
    print("1")
    print("1")
    time.sleep(1)
    print("1")
    print("1")
    print("1")
    time.sleep(1)
    print("1")
    print("1")
    print("1")

thd = threading.Thread(target=delay,args=())
thd.start()
print("a")
a = input("type here: ")
print("b")




