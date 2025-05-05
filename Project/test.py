import threading
import time
print("hi")


def delay():
    time.sleep(20)
    print("I'M STILL HERE!")

thd = threading.Thread(target=delay,args=(),daemon=True)

thd.start()
print("a")
print("b")




