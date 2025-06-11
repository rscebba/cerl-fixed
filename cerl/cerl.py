"""Library for querying CERL infrastructure"""

from dataclasses import dataclass
import requests 
from typing import List, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote 
from .utils import the, by_dot

def setup_requests() -> requests.Session:
    """Sets up a requests session to automatically retry on errors
    
    cf. <https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/>
    
    Returns
    -------
    http : requests.Session
        A fully configured requests Session object
    """
    http = requests.Session()
    assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
    http.hooks["response"] = [assert_status_hook]
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    return http

http = setup_requests()

# === Definition of complex data types ===

@dataclass
class QueryResult:
    """Representation of a query result
    
    Attributes
    ----------
    hits : int
        The number of hits returned by the query
    rows : list[dict]
        A list of dictionaries representing the (abbreviated) records returned by the query
    """
    hits: int
    rows: List[dict]


# === Interacting with the AMPLE API ===

def ample_query_hits(host: str, query: str) -> int:
    """Requests the number of hits for a query from the AMPLE API
    
    Arguments
    ---------
    host : str
        The URL for the AMPLE service to be queried
    query : str
        The query to be sent

    Returns
    -------
    hits : int
        The number of hits returned for the query
    """
    r = http.get(f"https://{host}/_search?query={quote(query)}&size=1&format=json")
    j = r.json()
    hits = j['hits']
    if isinstance(hits, dict):
        # AMPLE either returns {'hits': int} or {'hits': {'value': int}}
        hits = hits.get('value', 0)
    return hits

def ample_query_generator(host: str, query: str) -> Union[int, List[dict]]:
    """Requests the search results for a query from the AMPLE API in chunks of 100 records
    
    Arguments
    ---------
    host : str
        The URL for the AMPLE service to be queried
    query : str
        The query to be sent    

    Yields
    ------
    hits : int
        Number of hits (first value yielded)
    rows : list[dict]
        A list of dictionaries representing (abbreviated) records (all subsequent values yielded)
    """
    hits = ample_query_hits(host, query)
    yield hits

    offset = 0 
    # ElasticSearch will not return more than 10.000 records, so not point querying beyond that
    while offset < hits and offset < 10000:
        r = http.get(f"https://{host}/_search?query={quote(query)}&size=100&from={offset}&format=json")
        rows = r.json().get('rows', [])
        offset += 100
        yield rows

def ample_query(host: str, query: str) -> QueryResult:
    """Requests the search results for a query from the AMPLE API
    
    Arguments
    ---------
    host : str
        The URL for the AMPLE service to be queried
    query : str
        The query to be sent    

    Returns
    -------
    QueryResult
        A QueryResult object containing the number of hits and up to 10.000 search results    
    """
    generator = ample_query_generator(host, query)
    hits = next(generator)
    if hits:
        rows = list(sum(list(generator), []))
    else:
        rows = []
    return QueryResult(hits, rows)

def ids_from_result(result: QueryResult) -> List[str]:
    """Extract the IDs from a QueryResult object

    Arguments
    ---------
    result : QueryResult
        A QueryResult object returned by ample_query()
    
    Returns
    -------
    list[str]
        The IDs of all records contained in the QueryResult
    """
    return [row.get('id', None) for row in result.rows]

def _ample_record_request(host: str, idx: str, form: str, style: str) -> requests.Response:
    """Requests a record through the AMPLE API and returns the response

    Arguments
    ---------
    host : str
        The URL for the AMPLE service to be queried
    idx : str
        The identifier of the record to be requested
    form : str
        The form argument to be passed to the API
    style : str
        The form argument to be passed to the API
        (Form and Style together determine the record format)

    Returns
    -------
    r : requests.Response
        A requests Response object containing the record
    """

    r = http.get(f"https://{host}/{quote(idx)}?format={form}&style={style}")
    return r

def ample_record_export(host: str, idx: str, export: str) -> str:
    """Returns a record as a string in an export format
    
    Arguments
    ---------
    host : str
        The URL for the AMPLE service to be queried
    idx : str
        The identifier of the record to be requested
    export : str
        The desired export format    
    
    Returns
    -------
    str
        The record as a String in the specified format

    See also
    --------
    ample_record : Returns the record as a Python dictionary
    """

    # The AMPLE API determines record format from a combination
    # of the two arguments 'form' and 'style', so these are
    # resolved here:
    form, style = {
        'rdf/ttl': ('txt', 'ttl'),
        'yaml': ('txt', None),
        'rdf/xml': ('rdfxml', None),
        'rdf/jsonld': ('json', 'jsonld'),
        'unimarc': ('txt', 'internal')
    }.get(export, ('json', None))
    return _ample_record_request(host, idx, form, style).text

def ample_record(host: str, idx: str) -> dict:
    """Returns a record as a dictionary
    
    Arguments
    ---------
    host : str
        The URL for the AMPLE service to be queried
    idx : str
        The identifier of the record to be requested

    Returns
    -------
    dict
        The Python dictionary created from the JSON returned by the AMPLE API

    See also
    --------
    ample_record_export : Return the record as a String and in various formats
    """
    return _ample_record_request(host, idx, 'json', None).json()

# === Interacting with records ===

# == Syntactic sugar around fields ==
def cid(record: dict) -> str:
    """Returns the CERL identifier of a record, if available
    
    Arguments
    ---------
    record : dict
        The record of interest
    
    Returns
    -------
    cid : str
        The identifier of the record

    Raises
    ------
    ValueError
        If no identifier is found in the record
    """
    cid = the(by_dot(record, '_id'))
    if not isinstance(cid, str):
        raise ValueError(f"Not a string: {cid}")
    return cid

def ct_record_type(record: dict) -> str:
    """Infers the CERL Thesaurus record type from the identifier
    
    Arguments
    ---------
    record : dict
        The record of interest
    
    Returns
    -------
    str
        The human-readable record type of the record
    """
    return {
        'cnl': 'place',
        'cnp': 'person',
        'cni': 'printer',
        'cnc': 'corporate'
    }.get(cid(record)[:3], 'unspecified')

# === Hardcoded databases ===

CT, ISTC, HOLDINST, MEI = (f'data.cerl.org/{db}' for db in ('thesaurus', 'istc', 'holdinst', 'mei'))

ct_query                = lambda query: ample_query(CT, query)
holdinst_query          = lambda query: ample_query(HOLDINST, query)
istc_query              = lambda query: ample_query(ISTC, query)
mei_query               = lambda query: ample_query(MEI, query)

ct_record               = lambda *args, **kwargs: ample_record(CT, *args, **kwargs)
holdinst_record         = lambda *args, **kwargs: ample_record(HOLDINST, *args, **kwargs)
istc_record             = lambda *args, **kwargs: ample_record(ISTC, *args, **kwargs)
mei_record              = lambda *args, **kwargs: ample_record(MEI, *args, **kwargs)

ct_record_export        = lambda *args, **kwargs: ample_record_export(CT, *args, **kwargs)
holdinst_record_export  = lambda *args, **kwargs: ample_record_export(HOLDINST, *args, **kwargs)
istc_record_export      = lambda *args, **kwargs: ample_record_export(ISTC, *args, **kwargs)
mei_record_export       = lambda *args, **kwargs: ample_record_export(MEI, *args, **kwargs)