# %% [markdown]
# # Prompt engineering
# 
# - Create prompt w/
#     - Role
#     - Set categories to classify
#     - Few-Shot-Examples
#     - Task
#     - Input for items to classify

# %%
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

#import pandas as pd
import json

import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('MISTRAL_API_KEY')


# %%
def run_mistral(user_message, model="mistral-medium"):
    client = MistralClient(api_key=api_key)
    messages = [
        ChatMessage(role="user", content=user_message)
    ]
    chat_response = client.chat(
        model=model,
        messages=messages,
        temperature=0.5, # default 0.7, lower is more deterministic
        random_seed=42
    )
    return (chat_response, chat_response.choices[0].message.content)


# %%
def get_rewe_categories():
    """Format the main and subcategories found on the Rewe website for the prompt.
    Each product can be classified with one category. To avoid overlaps, some labels like vegan are excluded.
    Returns:
        STR: Formatted categories
    """
    
    # Import product categories as dict w/ key: main category, value: list of subcategories
    with open('../data/categories_rewe.json') as f:
        categories_rewe = json.load(f)

    # Remove certain categories because they are actually labels
    exclude_categories = ['Vegane Vielfalt', 'International', 'Regional']

    for cat in exclude_categories:
        categories_rewe.pop(cat, None)

    # Include new categories needed for items that are not products
    categories_rewe['Sonstige Positionen'] = ['Pfand & Leergut', 'Rabatt & Ermäßigung', 'Kategorie nicht erkannt']

    # String categories together in a formatted string to insert in the prompt
    categories_string = list()
    for main_category in categories_rewe:
        subs_string = '## Unterkategorien\n' + '\n'.join(categories_rewe[main_category])
        categories_string.append(f'# Hauptkategorie\n{main_category}\n{subs_string}\n')
    categories_string = '\n'.join(categories_string)

    return categories_string

# %%
def get_prompt(item, categories):
    prompt = (
        f"""
Du bist ein Experte für das Erkennen und Kategorisieren von verkürzten Produktnamen auf Supermarkt-Kassenbons.

Deine Aufgabe ist die folgende:
1. Löse den verkürzten Produktnamen in den Klammern <<< >>> zum vollständigen Produktnamen auf.
2. Ordne das Produkt der Hauptkategorien und der dazugehörige Unterkategorie zu, die das Produkt am besten klassifiziert.

Die möglichen Kategorien sind:

{categories}

Du wirst IN JEDEM FALL nur aus den vordefinierten Kategorien wählen. Deine Antwort enthält keine Erklärungen oder Anmerkungen. Die Antwort muss in valid JSON formatiert sein.

###
Hier sind einige Beispiele:

Verkürzter Produktname: HAUCHSCHN CURRY
Antwort: productName: Rügenwalder Mühle Veganer Hauchschnitt Typ Hähnchen, categoryMain: Fleisch & Fisch, categorySub: Fleischalternativen

Verkürzter Produktname: GRANATAPEL
Antwort: productName: Granatapfel, category_main: Obst & Gemüse, categorySub: Frisches Obst

Verkürzter Produktname: KASTEN LEER
Antwort: productName: Leergut Kasten, categoryMain: Sonstige Positionen, categorySub: Pfand & Leergut
###

<<<
Verkürzter Produktname: {item}
>>>
"""
    )
    return prompt

# %%
def process_abbreviation(item):
    """Completes the shortened item to full product name and categorizes it in a main and sub-category

    Args:
        item (STR): The product name as it is on the receipt.

    Returns:
        JSON: Full product name, main category, subcategory, input item string
    """
    # Get the needed information for the request
    categories_rewe = get_rewe_categories()
    prompt = get_prompt(item, categories=categories_rewe)

    # Request response from Mixtral
    try:
        print(f'Requesting Mixtral for {item}…')
        response, message = run_mistral(prompt)
        print('Received response')
    except:
        print('\n\n⚠️⚠️⚠️\n\nError requesting response from Mixtral!\n\nAPI response:')
        print(response)

    # Parse message string to json
    try:
        item_json = json.loads(message)
        item_json['product_abbr'] = item
        print(f"Parses response successfully, {item_json['productName']}")
    except:
        print('\n\n⚠️⚠️⚠️\n\Error parsing Mixtral message, not formatted correctly as JSON!\n\nMessage:')
        print(message)
    
    return item_json


# %%
#item_json = process_abbreviation('SKYR STYLE VAN.')


