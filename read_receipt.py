# import libraries
import os
from os.path import join
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.signal import argrelmin, argrelmax
import re
from PIL import Image, ImageDraw
import io

# set path of the skript as currrent path
#os.chdir(os.path.dirname(os.path.abspath(__file__)))
# path .env file if skript is in subfolder
load_dotenv()

# get path to SA_key from .env-file
sa_key_path = os.getenv("GOOGLE_SA_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_path


# Googles OCR function
def detect_text(image):
    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

   # with open(image_or_path, "rb") as image_file:
    #    content = image_file.read()
    byte_arr = io.BytesIO()
    image.save(byte_arr, format='JPEG') #TODO: test if it works with *.png
    content = byte_arr.getvalue()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    
    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
            )
    return response

# function that draws the bounding boxes on the passed receipt
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


# Main function that uses the detect_text() function and recreates the rows
# on the receipt from the individual bounding boxes (detect_text() finds single
# words and the corresponding bounding boxes, but is unable to recognize the lines/rows
#of a receipt)
def process_receipt(uploaded_file):
    '''
    This function takes an image as input and creates a dataframe that contains
    information about the product names and the amount of money that was spent
    on the products. 

    path - directory where the receipt is located
    filename - filename of the receipt
    '''
    # create image instance
    image = Image.open(uploaded_file)
    # Apply function to an receipt
    response = detect_text(image)
   

    # The text_annotations contain the recognized text and the corresponding bounding boxes
    # the first entry contains the whole text from the receipt and the consecutive entries
    # contain the text/coordinates from the individual bounding boxes
    texts = response.text_annotations

    # define helper function to search for the date string in the recognized text on the receipt
    def find_date(input_string):
        # define the date pattern in the format 'TT.MM.YYYY' and include possible whitespaces
        date_pattern = r'\b\d{2}\.\s?\d{2}\.\s?\d{4}\b'
        # search for pattern in input_string
        found = re.search(date_pattern, input_string)
        # Check if date was found
        if found:
            return found.group(0)
        else:
            return "Date not found"

    # store date as string and datetime variable   
    date = find_date(texts[0].description).replace(' ','')
    date_dt = datetime.strptime(date,'%d.%m.%Y').date()

    # Build dataframe, where bl: bottom_left, br: bottom_right, tr: top_right, tl: top_left
    # denote the corners of the BBs
    columns = ["String", "x_bl", "y_bl", "x_br", "y_br","x_tr","y_tr","x_tl","y_tl"] 
    df = pd.DataFrame(columns=columns)
    bounds = []

    for i, text in enumerate(texts[1:]):
        df.loc[i, "String"] = text.description
        bounds.append(text.bounding_poly) # extract all BB coords and write them in list
        for j in range(4):
            df.iloc[i,2*j+1] = text.bounding_poly.vertices[j].x  
            df.iloc[i,2*j+2] = text.bounding_poly.vertices[j].y  

    # convert the coords to integers for calculation of the mean BB positions
    df[['y_bl','y_br','y_tr','y_tl']] = df[['y_bl','y_br','y_tr','y_tl']].astype('int')
    # calulate mean BB y positions
    df['mean_y'] = df.eval('(y_bl+y_br+y_tr+y_tl)/4')

    # sort DF by mean y position to match text that appears in the same line
    df = df.sort_values(by=['mean_y']).reset_index(drop=True)

    # select only the block of the receipt where the products are listed
    product_list_start_ind = int(df[df.String== 'EUR'].index.values[0])+1
    try:
        product_list_end_ind = int(df[df.String=='SUMME'].index.values)
    except:
        product_list_end_ind = int(df[df.String=='SUM'].index.values)

    df_products = df[product_list_start_ind:product_list_end_ind]
    df_products.reset_index(drop=True,inplace=True)

    # for matching the bounding boxes to lines on the receipt we do the following:
    # 1) the mean y position increases stepwise (resembling stairs when plotted)
    #   - calculate the approximate slope using the min and may y position values
    # 2) subtract this slope from the stepwise increasing mean y positions
    #  - in this way you get a spiky signal (when plotted), where each maximum (index) 
    #    indicates the beginning of a line and the following minimum (index) 
    #    indicates the end of a line

    x = np.linspace(1,df_products.shape[0],num=df_products.shape[0])
    slope = (max(df_products.mean_y)-min(df_products.mean_y))/df_products.shape[0] # 1)
    y_flat = df_products.mean_y - slope*x-min(df_products.mean_y) # 2)

    # for local maxima
    max_ind = argrelmax(y_flat.to_numpy())[0]
    max_ind = np.append(0,max_ind[:-1])
    # for local minima
    min_ind = argrelmin(y_flat.to_numpy())[0]

    # label the rows of the dataframe with the corresponding lines on the receipt
    df_products.loc[:, 'line'] = ''
    for i in range(len(max_ind)):
        df_products['line'].iloc[max_ind[i]:min_ind[i]+1] = i
    df_products['line'].iloc[min_ind[i]+1:df_products.shape[0]] = i+1 # make sure the last line gets labeled as well

    # sort by x-coodinates of the bounding boxes to get the text in correct order
    df_products = df_products.sort_values(by=['line','x_bl']).reset_index(drop=True)
    
    # create new dataframe containing the concatenated strings that belong to the same line on the receipt
    df_sorted = df_products.groupby('line')['String'].apply(lambda x: ' '.join(x)).reset_index()

    # sort out lines that do not contain any price information
    df_sorted = df_sorted[df_sorted['String'].str.contains(' B',case=True)|df_sorted['String'].str.contains(' A *',case=True)].reset_index(drop=True)

    # remove the tax remarks at the end of the strings
    df_sorted['String'] = df_sorted['String'].str.replace(r' B$','',regex=True)
    df_sorted['String'] = df_sorted['String'].str.replace(r' A \*$','',regex=True)
    df_sorted['String'] = df_sorted['String'].str.replace(r' A$','',regex=True)

    def extract_price(input_str):
        # Search for pattern: [whitespace][letter or percentage symbol]
        match = re.search(r' [A-Za-z%]', input_str[::-1])
        if match:
            # position of the matching pattern
            position = match.start()
            # residual string starting from the position of the matched pattern
            res_str = input_str[-position:]
        else:
            res_str = input_str

        return res_str

    # extract the prices from the strings using extract_price function defined above
    df_sorted['price'] = df_sorted['String'].apply(extract_price)
    # dirty-fix section
    df_sorted['price'] = df_sorted['price'].apply(lambda x: re.sub(f'^{re.escape("14 ")}', '',x))
    df_sorted['price'] = df_sorted['price'].apply(lambda x: re.sub(f'^{re.escape("2.0 ")}', '',x))
    df_sorted['price'] = df_sorted['price'].apply(lambda x: re.sub(f'^{re.escape("W. ")}', '',x))
    df_sorted['price'] = df_sorted['price'].apply(lambda x: re.sub(f'^{re.escape("102 ")}', '',x))

    # remove the price from the string
    def replace_str(row):
        return row['String'].replace(row['price'],'')

    df_sorted['String'] = df_sorted.apply(replace_str,axis=1)

    # formatting of the df
    df_sorted['price'] = df_sorted['price'].str.lstrip('.B')
    df_sorted['price'] = df_sorted['price'].str.replace(',','.')
    df_sorted['price'] = df_sorted['price'].str.replace(' ','')
    df_sorted['price'] = df_sorted['price'].astype('float')

    df_sorted.drop('line',axis=1,inplace=True)
    df_sorted.rename(columns={'String':'product_abbr'},inplace=True)

    # add filename and date to the df
    df_sorted['receipt_id'] = uploaded_file.name
    df_sorted['date'] = date_dt

    image_boxed = draw_boxes(image,bounds,'blue')


    return df_sorted, image_boxed