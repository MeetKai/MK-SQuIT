# Copyright (c) 2020 MeetKai Inc. All rights reserved.

"""Get raw data from WikiData."""
import os
from typing import Dict

import typer
import requests, json
from requests.utils import quote

URL = "https://query.wikidata.org/sparql?format=json&query="

domain_sparql = """SELECT ?thing ?thingLabel ?thingAltLabel
WHERE
{
    ?thing wdt:P31 wd:DOMAIN_ID.
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
LIMIT 5000"""

properties_sparql = """SELECT DISTINCT ?prop ?propLabel ?propAltLabel WHERE {
  wd:DOMAIN_PROTO_ID ?p ?thing.
  ?prop wikibase:directClaim ?p.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}"""

domains = {
    "literary_work": "Q7725634",
    "movie": "Q11424",
    "person": "Q5",
    "television_series": "Q5398426",
    "chemical": "Q79529",
}

domain_prototypes = {
    "literary_work": "Q43361",
    "movie": "Q47221",
    "person": "Q43361",
    "television_series": "Q208072",
    "chemical": "Q279055",
}


def get_properties(data_dir: str):
    # Retrieve list of properties for a prototypical item in each domain
    for k, v in domain_prototypes.items():
        r = requests.get(url=URL + quote(properties_sparql.replace("DOMAIN_PROTO_ID", v)))
        save_json(r.json(), os.path.join(data_dir, f"{k}-props.json"))
        print(f"Retrieved {k} properties")


def get_domains(data_dir: str):
    # Retrieve list of entities for each domain
    for k, v in domains.items():
        r = requests.get(url=URL + quote(domain_sparql.replace("DOMAIN_ID", v)))
        save_json(r.json(), os.path.join(data_dir, f"{k}-5k.json"))
        print(f"Retrieved {k} entities")


def save_json(json_object: Dict, filename: str):
    raw_j = json_object["results"]["bindings"]
    things = []
    for o in raw_j:
        thing_dict = dict()
        for k, v in o.items():
            thing_dict[k] = v["value"]
        things.append(thing_dict)
    f = open(filename, "w")
    f.write(json.dumps(things, indent=4))
    f.close()


def main(data_dir: str = "data"):
    """Gets raw data from WikiData.
    python -m scripts.gather_wikidata --data-dir data
    """
    get_domains(data_dir)
    get_properties(data_dir)


if __name__ == "__main__":
    typer.run(main)
