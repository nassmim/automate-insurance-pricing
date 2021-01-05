import pandas as pd
import numpy as np
from sklearn.utils import resample

from copy import deepcopy
from datetime import date, timedelta, datetime
from calendar import isleap
import math
import random

try:
    from automated_pricing_flow.standard_functions import *
except:
    from standard_functions import *


def resample_data(X_train, y_train, upsample=True, replace=True, proportion_neg_over_pos=0.3, random_state=42):
    """
        Resamples the data either duplicating negative values (i.e. the label in minority) or by removing positive values, but risk of information loss
        Arguments --> the features, the predicted variable, a replace indicating if sampled data overwrites the current data,
                    the proportion of negative values over the positive value,
                    the seed to reproduce the exact same results
        Returns --> the resampled data
    """

    X_for_resampling = pd.concat((X_train, y_train), axis=1)
    X_negative = X_for_resampling[y_train == 0]
    X_positive = X_for_resampling[y_train > 0]

    if upsample == True:
        length_for_resampling = math.floor(len(X_negative) * proportion_neg_over_pos)
        X_positive_resampled = resample(X_positive, replace=replace, n_samples=length_for_resampling, random_state=random_state)
        X_resampled = pd.concat((X_negative, X_positive_resampled))
    else:
        length_for_resampling = math.floor(len(X_positive) / proportion_neg_over_pos)
        X_negative_resampled = resample(X_negative, replace=replace, n_samples=length_for_resampling, random_state=random_state)
        X_resampled = pd.concat((X_positive, X_negative_resampled))

    return X_resampled



def create_year_month(row, date_to_use):
    year = str(row[date_to_use].year)
    month_int = row[date_to_use].month
    month = str(month_int) if month_int > 9 else '0' + str(month_int)
    return year + '-' + month



def create_bins(df_portfolio, cut_func='pd.cut', column_to_use=None, bins=5, df_claims=None, bins_labels=None, right=False):

    """
        Gathers feature values within bins
        Arguments --> the df, the function to split in bucket, the column to reduce into bins,
                    the name of the second df where to split the variable in buckets, the bins we want and their names
        Returns --> Nothing, it directly changes the df arguments
    """

    portfolio_new_column = eval(cut_func)(df_portfolio[column_to_use], bins, labels=bins_labels, right=right) if cut_func == 'cut' else eval(cut_func)(df_portfolio[column_to_use], bins, labels=bins_labels)

    if df_claims is not None:
        if cut_func == 'pd.qcut':
            right = True
            intervals = portfolio_new_column.unique()
            left_bins, right_bins = [interval.left for interval in intervals], [interval.right for interval in intervals]
            min_left = min(left_bins)
            right_bins.insert(0, min_left), right_bins.sort()
            bins = right_bins

        claims_new_column = pd.cut(df_claims[column_to_use], bins=bins, labels=bins_labels, right=right)

        return portfolio_new_column, claims_new_column
    
    return portfolio_new_column

def derive_policy_totals(row, start_business_year, extraction_year, column_to_use):
    """
        Sums the earned amounts (premium, commission, etc.) in a same row
        Arguments --> the df row, the start / end year of the business production
                        and the column for which we calculate the sum
        Returns --> the total earned amount for a specific row (most time the annual contract earned amount)
    """

    total_sum = 0

    for year in range(start_business_year, extraction_year + 1):
        total_sum += row['' + column_to_use.format(year)]

    return total_sum



