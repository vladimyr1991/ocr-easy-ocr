import os
import pdf2image
from pdf2image import convert_from_path
# import pytesseract
import cv2
from argparse import ArgumentParser
import numpy as np

import json


parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="filename",
                    help="route to pdf FILE")

args = parser.parse_args()


def rotate(img, angle, background=(255, 255, 255)):
    """
    Rotate image. Angle is measured in degrees.
    """

    h, w = img.shape[:2]
    cX, cY = w // 2, h // 2

    mat = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
    return cv2.warpAffine(
        img, mat, (w, h),
        borderValue=background
    )


def ocr_core(image, page_num):

    # extracting metadata with recognized text from image
    boxes = pytesseract.image_to_data(image, lang='eng+rus')
    texts = boxes.splitlines()

    words_on_page = []

    for i, t in enumerate(texts):
        if i != 0:
            meta = t.split()
            if len(meta) == 12:
                word_meta = {
                    "value": meta[11],
                    "page": page_num,
                    "top": meta[7],
                    "left": meta[6],
                    "other": t
                    }
                words_on_page.append(word_meta)

    return words_on_page

# # for pytesseract
# def ocr_core(image, page_num):
#
#     # extracting metadata with recognized text from image
#     boxes = pytesseract.image_to_data(image, lang='eng+rus')
#     texts = boxes.splitlines()
#
#     words_on_page = []
#
#     for i, t in enumerate(texts):
#         if i != 0:
#             meta = t.split()
#             if len(meta) == 12:
#                 word_meta = {
#                     "value": meta[11],
#                     "page": page_num,
#                     "top": meta[7],
#                     "left": meta[6],
#                     "other": t
#                     }
#                 words_on_page.append(word_meta)

    return words_on_page

def extract_text(guid):

    input_folder = "./input_data"

    # converting pdf to images
    images = convert_from_path(pdf_path=os.path.join(input_folder, f"{guid}.pdf"), dpi=500)

    result = []

    for page_num, image in enumerate(images):
        output = ocr_core(image=image, page_num=page_num + 1)
        result = result + output

    # saving json with results
    with open(f'./output_data/{guid}.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)


def extract_text_from_bytes(pdf_bytes):

    # converting pdf to images
    images = pdf2image.convert_from_bytes(pdf_bytes)

    result = []

    for page_num, image in enumerate(images):
        # replacing noise from image
        image = preprocessing_image(image)
        # extracting text from image
        output = ocr_core(image=image, page_num=page_num + 1)
        # accumulating recognition
        result = result + output

    return result


def preprocessing_image(img):

    """
    :param img: image RGB as an array
    :return: preprocessed black and white image
    """
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # making image gray

    low_threshold = 1
    high_threshold = 100
    edges = cv2.Canny(gray, low_threshold, high_threshold)

    rho = 1 # distance resolution in pixels of the Hough grid
    theta = np.pi / 180  # angular resolution in radians of the Hough grid
    threshold = 1000  # minimum number of votes (intersections in Hough grid cell)
    min_line_length = 500 # minimum number of pixels making up a line
    max_line_gap = 500 # maximum gap in pixels between connectable line segments
    line_image = np.copy(img) * 0  # creating a blank to draw lines on

    # Run Hough on edge detected image
    # Output "lines" is an array containing endpoints of detected line segments
    lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]), min_line_length, max_line_gap)

    for line in lines:
        for x1, y1, x2, y2 in line:
            cv2.line(line_image, (x1, y1), (x2, y2), (255, 255, 255), 2)

    # Draw the lines on the  image
    lines_edges = cv2.addWeighted(img, 0.8, line_image, 1, 0)
    gray = cv2.cvtColor(lines_edges, cv2.COLOR_BGR2GRAY)

    thresh = 10
    (thresh, bw) = cv2.threshold(gray, thresh, 255, cv2.THRESH_OTSU)

    return bw
