from datetime import date


def addYears(d, years):
    try:
#Return same day of the current year        
        return d.replace(year = d.year + years)
    except ValueError:
#If not same day, it will return other, i.e.  February 29 to March 1 etc.        
        return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))


def remove_words(word, **kwargs):
    """
        Replaces part of the word by another value
        Arguments --> the word that has parts to be replaced,
                    the parts of the word to replace and by value value to replace them specified in tuples
        Returns --> the new word with the desired parts replaced
    """

    for word_to_remove in kwargs.values():
        word = word.replace(word_to_remove[0], word_to_remove[1])

    return word


def get_first_letters(x, number_ok, number_ko, size):
    return x[:number_ko] if len(x) < size else x[:number_ok]



def get_list_from_list(init_list, list_to_be, is_in_list=True):
    """ Generates a list from a initial one. init_list is the one we loop through and list_to_be is the
        one within the element must also be. list_to_be serves as a check on the element, i.e. should the element
        be taken or not.
    """
    if isinstance(list_to_be, str) == True:
        list_to_keep = [element for element in init_list if list_to_be in element] if is_in_list == True else [element for element in init_list if list_to_be not in element]
    else:
        list_to_keep = [element for element in init_list if element in list_to_be] if is_in_list == True else [element for element in init_list if element not in list_to_be]

    return list_to_keep



def get_columns_by_type(df, types=None, excluded_columns=None):
    """
        Get the features from the dataframe depending on the required features specified in the args
        Arguments -->df, types of data specified by the user in a list or as string if only one, and the list of features to exclude
        Returns --> a df with only the selected features
    """

    df_columns = df.select_dtypes(include=types)

    if excluded_columns is not None:
        df_columns = df_columns.drop(columns=excluded_columns, errors='ignore')
    return df_columns