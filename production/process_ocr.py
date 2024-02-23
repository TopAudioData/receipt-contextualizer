'''
recognized text blocks of the receipt with Google Vision
takes an image variable (----and a filename----)
returns as dataframe with productnames and prices (----per filename----)
'''


# import libraries
import os
from dotenv import load_dotenv
import pandas as pd
from os.path import join
from datetime import datetime

load_dotenv()
SA_KEY=os.getenv("GOOGLE_SA_KEY")
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SA_KEY



# Googles OCR function for text recoginition
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



# Main function that uses the detect_text() function and recreates the rows
# on the receipt from the individual bounding boxes (detect_text() finds single
# words and the corresponding bounding boxes, but is unable to recognize the lines/rows
#of a receipt)
def process_receipt(path,filename):
    '''
    This function takes an image as input and creates a dataframe that contains
    information about the product names and the amount of money that was spent
    on the products. 

    path - directory where the receipt is located
    filename - filename of the receipt
    '''
    # Apply function to an receipt
    response = detect_text(join(path,filename))

    # The text_annotations contain the recognized text and the corresponding bounding boxes
    # the first entry contains the whole text from the receipt and the consecutive entries
    # contain the text/coordinates from the individual bounding boxes
    texts = response.text_annotations

    # Build dataframe, where bl: bottom_left, br: bottom_right, tr: top_right, tl: top_left
    # denote the corners of the BBs
    columns = ["String", "x_bl", "y_bl", "x_br", "y_br","x_tr","y_tr","x_tl","y_tl"] # uncomment if you need x coords as well
    #columns = ["String", "y_bl", "y_br","y_tr","y_tl"]
    df = pd.DataFrame(columns=columns)

    for i, text in enumerate(texts[1:]):
        df.loc[i, "String"] = text.description
        for j in range(4):
            df.iloc[i,2*j+1] = text.bounding_poly.vertices[j].x  # uncomment if you need x coords as well 
            #df.iloc[i,j+1] = text.bounding_poly.vertices[j].y
            df.iloc[i,2*j+2] = text.bounding_poly.vertices[j].y  # uncomment if you need x coords as well

    # convert the coords to integers for calculation of the mean BB positions
    df[['y_bl','y_br','y_tr','y_tl']] = df[['y_bl','y_br','y_tr','y_tl']].astype('int')
    # calulate mean BB positions
    df['mean_y'] = df.eval('(y_bl+y_br+y_tr+y_tl)/4')

    # sort DF by mean height to match text that appears in the same line
    df = df.sort_values(by=['mean_y']).reset_index(drop=True)

    # select only the block of the receipt where the products are listed
    product_list_start_ind = int(df[df.String== 'EUR'].index.values[0])+1
    product_list_end_ind = int(df[df.String=='SUMME'].index.values)

    df_products = df[product_list_start_ind:product_list_end_ind]

    # Create empty list and dataframe to fill it later on
    shown_indices = []
    columns = ['product_abbr','price']
    df_cleaned = pd.DataFrame(columns=columns)
    counter = 1 # used to build the cleaned data frame row by row

    # check if consecutive rows in df_products belong to the same line in the receipt
    for i in df_products['mean_y']:
        condition = (df_products['mean_y'] >= i) & (df_products['mean_y'] < i + 10)
        indices = df_products.index[condition] # store the indices that fulfill the condition
        
        # check if the indices have been shown before
        if not any(idx in shown_indices for idx in indices):
            # only keep lines that end with A,B or * and write product_abbr's and prices into df_cleaned
            chars = ['A','B','*']
            selected = df_products.loc[indices].sort_values(by=['x_bl'])['String']
            if selected.iloc[-1] in chars:
                if selected.iloc[-1] == '*':
                    df_cleaned.loc[counter,'product_abbr'] = ' '.join(selected.iloc[:-3])
                    df_cleaned.loc[counter,'price'] = selected.iloc[-3].replace(',','.')
                else:
                    df_cleaned.loc[counter,'product_abbr'] = ' '.join(selected.iloc[:-2])
                    df_cleaned.loc[counter,'price'] = selected.iloc[-2].replace(',','.')
                counter += 1
            shown_indices.extend(indices)

    # convert the price column to floats
    df_cleaned.price = df_cleaned.price.astype('float')
    df_cleaned['receipt_id'] = filename
    df_cleaned['processing_date'] = datetime.today().strftime('%d-%m-%Y')

    return df_cleaned