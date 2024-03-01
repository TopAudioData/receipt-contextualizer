## Setup

Unzip the data folder

```bash
unzip data.zip
```

In order to process receipts you will need a Google Cloud Vision API key and a Mistral API key
Once you have your key (stored as .json file) create a `.env` file where you store your API key like this:

```bash
touch .env
mkdir SA_key
```

Open the `.env` file and add

```bash
MISTRAL_API_KEY="<your_mistral_api_key>"
GOOGLE_SA_KEY="SA_key/<name_of_your_API_key>.json"
```
Here, `SA_key` denotes the directory where your API key is stored.
The `process_receipt.py` script will then read your `.env` file to locate the Google Cloud API key.
The `process_llm.py` script will read your Mistral API from the `.env` file.



1. Install [Docker](https://www.docker.com/get-started/)
1. Install postgresql@14 `brew install postgresql@14`
1. `cd` into this repo and enter: `docker build -t postgres .`
1. Run in terminal: 

```bash
docker run -d -e POSTGRES_USER='postgres' \
    -e POSTGRES_PASSWORD='postgres' \
    -e POSTGRES_DB='receipts' \
    -v $(pwd)/db-data:/var/lib/postgresql/data \
    -p 5432:5432 \
    --name receipts-db \
    postgres
```
### Setup

Use the requirements file in this repo to create a new environment.

```bash
pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_latest.txt
```

Run the database.py script to fill in the REWE search data.
```bash
python database.py
```