def derive_yearly_amounts(df, start_business_year, extraction_date, contract_start_date_column_name, contract_end_date='actual_contract_end_date', row_per_each_contract_year=True, add_one_day=False, written_premium_column_name='asif_written_premium_excl_taxes', number_paid_premium_column_name='written_multiplier'):
    """
        Derives the earned amounts (premium, commission, etc.) for each occurrence year
        Arguments --> the df row, the business start year, the data extraction date, the contract start and end columns names
                    a flag indicating if the portfolio has a unique row for the full policy contract or a row per yearly amendment,
                    a flag indicating if a day must be added to the end date to derive the dates differences,
                    the columns names to use for premium and for the number of times premiums was paid 
        Returns --> a new row with the columns created
    """

    df_copy = deepcopy(df)
    extraction_year = extraction_date.year
    
    if row_per_each_contract_year == True:
        for year in range(start_business_year, extraction_year + 1):
            df_copy['exposure_in_{}'.format(year)] = df_copy.apply(lambda x: derive_annual_exposure(x, year, extraction_date, contract_start_date_column_name, contract_end_date, add_one_day), axis=1)
            df_copy['asif_earned_premium_in_{}'.format(year)] = df_copy['exposure_in_{}'.format(year)] * df_copy[written_premium_column_name]

    else:
        for year in range(start_business_year, extraction_year + 1):
            df_copy['exposure_in_{}'.format(year)] = df_copy.apply(lambda x: derive_annual_exposure(x, year, extraction_date, contract_start_date_column_name, contract_end_date, add_one_day), axis=1)
            df_copy['asif_written_premium_in_{}'.format(year)] = df_copy.apply(lambda x: derive_yearly_amount(x, year, extraction_date, contract_start_date_column_name, written_premium_column_name, contract_end_date, number_paid_premium_column_name), axis=1)
            df_copy['asif_earned_premium_in_{}'.format(year)] = df_copy['exposure_in_{}'.format(year)] * df_copy[written_premium_column_name] / df_copy[number_paid_premium_column_name]

    return df_copy



# Function that must be re-worked, not time efficient so far
# def derive_yearly_amounts(row, start_business_year, extraction_year, contract_start_date_column_name, incl_gwp_per_year=False, inflation_rate=None):
#     """
#         Derives the earned amounts (premium, commission, etc.) in a specific year
#         Arguments --> the df row, the year
#                     If incl_gwp_per_year is True, creates a column for the written premium per occurrence year\n\
#                     as occurrence is equivalent to effective year of the contract, the use case would be if portfolio is at inception level
#                     if inflation rate is set up, then it calculates the inflated amount
#         Returns --> a new row with the columns created
#     """

#     for year in range(start_business_year, extraction_year + 1):
#         exposure = row['exposure_in_{}'.format(year)] = derive_annual_exposure(row, year, extraction_date, contract_start_date_column_name)
#         row['asif_earned_premium_in_{}'.format(year)] = row['written_premium_excl_taxes'] * exposure * ((1 + inflation_rate) * (extraction_year - year) if inflation_rate is not None else 1)

#         # Calculation has to be based on the contract lenght in years
#         if incl_gwp_per_year == True:
#             row['asif_written_premium_in_{}'.format(year)] = derive_yearly_written_premium(row, year, extraction_year)* ((1 + inflation_rate) * (extraction_year - year) if inflation_rate is not None else 1)

#     return row



def derive_yearly_amount(row, year, extraction_date, contract_start_date_column_name, written_premium_column_name, contract_end_date, number_paid_premium_column_name):
    """
        Derives the written premium per year if the data has a single row per contract (i.e. the premium reflects the full contract duration) 
        Arguments --> the df row, the year on which we want the premium value, the extraction year
                    the written premium column name on which we perform calculations 
        Returns --> the written premium per year
    """

    multiplier = row[number_paid_premium_column_name]
    amount = row[written_premium_column_name] / multiplier if multiplier > 0 else 0

    if year < row[contract_start_date_column_name].year or year > row[contract_end_date].year:
        amount = 0

    elif year == row[contract_end_date].year:

        if year < row[contract_start_date_column_name].year + multiplier:
            if row[contract_end_date] <= addYears(row[contract_start_date_column_name], multiplier - 1):
                amount = 0
        elif row[contract_end_date] <= addYears(row[contract_start_date_column_name], multiplier):
            amount = 0
        elif extraction_date < addYears(row[contract_start_date_column_name], multiplier):
            amount = 0

    return amount



# def derive_yearly_written_premium(row, year, extraction_year):

#     multiplier = 1
#     end_date = row['contract_end_date']

