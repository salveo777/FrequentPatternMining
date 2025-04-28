import pandas as pd


def transform_pandas_to_t (df):
    """
    Transforms a binary transaction database into a list of sets.

    Args:
        df (pandas.DataFrame): a dense transaction database with items as columns, rows as transactions, and int or bool entries indicating the existence (True | 1) or absence (False | 0) of an item in the corresponding transaction (i.e., row).

    Returns:
        a list of sets

    """
    return [set(df.columns.values[row]) for _, row in df.astype(bool).iterrows()]


def get_transaction_dict (transaction_db, sort_asc = True):
    """
    Transforms our transaction list (of sets) to a (sorted) dictionary containing the frequency per item and the indices of its occurences in our transaction list.

    Args:
      transaction_db (list): a list of sets
      sort_asc (bool): should our transaction dictionary be sorted ascendingly

    Returns:
      a nested dictionary containing frequency and (positional) indices per item
    """
    # get all unique items in our transaction db
    elems = set.union(*transaction_db)
    out_dict = {}

    # derive frequency & positional indices per item
    for e in elems:
        pos_set = set()
        for i in range(len(transaction_db)):  
            if e in transaction_db[i]:
                pos_set.add(i)
        out_dict[e] = {"frequency": len(pos_set),
                       "positions": pos_set}

    # sort by support ascending - 
    if sort_asc:
        out_dict = sort_by_support_asc(out_dict)

    return(out_dict)


def sort_by_support_asc (my_dict):
    """
    Sort our nested frequent item set dictionary by its frequency (i.e., support).

    Args:
      our transaction dict (dict): with item(s) as keys and a sublist consisting of frequency and positions

    Returns:
      a sorted transaction dict
    """
    return dict(sorted(my_dict.items(), key = lambda item: item[1]["frequency"]))



def tiny_eclat (transaction_dict, smin, prefix = None, F = None):
  """
  The recursive Eclat algorithm.

  On highest level, we input all singleton items with their support in ascending order.
  For each singleton we check, if it meets the minimal support. 
  If so, we save this observation in our output dictionary F. 
  Then, we go into the recursion, i.e., we define our current frequent element as prefix and build a conditional transaction dict from it.
  This conditional transaction dict is then processed as usual with tiny_eclat().

  Args:
    transaction_dict (dict): our sorted (conditional) transaction dictionary.
    smin (int): our minimal absolut support (i.e., frequency to determine "frequent items"); can also be written as relative support [%] * N_transactions.
    prefix (str): empty in the highest recursion; gets extended when conditional transaction dictionaries are built.
    F (dict): our interim output dictionary for frequent items

  Returns:
    F (dict): a nested dictionary containing all (frequent) item sets, with their support (i.e., frequency) and positional indices.
  """

  # initialize
  if prefix is None:
      prefix = str()
  if F is None:
      F = {}

  # as long as there are entries in our transaction dict, do this:
  if bool(transaction_dict):
      for index, key in enumerate(transaction_dict.keys()):
          if transaction_dict[key]["frequency"] >= smin:
              # this is a frequent item, hence prepare prefix for examining conditional transaction dicts
              pf = key
              # styling workaround - otherwise we would have singletons named "__Item"
              if prefix == "":
                  pf_out = key
              else:
                  pf_out = prefix + "__" + key
              F[pf_out] = {"frequency": transaction_dict[key]["frequency"],
                            "positions": transaction_dict[key]["positions"]}

              # prepare conditional dict
              remaining_transaction_dict = divide_transactions(index, transaction_dict)  # divide & conquer
              cond_transaction_dict = cond_transaction_dict_isect(key, transaction_dict, remaining_transaction_dict, True)  # create conditional dict

              # go into recursion for new conditional dicts if it's not empty
              if bool(cond_transaction_dict): 
                  tiny_eclat(transaction_dict = cond_transaction_dict, smin = smin, prefix = pf_out, F = F)

  return F


def divide_transactions (index, transaction_dict):
    """
    Divide to conquer the sorted transaction dict: derive remaining items with equal or higher support (i.e., current item index + 1) which were not visited yet

    Args:
      index (int): position of current item in transaction list
      transaction_dict (dict): nested dictionary containing remaining information

    Returns:
      a sorted transaction dict containing items with equal or higher support.
    """
    return {k: transaction_dict[k] for k in list(transaction_dict.keys())[index+1:]}


def cond_transaction_dict_isect (key, original_transaction_dict, remaining_transaction_dict, sort_asc = True):
    """
    Calculate support (i.e., item frequency) and positional indices for conditional item sets.

    Example: Assume following items and their support: A < B < C < D, and entering key = A.
    We then have our original_transaction_dict = {A, B, C, D} and remaining_transaction_dict = {B, C, D}
    Further lets assume, key = A occurs on this indices {1,4,5} in our original_transaction_dict.
    Then our cond_transaction_dict will only comprise those items in {B,C,D} which have overlapping indices with A.

    Args:
      key (str): current item key (e.g., name)
      original_transaction_dict (dict): original/ "independent" sorted transaction dict
      remaining_transaction_dict (dict): original_transaction_dict without current or less suported items
      sort_asc (bool): if True sort conditional transaction dict ascendingly

    Returns:
      cond_transaction_dict (dict): a sorted conditional transaction dict, which only contains items which co-occure with our initially set key item
    """
    #prefix = key
    src1_dict = original_transaction_dict[key]  
    cond_transaction_dict = dict()
    for new_index, new_key in enumerate(remaining_transaction_dict.keys()):  
        src2_dict = remaining_transaction_dict[new_key]  
        cond_trans = src1_dict["positions"].intersection(src2_dict["positions"])
        cond_supp = len(cond_trans)
        cond_transaction_dict[new_key] = {"frequency": cond_supp,
                                          "positions": cond_trans}

        # sort by support ascendingly
        if sort_asc:
            cond_transaction_dict = sort_by_support_asc(cond_transaction_dict)

    return cond_transaction_dict


def summarise_tiny_eclat(tiny_eclat_result, as_df = True):
  """
  Summarise output of tiny_eclat(), by calculating the frequent item set size, and descendingly sorting the resulting dictionary based on 1) frequent item set size and 2) support (i.e., set frequency).
  If not differently specified, the output is formatted as a pandas dataframe.

  Args:
    tiny_eclat_results (dict): output dictionary of tiny_eclat(), containing frequent item sets (i.e., meeting minimal support) with their support and positional indices.
    as_df (bool): if True the output dictionary is formated as a pandas dataframe

  Results:
    either a sorted dictionary or dataframe
  """

  # Calculate frequent item set size, to order by it
  out = {k: {**value, "frequent_set_size": len(k.split("__"))} for k, value in tiny_eclat_result.items()}
  out = dict(sorted(out.items(), key = lambda item: (item[1]["frequent_set_size"], item[1]["frequency"]), reverse=True))

  # transform results into a dataframe
  if as_df:
      out = pd.DataFrame([{"KEY": key,
                           "ITEM_SET": set(key.split("__")),
                           "ITEM_SET_SIZE": value["frequent_set_size"],
                           "SUPPORT": value["frequency"],
                           "POSITION_ID": value["positions"]
                           } for key, value in out.items()
                           ])

  return out
