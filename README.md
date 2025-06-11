
# CERL library

Python bindings for the [Consortium of European Research Library's API](https://data.cerl.org).

NOTE: This is a fork of the original cerl package by Andreas Walker (Hochschule Hannover, ORCID 0000-0002-1541-122X), preserved from version 0.0.5, with a small fix to cerl.py for compatibility with newer versions of urllib3.

## Installation (Updated)

```bash
pip install git+https://github.com/rscebba/cerl-fixed.git
```
Import as usual
 
```bash
import cerl
```

## Basic example

```python
from cerl import ample_query, ample_record, ids_from_result, by_dot, the

# Connect to any AMPLE instance
ct = 'data.cerl.org/thesaurus'
# Run a search query
result = ample_query(ct, 'Purslowe, Elizabeth')
for idx in ids_from_result(result):
    # Download the record as a Python dict
    record = ample_record(ct, idx)
    # Access the record by dot notation
    cid = the(by_dot(record, '_id'))
    assert cid == idx
```

## Features
* Access to any AMPLE instance by specifying the `host` string (e.g. "data.cerl.org/thesaurus")
  * Some databases hardcoded as syntactic sugar:
    * `CT` 
    * `ISTC`
    * `HOLDINST`
    * `MEI`
* Use the standard search syntax with `ample_query`
  * The same databases hardcoded as syntactic sugar: `ct_query` etc.
* Download records as Python `dict` objects with `ample_record`
  * Again, `ct_record` etc.
* Download records in other formats with `ample_record_export`
  * Again, `ct_record_export` etc.
  * Export formats supported (but not all for each database):
    * rdf/ttl
    * rdf/xml
    * rdf/jsonld
    * json
    * yaml
    * unimarc
* Access to record fields using the dot notation from search syntax via `by_dot` (NOTE: always returns a `list` of results)
    * If you know there is only one object/value being returned, wrap in `the`
    * Syntactic sugar around some fields:
      * Resolve CT record types with `ct_record_type`
      * Get the CID (CERL ID) with `cid`
* Add a timestamp to a record after modifying it with `add_timestamp`


    
    
