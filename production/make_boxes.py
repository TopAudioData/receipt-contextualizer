'''
Make bounding boxes around recognized text blocks of the receipt
'''

# Import libraries and Google Vison Key
import argparse
from enum import Enum
from PIL import Image, ImageDraw
import io
import os
from dotenv import load_dotenv
from google.cloud import vision

# set path of the skript as currrent path
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# path .env file if skript is in subfolder
env_path = '../.env'
# check if path is valid / .env is a file
if os.path.isfile(env_path):
    # load .env file
    load_dotenv(dotenv_path=env_path)
else: # if path is not vaild / -env is not a file
    env_path = './.env' # try if skript is in main path of the repository
    # check if path is now valid / .env is a file
    if os.path.isfile(env_path):
         # load .env file
        load_dotenv(dotenv_path=env_path)
    else: # if both paths don't work
        print(".env file not found")
# get path to SA_key from .env-file
sa_key_path = os.getenv("GOOGLE_SA_KEY")
# Check if path to SA_key is valid
if os.path.isfile(sa_key_path):
    # use the SA_key if path is valid
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_path
else:
    sa_key_path = sa_key_path[1:]
    # Check if path to SA_key is valid
    if os.path.isfile(sa_key_path):
        # use the SA_key if path is valid
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_path
    else: # if both paths don't work
        print(" SA_key file not found")


# define features to be detected by Google Vision
class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5

def draw_boxes(image, bounds, color):
    """Draws a border around the image using the hints in the vector list.

    Args:
        image: the input image object.
        bounds: list of coordinates for the boxes.
        color: the color of the box.

    Returns:
        An image with colored bounds added.
    """
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon(
            [
                bound.vertices[0].x,
                bound.vertices[0].y,
                bound.vertices[1].x,
                bound.vertices[1].y,
                bound.vertices[2].x,
                bound.vertices[2].y,
                bound.vertices[3].x,
                bound.vertices[3].y,
            ],
            None,
            color, width=3
        )
    return image

#def get_document_bounds(image_file, feature):
def get_document_bounds(image_input, feature):

    """Finds the document bounds given an image and feature type.

    Args:
        image_file: path to the image file.
        feature: feature type to detect.

    Returns:
        List of coordinates for the corresponding feature type.
    """
    client = vision.ImageAnnotatorClient()

    bounds = []

    #with open(image_file, "rb") as image_file:
    #    content = image_file.read()
    byte_arr = io.BytesIO()
    image_input.save(byte_arr, format='JPEG') #TODO: test if it works with *.png
    byte_arr = byte_arr.getvalue()

    content = byte_arr

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    # Collect specified feature bounds by enumerating all document features
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        if feature == FeatureType.SYMBOL:
                            bounds.append(symbol.bounding_box)

                    if feature == FeatureType.WORD:
                        bounds.append(word.bounding_box)

                if feature == FeatureType.PARA:
                    bounds.append(paragraph.bounding_box)

            if feature == FeatureType.BLOCK:
                bounds.append(block.bounding_box)

    # The list `bounds` contains the coordinates of the bounding boxes.
    return bounds

#def render_doc_text(filein, fileout):
def render_doc_text(image_in):
    """Outlines document features (blocks, paragraphs and words) given an image.

    Args:
        filein: path to the input image.
        fileout: path to the output image.
    """
    #image = Image.open(filein)
    image_out = image_in.copy()  # Create a copy to draw on
    bounds = get_document_bounds(image_in, FeatureType.BLOCK)
    draw_boxes(image_out, bounds, "blue")
    bounds = get_document_bounds(image_in, FeatureType.PARA)
    draw_boxes(image_out, bounds, "yellow")
    bounds = get_document_bounds(image_in, FeatureType.WORD)
    draw_boxes(image_out, bounds, "red")

    #if fileout != 0:
     #   image.save(fileout)
    #else:
     #   image.show()
    return image_out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("detect_file", help="The image for text detection.")
    parser.add_argument("-out_file", help="Optional output file", default=0)
    args = parser.parse_args()


    image_in = Image.open(args.detect_file)  # Open the image file
    print(args.detect_file)
    fileout = args.out_file
    

    image_out = render_doc_text(image_in)

    if fileout != 0:
       image_out.save(fileout)
    else:
       image_out.show()
    

