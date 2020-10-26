## Snippets

**Single-Entity CFG**

```plaintext
S -> "[WH]" IS Q "?"
IS -> "is" | "was"
Q -> NOUN | VERB-ADP
NOUN -> "[THING]" | NOUN "'s [NOUN]" | "the [NOUN] of" NOUN
VERB-ADP -> NOUN "[VERB-ADP]"
```

**Single-Entity Example Production**

`[WH] was the [NOUN] of [THING] [VERB-ADP] ?`

**Single-Entity Example Question**

`Who was the film director of Fargo influenced by?`

**SPARQL Template and Complete Query** 

`SELECT ?end WHERE { [CLAUSES] }`

`SELECT ?end WHERE { [ Fargo ] wdt:P57 / wdt:P737 ?end . }`



**Single-Entity Numbered Template Example**

`[WH] was the [NOUN:A:0] of [THING:A] [VERB-ADP:A:1] ?`



**Example of Entity Storage**

```json
[
	...,
  {
    "thing": "http://www.wikidata.org/entity/Q222720",
    "labels": [
      "Fargo"
    ]
  },
  ...
]
```



**Example of Predicate Storage**

```json
[
  ...,
  {
    "prop": "http://www.wikidata.org/entity/P737",
    "type": "person->person",
    "labels": [
      "favorite player",
      "has influence",
      "influenced by",
      "informed by",
      "role model"
    ],
    "pos": {
      "NOUN": [
        "favorite player",
        "role model"
      ],
      "AUX-NOUN": [
        "has influence"
      ],
      "VERB-ADP": [
        "influenced by",
        "informed by"
      ]
    }
  },
  ...
]
```