#     if 'contract_effective_date' in row.index and __name__ == '__main__':
#         print('Lines are at contract effective dates, i.e. you already have written premium per year. A simple groupby is sufficient to have the totals per year.\n\
# Also that means there can be several lines for a same policy corresponding to renewals.\ This entails potential duplicates and wrong summations.')
#         start_date = row['contract_effective_date']
#     else:
#         start_date = row['contract_inception_date']

#     contract_length = (end_date + timedelta(days=1) - start_date).days / 366

#     # Contract lenght is greater than 1, i.e. there might be amendments (if annual contracts) or the contract is pluri-annual
#     if contract_length > 1:

#         # If year is higher than the contract start year or greater than its end year, it means the contrat has either not yet started or already finished
#         if year < start_date.year or year >= end_date.year:
#             multiplier = 0
#         # The total amount will be assumed to be distributed uniformly over the years
#         else:
#             multiplier =  1 / contract_length

#     return row['asif_written_premium_excl_taxes'] * multiplier



def derive_annual_exposure(row, year, extraction_date, contract_start_date_column_name, contract_end_date, add_one_day):
    """
        Derives the annual exposure
        Arguments --> the df row, the year in which we calculate the exposure, the data extraction date, the contract start and end date columns names
            a flag indicating if a day must be added to the end date to derive the dates differences
        Returns --> the exposure in years
    """

    effective_date = row[contract_start_date_column_name]

    start_date = max(datetime(year, 1, 1), effective_date)
    end_date = min(extraction_date, datetime(year + 1, 1, 1) + timedelta(days=1) * add_one_day, row[contract_end_date])
    total_days = 366 if isleap(year) == True else 365
    annual_exposure = (end_date - start_date).days / total_days

    return max(0, annual_exposure)



def inflate_amounts(df, extraction_year, contract_start_date_column_name, inflation_rate, portfolio=True, row_per_each_contract_year=True, latest_premium=True, number_paid_premium_column_name='written_multiplier', occurrence_date_column_name='occurrence_date', column_to_use='written_premium_excl_taxes', min_value=None):
    """
        Derives as-if amounts due to inflation rate
        Arguments --> the df row, the data extraction year, the contracts dates columns name, the average inflation rate 
                a flag indicating if the inflation is on the portfolio side or not, if the portfolio has a unique row for the full policy contract or a row per yearly amendment,
                if the premium are the latest one or at inception (in the case of data with a row per full contract duration), the number of premiums paid at inception, the claim occurrence date column name
                which column to inflate 
        Returns --> An inflated amount
    """

    latest_premium_adjustment = 0

    if portfolio == True:
        start_years = df[contract_start_date_column_name].dt.year

        # This is the portfolio, so the year that enables to inflate is the start of the contract
        if row_per_each_contract_year == False and latest_premium == True:
            latest_premium_adjustment = df[number_paid_premium_column_name] - 1

    else:
        # In the claims side, the date that enables to inflate is the occurrence year
        start_years =  df[occurrence_date_column_name].dt.year

    inflated_values = df[column_to_use] * (1 + inflation_rate)**(extraction_year - start_years - latest_premium_adjustment)

    if min_value is not None:
        inflated_values = np.where(inflated_values < 0, 0, inflated_values)

    return inflated_values



def derive_premium_multiplier(df, contract_start_date_column_name, row_per_each_contract_year=True, actual_contract_length_column_name='actual_contract_length', actual_contract_end_date_column_name='actual_contract_end_date', annual_premium=True):
    """
        Derives the total premium for the whole coverage period. One use case will be especially for db with a single row by policy
        with the latest annual written premium even though the policyholder remained several years in the portfolio
        Arguments --> the df row, the data main contract date (if it's at effective or inception year), a boolean indicating if only the annual premium is indicated,
                    a flag indicating if the portfolio has a unique row for the full policy contract or a row per yearly amendment
        Returns --> The total premium depending on the contract length
    """ 

    def derive_length(row):
        """ Calculate the length of the contract """

        contract_length = row[actual_contract_length_column_name]

        derived_end = addYears(row[contract_start_date_column_name], contract_length - 1)

        if contract_length == 0 or row[actual_contract_end_date_column_name] == row[contract_start_date_column_name]:
            return 0
        else:
            return contract_length if derived_end < row[actual_contract_end_date_column_name] else max(1, contract_length - 1) 

    if row_per_each_contract_year == False and annual_premium == True:
        multipliers = df.apply(lambda x: derive_length(x), axis=1)
    else:
        multipliers = [1 for row in df.index]
        
    return multipliers



