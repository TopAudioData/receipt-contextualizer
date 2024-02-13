def get_embeddings_by_chunks(data, chunk_size, api_key):
    '''
    Returns embeddings for data as a list of arrays.
    '''

    from mistralai.client import MistralClient
    from ast import literal_eval

    client = MistralClient(api_key)

    chunks = [data[x : x + chunk_size] for x in range(0, len(data), chunk_size)]
    embeddings_response = [
        client.embeddings(model="mistral-embed", input=c) for c in chunks
    ]
    return [literal_eval(d.embedding) for e in embeddings_response for d in e.data]