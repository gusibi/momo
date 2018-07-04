#! -*- coding: utf-8 -*-

"""
1. 将文字写入到 note_body.png
2. 将 note_header.png 拼接到 note_body.png 上边
3. 将 note_footer.png 拼接到 note_body.png 后边
"""
import time
from os import path

from PIL import Image, ImageDraw, ImageFont

from momo.settings import Config

otf = Config.NOTE_OTF
font = ImageFont.truetype(otf, 24)


class Note:

    def __init__(self, text, filename, header=None, body=None, footer=None,
                 header_height=None, footer_height=None,
                 body_wh=None, note_width=None, line_padding=10):
        self.text = text
        self.header = header
        self.body = body
        self.footer = footer
        self.note_width = note_width
        self.line_padding = line_padding  # 行高 padding
        self.header_height = header_height
        self.footer_height = footer_height
        self.body_width, self.body_height = body_wh
        self.paragraphs, self.note_height, self.line_height = self.split_text()
        self.filename = '/tmp/%s' % filename
        self.background_img = None

    def get_paragraph(self, text):
        txt = Image.new('RGBA', (100, 100), (255, 255, 255, 0))
        # get a drawing context
        draw = ImageDraw.Draw(txt)
        paragraph, sum_width = '', 0
        line_numbers, line_height = 1, 0
        for char in text:
            w, h = draw.textsize(char, font)
            sum_width += w
            if sum_width > self.note_width:
                line_numbers += 1
                sum_width = 0
                paragraph += '\n'
            paragraph += char
            line_height = max(h, line_height)
        if not paragraph.endswith('\n'):
            paragraph += '\n'
        return paragraph, line_height, line_numbers

    def split_text(self):
        # 将文本按规定宽度分组
        max_line_height, total_lines = 0, 0
        paragraphs = []
        for t in self.text.split('\n'):
            paragraph, line_height, line_numbers = self.get_paragraph(t)
            max_line_height = max(line_height, max_line_height)
            total_lines += line_numbers
            paragraphs.append((paragraph, line_numbers))
        line_height = max_line_height + self.line_padding # 行高多一点
        total_height = total_lines * line_height
        return paragraphs, total_height, line_height

    def draw_text(self):
        background_img = self.make_backgroud()
        note_img = Image.open(background_img).convert("RGBA")
        draw = ImageDraw.Draw(note_img)
        # 文字开始位置
        x, y = 80, 100
        for paragraph, line_numbers in self.paragraphs:
            for line in paragraph.split('\n')[:-1]:
                draw.text((x, y), line, fill=(110, 99, 87), font=font)
                y += self.line_height
            # draw.text((x, y), paragraph, fill=(110, 99, 87), font=font)
            # y += self.line_height * line_numbers
        note_img.save(self.filename, "png", quality=1, optimize=True)
        return self.filename

    def get_images(self):
        numbers = self.note_height // self.body_height + 1
        images = [(self.header, self.header_height)]
        images.extend([(self.body, self.body_height)] * numbers)
        images.append((self.footer, self.footer_height))
        return images

    def make_backgroud(self):
        # 将图片拼接到一起
        images = self.get_images()
        total_height = sum([height for _, height in images])
        # 最终拼接完成后的图片
        backgroud = Image.new('RGB', (self.body_width, total_height))
        left, right = 0, 0
        background_img = '/tmp/%s_backgroud.png' % total_height
        # 判断背景图是否存在
        if path.exists(background_img):
            return background_img
        for image_file, height in images:
            image = Image.open(image_file)
            # (0, left, self.body_width, right+height)
            # 分别为 左上角坐标 0, left
            # 右下角坐标 self.body_width, right+height
            backgroud.paste(image, (0, left, self.body_width, right+height))
            left += height  # 从上往下拼接，左上角的纵坐标递增
            right += height  # 左下角的纵坐标也递增
        backgroud.save(background_img, quality=85)
        self.background_img = background_img
        return background_img


note_img_config = {
    'header': Config.NOTE_HEADER_IMG,
    'body': Config.NOTE_BODY_IMG,
    'footer': Config.NOTE_FOOTER_IMG,
    'header_height': Config.NOTE_HEADER_HEIGHT,
    'footer_height': Config.NOTE_FOOTER_HEIGHT,
    'body_wh': (Config.NOTE_WIDTH, Config.NOTE_BODY_HEIGHT),
    'note_width': Config.NOTE_TEXT_WIDTH,
}
print(note_img_config)
