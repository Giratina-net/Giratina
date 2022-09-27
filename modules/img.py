from PIL import Image, ImageFont, ImageDraw
import random

class Giratina_Image:
    image = 0

    def load(self, path):
        self.image = Image.open(path)

    def write(self, path):
        self.image.save(path)
        
    # テキストを追加
    def drawtext(self, text, pos, fill='white', anchor='mm', fontpath='.fonts/meiryo.ttf' , fontsize=24, direction='rtl', stroke_width=0, stroke_fill='black'):
        font = ImageFont.truetype(fontpath, fontsize)

        draw = ImageDraw.Draw(self.image)
        draw.text(pos, text, fill=fill, font=font, anchor=anchor, direction=direction, stroke_width=stroke_width, stroke_fill=stroke_fill)

    # コンポジット(透過画像対応)
    def composit(self, img, position):
        bg_clear = Image.new("RGBA", self.image.size, (255, 255, 255, 0))
        bg_clear.paste(img, position)
        self.image = Image.alpha_composite(self.image, bg_clear)


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