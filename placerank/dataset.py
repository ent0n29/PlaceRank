from placerank.logic_views import InsideAirbnbSchema
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, Index
from whoosh.analysis import Analyzer
import requests
import io
import os
import csv
import gzip
import sys

LINK = "http://data.insideairbnb.com/united-states/ny/new-york-city/2024-01-05/data/listings.csv.gz"

def download_dataset_source(storage: io.StringIO) -> io.StringIO:
    """
    Download data of InsideAirbnb and unpacks it in memory.
    """

    r = requests.get(LINK)
    
    if not r.ok:
        raise ConnectionError(f"Error retrieving the dataset source. Server returned status code {r.status}")
    
    with io.BytesIO(r.content) as gz_response:
        with gzip.GzipFile(mode="r:gz", fileobj=gz_response) as gz:
            for line in gz:
                storage.write(line.decode()) #TODO: reimplement using less memory

    storage.seek(0)
    return storage


def create_index(index_dir: str, schema: Schema) -> Index:
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    
    ix = create_in(index_dir, schema)

    return ix


def populate_index(index_dir: str, analyzer: Analyzer = None):
    schema = InsideAirbnbSchema(analyzer)
    ix = create_index(index_dir, schema)

    with io.StringIO() as storage, ix.writer() as writer:
        download_dataset_source(storage)

        dset = csv.DictReader(storage)

        for row in dset:
            writer.add_document(**schema.get_document_logic_view(row))

    ix.close()


if __name__ == "__main__":
    populate_index(sys.argv[1])
