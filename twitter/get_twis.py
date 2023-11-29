import re
import PyPDF2
from playwright.sync_api import sync_playwright
from reportlab.pdfgen import canvas
import os
import time
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.platypus import Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 最近lastN条推文
lastN = 5

# 被爬取的用户id
twitter_ids = ['billjian24','Web3Tinkle','V1JeromeLoo']

twis = []

# 指定中文字体文件的路径
font_path = "font.ttf"

def filter_emojis(text):
    # 使用正则表达式匹配Unicode表情符号
    emoji_pattern = re.compile(r'[\U00010000-\U0010FFFF]|[\uD800-\uDBFF][\uDC00-\uDFFF]', flags=re.UNICODE)
    
    # 使用空字符串替换匹配到的表情符号
    text_without_emojis = emoji_pattern.sub('', text)
    
    return text_without_emojis

def cutPhotoUrl(text):
    # 使用正则表达式匹配 URL 链接
    urls = re.findall(r'https://t\.co/\w+', text)

    # 替换 URL 链接为空字符串
    for url in urls:
        text = text.replace(url, '')
    return text

def intercept_response(response):
    global twis
    # we can extract details from background requests

    if response.request.resource_type == "xhr" and 'UserTweets' in response.url:
        data = response.json()
        print('response:',response.url)
        
        # 使用正则表达式提取匹配的文本
        pattern = r'"full_text":"(.*?)","is_quote_status"'
        matches = re.findall(pattern, response.text())
        c = 0
        # 打印所有匹配的内容
        for match in matches:
            twis.append(filter_emojis(cutPhotoUrl(match)))
            c = c + 1
            if c >= lastN:
                break

        # print(response.text())
    return response


def writeToPdf():
    # 注册中文字体
    pdfmetrics.registerFont(TTFont("ChineseFont", font_path))

    # 创建一个PDF文档
    doc = SimpleDocTemplate("dailyTwi.pdf", pagesize=letter)


    # 创建一个样式表
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "ChineseFont"  # 使用自定义字体

    # 创建一个Story，用于存放所有要添加到PDF中的元素
    story = []

    # 遍历字符串列表，将每行文本添加到Story中
    for item in twis:
        paragraph = Paragraph(item, styles["Normal"])
        story.append(paragraph)
        story.append(Spacer(1, 12))  # 添加一个间距，分隔每行文本

    # 将Story添加到PDF文档中
    doc.build(story)
    

    
def generateWordCloud():
    # 每个元素之间插入换行符
    text = "\n".join(twis)

    # 创建词云
    wordcloud = WordCloud(width=1500, height=1200, background_color="white", font_path=font_path).generate(text)

    # 保存词云为图片
    wordcloud.to_file("wordcloud.png")


    # 创建一个 PDF 页面对象
    c = canvas.Canvas("modified.pdf", pagesize=letter)

    # 插入图片
    image = ImageReader("wordcloud.png")  # 图片文件的路径
    c.drawImage(image, 200, 200, width=400, height=400)  # 调整坐标和大小

    # 保存 PDF 文件
    c.save()

    # 合并现有的 PDF 和新生成的 PDF
    from PyPDF2 import PdfReader, PdfWriter

    existing_pdf = PdfReader(open("dailyTwi.pdf", "rb"))
    new_pdf = PdfReader(open("modified.pdf", "rb"))
    output_pdf = PdfWriter()

    # 添加新生成的 PDF 页
    for page_num in range(len(new_pdf.pages)):
        page = new_pdf.pages[page_num]
        output_pdf.add_page(page)
    # 添加现有的 PDF 页
    for page_num in range(len(existing_pdf.pages)):
        page = existing_pdf.pages[page_num]
        output_pdf.add_page(page)

    # 保存合并后的 PDF
    with open("final.pdf", "wb") as output_stream:
        output_pdf.write(output_stream)

    # 删除临时文件
    os.remove("dailyTwi.pdf")
    os.remove("modified.pdf")
    os.remove("wordcloud.png")


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.on("response", intercept_response)
        for twitter_id in twitter_ids:
            page.goto(f'https://twitter.com/{twitter_id}')
            page.wait_for_load_state('networkidle')

        browser.close()
    

    for twi in twis:
        print(twi)

    writeToPdf()

    generateWordCloud()

def repeat_until_no_error():
    global twis
    while True:
        try:
            run()
            print("函数执行成功！")
            break  # 执行成功后退出循环
        except Exception as e:
            print(f"函数执行时发生异常: {str(e)}")
            print("稍后重试...")
            twis = []
            time.sleep(1)  # 等待一段时间后重试

repeat_until_no_error()