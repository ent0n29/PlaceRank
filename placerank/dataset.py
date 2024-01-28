from placerank.views import InsideAirbnbSchema, DocumentView
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, Index
from whoosh.analysis import Analyzer
import requests
import io
import os
import sys
import csv
import gzip
import pydash
import argparse

# DEFAULT_URL = "http://data.insideairbnb.com/united-states/ny/new-york-city/2024-01-05/data/listings.csv.gz"
# DEFAULT_DIR = "index/"
# DEFAULT_LOCAL_FILE = "datasets/listings.csv"

def download_dataset(url: str, storage: io.StringIO) -> io.StringIO:
    """
    Download data of InsideAirbnb and unpacks it in memory.
    """

    r = requests.get(url)
    
    if not r.ok:
        raise ConnectionError(f"Error retrieving the dataset source. Server returned status code {r.status}")

    with io.BytesIO(r.content) as gz_response:
        with gzip.GzipFile(mode="r:gz", fileobj=gz_response) as gz:
            for line in gz:
                storage.write(line.decode()) #TODO: reimplement using less memory

    storage.seek(0)
    return storage


def get_dataset(local_file: str, remote_url: str, storage: io.StringIO) -> io.StringIO:
    """
    Proxy method that writes the downloaded content to file, if passed; otherwise it keeps an in-memory representation of the dataset.
    If just a local file is passed, the dataset is loaded from that file.
    """
    if not remote_url and (not local_file or not os.path.isfile(local_file)):
        raise RuntimeError("Invalid local file and no remote source. Please provide at least one valid argument.")

    if remote_url:
        storage = download_dataset(remote_url, storage)

        if local_file:
            with open(local_file, 'w') as f:
                print(storage.getvalue(), file = f)
        return storage
    
    with open(local_file, 'r') as f:
        storage = io.StringIO(f.read())
    return storage


def create_index(index_dir: str, schema: Schema) -> Index:
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    
    ix = create_in(index_dir, schema)

    return ix


def populate_index(index_dir: str, local_file: str, remote_url: str = None, analyzer: Analyzer = None):
    schema = InsideAirbnbSchema(analyzer)
    ix = create_index(index_dir, schema)

    with io.StringIO() as ram_storage, ix.writer() as writer:
        storage = get_dataset(local_file, remote_url, ram_storage)

        dset = csv.DictReader(storage)

        for row in dset:
            writer.add_document(**schema.get_document_logic_view(row))

    ix.close()


def load_page(local_dataset: str, id: str) -> DocumentView:
    """
    TODO: optimize using in-memory dataset
    """
    with open(local_dataset, 'r') as listings:
        return DocumentView.from_record(
            pydash.chain(csv.DictReader(listings.readlines()))
                .filter(lambda r: r['id'] == id)
                .value()
                .pop()
        )


def main():
    parser = argparse.ArgumentParser(
        prog = "Placerank dataset downloader and indexer",
        description = "Convenience module to download and index a InsideAirBnb dataset"
    )

    parser.add_argument('-i', '--index-directory', required = True, help = 'Directory in which the index is created')
    parser.add_argument('-l', '---local-file', required = True, help = 'Path to local file. Download destination if dataset is not there, otherwise used as a local cache')
    parser.add_argument('-r', '--remote-url', help = 'Source URL from which the dataset is downloaded. Omit it if you want to use the local copy on your disk.')
    
    args = parser.parse_args(sys.argv[1:])  # Exclude module itself from arguments list

    populate_index(args.index_directory, args.local_file, args.remote_url)


if __name__ == "__main__":
    main()
