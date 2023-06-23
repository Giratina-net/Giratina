from time import sleep
import math
def up_timer(input):
    try:
        global t
        input = list(map(int,input.split(":")))
        if len(input) == 2 and input[1] < 60:
            input = input[0] * 60 + input[1]
            t=math.floor(((input-1))/60)
            for i in range(0,input-1)[::-1]:
                if not t == math.floor((i+1)/60):
                    print("残り"+str(t)+"分です！")
                sleep(1)
                t=math.floor((i+1)/60)
#                print(str(t)+":"+str((i+1)%60).zfill(2))
            sleep(1)
            print("時間です！")
    except:
        return False
    
up_timer("00:05")