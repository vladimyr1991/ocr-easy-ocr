import easyocr
import pdf2image
import cv2
import numpy as np
import pprint
import os
import json
from supportive_methods import preprocessing_image
from PIL import Image, ImageFont, ImageDraw


pp = pprint.PrettyPrinter(width=200, compact=True)
reader = easyocr.Reader(['ru','en'], gpu=False, quantize=False)
path = "."

if __name__ == "__main__":

    documents = os.listdir("./input_data")

    for document in documents:

        document_images = pdf2image.convert_from_path(f'./input_data/{document}', fmt="tiff")

        for num, image in enumerate(document_images):

            # image = preprocessing_image(image)
            image = np.array(image)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            recognition = reader.readtext(image)

            for result in recognition:

                top_left = tuple(result[0][0])
                bottom_right = tuple(result[0][2])
                text = result[1]

                top_left_x = result[0][0][0]
                top_left_y = result[0][0][1]
                bottom_right_x = result[0][2][0]
                bottom_right_y = result[0][2][1]

                width = bottom_right_x - top_left_x
                height = bottom_right_y - top_left_y

                resulting_json = {
                    "left": str(top_left_x),
                    "top": str(top_left_y),
                    "length": str(length),
                    "height": str(height),
                    "text": text
                    }

                font = cv2.FONT_HERSHEY_SIMPLEX

                image = cv2.rectangle(image, (top_left_x, top_left_y), (top_left_x+length, top_left_y+height), (0, 255, 0), 3)

                # pil_image = Image.fromarray(image)
                # draw = ImageDraw.Draw(pil_image)
                # kbd = ImageFont.truetype("~/Library/Fonts/DejaVuSerif.ttf", 30, encoding="unic")
                # draw.text((top_left[0], bottom_right[1]), text, font=kbd, fill=(0, 0, 255))
                # image = np.array(pil_image)
                cv2.imwrite(f"./output_data/{document.split('.')[0]}_page_{str(num)}.jpg", image)

                with open("./output_data/test.json", "w") as f:
                    json.dump(resulting_json, f)