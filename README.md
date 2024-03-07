## Setup

Open a terminal and `cd` into this repo.

Unzip the data folder

```bash
unzip data.zip
```

### APIs

The current version of RECEIPT CONTEXTUALIZER is uses the Google Cloud Vision API the Mistral API. Allow your instance of RECEIPT CONTEXTUALIZER to connect to both with the following steps.

Create necessary files and directories.

```bash
touch .env
```

```bash
mkdir SA_key
```

Create a GCP project and a service account, download and save the JSON in the directory `SA_key`, and activate the [Cloud Vision API](https://console.cloud.google.com/marketplace/product/google/vision.googleapis.com). You can find help on how to create a project and a service account [here](https://support.google.com/a/answer/7378726).

Create an API-key on Mistral AI's [La Platforme](https://console.mistral.ai).

Open the `.env` file and A. enter your Mistral API key and B. your GCP service account's filename into the path.

```bash
MISTRAL_API_KEY="<your_mistral_api_key>"
GOOGLE_SA_KEY="SA_key/<name_of_your_API_key>.json"
```

### Database

This prototype runs on a PostgreSQL vector database. If you don't have an instance running, you can set up a local database with the following steps.

If you choose a different PostgreSQL instance, change the standard username and password in the database.py script.

Install PostgreSQL with [Homebrew](https://brew.sh). 

```bash
brew install postgresql@14
```
Install [Docker](https://www.docker.com/get-started/).

Create a `receipts` database container by running:

```bash
docker build -t postgres .
```
```bash
docker run -d -e POSTGRES_USER='postgres' \
    -e POSTGRES_PASSWORD='postgres' \
    -e POSTGRES_DB='receipts' \
    -v $(pwd)/db-data:/var/lib/postgresql/data \
    -p 5432:5432 \
    --name receipts-db \
    postgres
```

Start the database container

- Open the Docker dashboard and click the play icon at the `receipts` container.

### Python environment

Create a new python environment and install the requirements.

```bash
pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Insert Rewe products for search

Run the database.py script to insert the REWE search data.

```bash
python database.py
```

### Use the interface

Start RECEIPT CONTEXTUALIZER by running

```bash
streamlit run home.py
```
