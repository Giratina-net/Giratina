# 画像処理に用いる数値計算関数
import random

# 最小値を設定
def minlim(val, min):
    if val < min:
        return min
    else:
        return val


# 最大値を設定
def maxlim(val, max):
    if val > max:
        return max
    else:
        return val


# 最小値、最大値を設定
def minmaxlim(val, min, max):
    if val < min:
        return min
    elif val > max:
        return max
    else:
        return val


# 数値のミラーループ
def roop(num, min, max):
    range = max - min
    n = (num - min) // range
    val = (num - min) % range
    result = 0
    if n % 2 == 0:
        result = min + val
    else:
        result = max - val
    return result


# 矩形
class Rect:
    left = 0
    top = 0
    right = 0
    bottom = 0
    width = 0
    height = 0
    size = 0

    def __init__(self, left, top, right, bottom):
        self.left = min(left, right)
        self.top = min(top, bottom)
        self.right = max(left, right)
        self.bottom = max(top, bottom)

        self.width = abs(right - left)
        self.height = abs(bottom - top)

        self.size = (self.width, self.height)


# 領域(矩形の集合)
class Region:
    rects = []
    def __init__(self, rects):
        self.rects = rects

    def add_rect(self, rect):
        self.rects.append(rect)

    def randompos(self):
        weights = [r.width * r.height for r in self.rects]
        rect_choice = random.choices(self.rects, weights=weights)[0]
        result_x = random.randint(rect_choice.left, rect_choice.right)
        result_y = random.randint(rect_choice.top, rect_choice.bottom)
        return (result_x, result_y)
