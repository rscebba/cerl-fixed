from typing import Any, Union

"""Utility functions"""

# === Access dictionaries by dot notation ===

def _jump_list(target: Union[dict, list], key: str) -> list:
    """Implements "jumping across" lists when using dot notation
    
    Arguments
    ---------
    target : Union[dict, list]
        Either a dictionary or a list
    key
        Key to be resolved against the target

    Returns
    -------
    list
        The list of values
    """
    if isinstance(target, dict):
        value = target.get(key, None)
        return [value] if value else []
    if isinstance(target, list):
        values = []
        for item in target:
            value = _jump_list(item, key)
            values.extend(value)
        return values

def by_dot(record: dict, path: str) -> list:
    """Allows access to a dictionary by dot notation and returns a list of values
    
    Always returns a list, because dot notation may have multiple target values.
    If target is known to be a single value, explicitly wrap the result in `the()`

    Arguments
    ---------
    record : dict
        The record to be queried
    path : str
        A path of keys in dot notation

    Returns
    -------
    current : list 
        The list of values that can be found under this key

    See also
    --------
    the : Simplify list with only a single element
    """
    current = [record]
    for step in path.split('.'):
        branches = []
        for branch in current:
            value = _jump_list(branch, step)
            if value: branches.extend(value)
        current = branches 
    return current

def the(l: list) -> Any:
    """Iota operator, returns single element from list or raises an error
    
    Parameters
    ----------
    l : list
        Any list that contains a single element

    Returns
    -------
    Any
        The single element from the list l

    Raises
    ------
    ValueError
        If the list contains fewer or more than 1 element
    """
    if len(l) == 0:
        raise ValueError(f"{l} is empty")
    if len(l) != 1:
        raise ValueError(f"{l} contains more than one element")
    else:
        return l[0]
