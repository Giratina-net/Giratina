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
