# import libraries
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from os import listdir
from os.path import join
from natsort import natsorted # needed for sorting filenames of the receipts

SA_KEY=os.getenv("GOOGLE_SA_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SA_KEY



# Googles OCR function
def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    '''
    # commented out to supress printed output of the function
    print("Texts:")
    for text in texts:
        print(f'\n"{text.description}"')

        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]

        print("bounds: {}".format(",".join(vertices)))
    '''
    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
            )
    return response


def process_receipts(path, filename):
    '''
    This function takes an image as input and creates a dataframe that contains
    information about the product names and the amount of money that was spent
    on the products. 
    '''
    # Apply function to a receipt
    response = detect_text(os.path.join(path, filename))

    # The text_annotations contain the recognized text and the corresponding bounding boxes
    # the first entry contains the whole text from the receipt and the consecutive entries
    # contain the text/coordinates from the individual bounding boxes
    texts = response.text_annotations

    # Build dataframe, where bl: bottom_left, br: bottom_right, tr: top_right, tl: top_left
    # denote the corners of the BBs
    columns = ["String", "x_bl", "y_bl", "x_br", "y_br","x_tr","y_tr","x_tl","y_tl"]
    df = pd.DataFrame(columns=columns)

    for i, text in enumerate(texts[1:]):
        df.loc[i, "String"] = text.description
        for j in range(4):
            df.iloc[i,2*j+1] = text.bounding_poly.vertices[j].x
            df.iloc[i,2*j+2] = text.bounding_poly.vertices[j].y

    # convert the coords to integers for calculation of the mean BB positions
    df[['y_bl','y_br','y_tr','y_tl']] = df[['y_bl','y_br','y_tr','y_tl']].astype('int')
    # calculate mean BB positions
    df['mean_y'] = df.eval('(y_bl+y_br+y_tr+y_tl)/4')

    # sort DF by mean height to match text that appears in the same line
    df = df.sort_values(by=['mean_y']).reset_index(drop=True)

    # calculate the letter hight to separate lines
    df['letter_height'] = df.eval('(y_bl-y_tr)+(y_tl-y_br)/2')

    # select only the block of the receipt where the products are listed
    if 'EUR' in df.String.values:
        product_list_start_ind = int(df[df.String== 'EUR'].index.values[0])+1
    else:
        raise ValueError("'EUR' not found in the receipt")

    if 'SUMME' in df.String.values:
        product_list_end_ind = int(df[df.String=='SUMME'].index.values)
    elif 'SUM' in df.String.values:
        product_list_end_ind = int(df[df.String=='SUM'].index.values)
    else:
        raise ValueError("'SUMME' or 'SUM' not found in the receipt")

    df_products = df[product_list_start_ind:product_list_end_ind]

    # Create empty list and dataframe to fill it later on
    shown_indices = []
    columns = ['product_name','price']
    df_cleaned = pd.DataFrame(columns=columns)
    counter = 1 # used to build the cleaned data frame row by row

    # check if consecutive rows in df_products belong to the same line in the receipt
    for i in df_products['mean_y']:
        threshold = 0.1 * df_products['letter_height'].mean()
        condition = (df_products['mean_y'] >= i) & (df_products['mean_y'] < (i + threshold))
        indices = df_products.index[condition] # store the indices that fulfill the condition
        
        # check if the indices have been shown before
        if not any(idx in shown_indices for idx in indices):
            # only keep lines that end with A,B or * and write product_names and prices into df_cleaned
            chars = ['A','B','*']
            selected = df_products.loc[indices].sort_values(by=['x_bl'])['String']
            if selected.iloc[-1] in chars:
                if selected.iloc[-1] == '*':
                    df_cleaned.loc[counter,'product_name'] = ' '.join(selected.iloc[:-3])
                    df_cleaned.loc[counter,'price'] = selected.iloc[-3].replace(',','.')
                else:
                    df_cleaned.loc[counter,'product_name'] = ' '.join(selected.iloc[:-2])
                    df_cleaned.loc[counter,'price'] = selected.iloc[-2].replace(',','.')
                counter += 1
            shown_indices.extend(indices)

    # convert the price column to floats
    df_cleaned.price = df_cleaned.price.astype('float')
    df_cleaned['receipt_id'] = filename

    return df_cleaned



# find all receipts in the specified path and sort them in ascending order
path = '../rewe_scanned/Rewe_Bons_Scans_ToP/'
files = natsorted(listdir(path))
#files.pop(0) # remove DSstore file
files

df_list = []

for file in files:
    df = process_receipts(path,file)
    df_list.append(df)

df_all = pd.concat(df_list,ignore_index=True)

pd.set_option('display.max_rows', None)
df_all

# Clean the rows that were misinterpreted manually
df_all.product_name[15] = 'Rabatt 30 %'
df_all.price[15] = -0.6

df_all.product_name[23] = 'RUCOLA'
df_all.price[23] = 1.19

df_all.product_name[28] = 'BIO EIER OKT'
df_all.price[28] = 3.19

df_all.product_name[73] = 'RBW APFELESSIG'
df_all.price[73] = 5.16

df_all.product_name[107] = 'PFAND 3,10 EUR'
df_all.price[107] = 3.10

df_all.product_name[118] = 'GRIE. PFEFFERON.'
df_all.price[118] = 2.18

df_all.product_name[119] = 'CURLY WURLY'
df_all.price[119] = 1.77

df_all.product_name[149] = 'PFAND 0,25 EURO'
df_all.price[149] = 0.25

df_all.product_name[186] = 'EIER BH M-L'
df_all.price[186] = 1.99

df_all.product_name[192] = 'TOM KHA GAI'
df_all.price[192] = 1.19

df_all.product_name[206] = 'BACK. -GRILLREIN.'
df_all.price[206] = 3.49

df_all.product_name[210] = 'CASHEWKERNE'
df_all.price[210] = 2.19

df_all.product_name[211] = 'AMAZONMULTI30'
df_all.price[211] = 30.00

df_all.product_name[220] = 'PFAND'
df_all.price[211] = 0.75

df_all.to_csv('../data/scanned_rewe_receipts_ToP_cleaned.csv')