def change_value(df, columns=None, current_values=None, new_values=None):
    """
        Updates df columns with new values
        Arguments --> the df to work on, the columns, their respective current values to change and the new values to replace them with
                        if column is a string or a list of length one, then the current and new values are associated to
                        this unique column
        Returns --> a tuple of pandas series if several columns have to be changed, otherwise a pandas serie
    """


    # Several columns must have a value changed
    if isinstance(columns, list) and len(columns) > 1:
        results = []

        # We loop through the columns to create each time a new one with the updated value that is added in the list
        for index, column in enumerate(columns):
            results.append(np.where(df[column] == current_values[index], new_values[index], df[column]))

        # Returns a tuple as there are several columns that will get the output
        return tuple(results)

    else:
        column = columns[0] if isinstance(columns, list) == True else columns

        # Working on just one column but many of its values have to be replaced by new ones
        if isinstance(current_values, list) == True:
            # Maps the old to new values specified in the args
            mapping_values = dict(zip(current_values, new_values))
            all_current_values = df[column].unique()
            # Maps all the values as the map function needs the whole set of values ; otherwise other values would be set to nan
            all_mapping_values = {value: value if value not in current_values else mapping_values[value] for value in all_current_values}
            return df[column].map(all_mapping_values)

        # There is only one column and one value to change
        else:

            return np.where(df[column] == current_values, new_values, df[column])



def impute_mean_mode(df, columns):
    """
        Works on the dataframe columns defined in the args and returns a new df with mean and mode imputing
        for numerical/categorical variables
        Arguments --> df and columns to impute
        Returns --> df with missing values filled by mode or mean
    """

    columns_to_fill = {}

    for column in columns:

        if df[column].notnull().all() == False and df[column].notnull().any() == True:

            if df[column].dtype in ['object']:
                columns_to_fill[column] = df[column].mode()[0]
            elif df[column].dtype in ['float64', 'int64', 'int32']:
                columns_to_fill[column] = df[column].mean()

    return df.fillna(columns_to_fill)



def check_create_datetime(df, column, format='%d/%m/%Y'):
    """Checks if the column is a datetime or if it needs to be converted"""

    try:
        check = df[column].dt.year
        return df[column]
    except:
        return convert_to_datetime(df, column, format=format)

    

def convert_to_datetime(df, columns=None, format='%d/%m/%Y'):
    return df[columns].apply(pd.to_datetime, format=format)



def derive_age(df, columns):
    """
        Derives years between specified date columns and today
        Returns --> series values
    """

    today = datetime.today()
    return df[columns].apply(lambda x: today.year - x.dt.year - ((today.month < x.dt.month) & (today.day < x.dt.day)))



def derive_years_from_two_dates(df, start_date, end_date, year_number_of_days=365, extraction_date=None):
    """
        Derives days between two dates
        Arguments --> columns names for start and for end dates
        Returns --> difference in days between the two dates
    """

    if extraction_date is not None: 
        contract_length = df.apply(lambda x: (min(extraction_date, x[end_date]) + timedelta(1) - x[start_date]).days / year_number_of_days, axis=1)
    else:
        contract_length = df.apply(lambda x: (x[end_date] + timedelta(1) - x[start_date]).days / year_number_of_days, axis=1)

    return contract_length



def create_columns(df, columns):
    """
        Creates new columns - for the ones on which calculations are performed - if they are not yet in the df or if they have only null values
        Arguments --> the list of columns that are affected by calculations (claims costs, premiums etc.)
        Returns --> a new df with the new columns added
    """
    new_df = deepcopy(df)
    new_df_columns = new_df.columns

    for column in columns:
        if column not in new_df_columns or new_df[column].isnull().all() == True:
            new_df[column] = 0

    return new_df



def rename_columns(df, names_mapping):
    return df.rename(columns=names_mapping)