from typing import List, Dict
from itertools import zip_longest

from algomancy.dataengine.datamanager import InputFileConfiguration


def hamming_distance(s1, s2):
    """
    Calculates the Hamming distance between two strings.

    The Hamming distance is defined as the number of differing characters between
    two strings of equal length. If the strings are of different lengths, it will
    compare them up to the length of the shorter string and count differing
    characters, considering any excess characters in the longer string as
    additional differences.

    Args:
        s1: The first string to compare.
        s2: The second string to compare.

    Returns:
        int: The Hamming distance between the two strings.
    """
    return sum(c1 != c2 for c1, c2 in zip_longest(s1, s2))

def find_closest_match(file_names: List[str], file_configuration: InputFileConfiguration)-> str:
    """
    Finds the closest match to a file configuration's reference name.

    Finds the file name from a list that is the closest match to a given file configuration's
    reference name using the Hamming distance as the measure of similarity.

    Args:
        file_names (List[str]): A list of file names to evaluate.
        file_configuration (InputFileConfiguration): Configuration object containing
            the reference file name for comparison.

    Returns:
        str: The file name from the list that is the closest match to the reference
            file name.
    """
    return min(
        file_names,
        key=lambda x: hamming_distance(x.lower(), file_configuration.file_name_with_extension.lower())
    )

def is_bijective_mapping(mapping: Dict[str, str])-> bool:
    """
    Determines if the input mapping is bijective.

    A mapping is bijective if every element of the domain is mapped to a unique
    element of the codomain, and every element of the codomain is uniquely
    mapped back to an element in the domain. This function checks the bijection
    by verifying that the lengths of the mapping's values and keys are equal
    to the mapping itself.

    Args:
        mapping (Dict[str, str]): A dictionary representing the mapping between
            two sets where keys represent the domain and values represent the
            codomain.

    Returns:
        bool: True if the mapping is bijective, otherwise False.
    """
    return len(mapping) == len(set(mapping.values())) and len(mapping) == len(set(mapping.keys()))

def match_file_names(
        file_configurations: List[InputFileConfiguration],
        file_names: List[str]
)-> Dict[str, str]:
    """
    Matches file configurations to file names and attempts to create a bijective mapping.

    This function takes a list of file configurations and file names and tries to match
    each configuration to the closest corresponding name. The result will be a dictionary
    representing a bijective mapping between the file configurations and the file names.
    An exception is raised if such a bijective mapping cannot be established.

    Args:
        file_configurations: List of InputFileConfiguration objects to match.
        file_names: List of available file names.

    Raises:
        AssertionError: If the number of file_names is less than or greater than the number
            of file_configurations.
        Exception: If a bijective mapping between file configurations and file names cannot
            be established.

    Returns:
        A dictionary mapping file configuration names to file names.
    """
    assert len(file_names) >= len(file_configurations), "Missing input files"
    assert len(file_names) <= len(file_configurations), "Too many input files"

    initial_guess = {fc.file_name: find_closest_match(file_names, fc) for fc in file_configurations}
    if is_bijective_mapping(initial_guess):
        return initial_guess

    raise Exception("Could not find bijective mapping.")
