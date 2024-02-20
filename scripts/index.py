from refactored import get_embeddings_by_chunks
import processing as p
import pandas as pd

def main():
    product_json = p.process_item('VKORN SONNENBATZ')
    print(product_json)

if __name__=='__main__':
    main()