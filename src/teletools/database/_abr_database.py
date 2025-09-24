"""
ABR Telecom Database Query Module.

This module provides functionality to query the ABR (Agência Brasileira de Regulamentação)
Telecom database for retrieving carrier information associated with phone numbers.
It uses DuckDB for efficient querying and includes optimized performance settings
for handling large datasets.

Classes:
    QueryABRDataBase: Main class for querying carrier information from the ABR database.

Constants:
    DUCKDB_THREADS: Number of threads for DuckDB operations (default: 12).
    DUCKDB_MEMORY_LIMIT: Memory limit for DuckDB operations (default: "16GB").
"""

from datetime import date, datetime
from os.path import exists
from typing import Iterable

import duckdb
import numpy as np

from ._database_config import DUCKDB_MEMORY_LIMIT, DUCKDB_THREADS
from ._sql_queries import CREATE_TEMP_TABLE, INSERT_DATA_INTO_TEMP_TABLE, QUERY_NUMBERS


class QueryABRDataBase:
    """
    A class for querying the ABR Telecom database to retrieve carrier information for phone numbers.

    This class provides an interface to query and retrieve information about mobile carriers
    associated with specific phone numbers from the ABR Telecom database. It includes
    functionality for date-based queries and handles database connections with optimized
    performance settings.

    Attributes:
        database (str): Path to the DuckDB database file containing ABR Telecom data.

    Examples:
        >>> db = QueryABRDataBase("path/to/abr_database.db")
        >>> numbers = [11987654321, 11987654322]
        >>> results = db.query_numbers_carriers(numbers)
        >>> # Query with specific date
        >>> results = db.query_numbers_carriers(numbers, reference_date=20231201)

    Note:
        - The database file must exist before instantiating the class
        - Uses DuckDB with optimized settings (threads={DUCKDB_THREADS}, memory={DUCKDB_MEMORY_LIMIT})
    """

    def __init__(self, database):
        if exists(database):
            self.database = database
            self._database_setup()
        else:
            raise FileNotFoundError(
                f"Database file not found at: {self.database}. No new database will be created."
            )

    def _database_setup(self):
        """
        Configure and initialize the DuckDB database connection with performance settings.

        This private method establishes the database connection and applies optimized
        performance settings including thread count, memory limit, and progress bar
        configuration for efficient query execution.

        Note:
            This method is automatically called during class initialization if the
            database file exists.
        """
        with duckdb.connect(self.database) as conn:
            # Performance settings
            conn.execute(f"SET threads={DUCKDB_THREADS}")
            conn.execute(f"SET memory_limit='{DUCKDB_MEMORY_LIMIT}'")
            conn.execute("SET enable_progress_bar=false")
            print(f"Connected to existing database: {self.database}")

    def query_numbers_carriers(
        self, subscribers_numbers: Iterable[int], reference_date: int = None
    ):
        """
        Query carrier information for a list of subscriber numbers from the ABR Telecom database.
        This method queries the ABR Telecom  database to retrieve carrier information for the
        provided subscriber numbers on a specific reference date.

        Args:
            subscribers_numbers (Iterable[int]): An iterable collection (list, tuple, set, etc.)
                of subscriber phone numbers to query. Each number should be an integer.
            reference_date (int, optional): The reference date for the query in YYYYMMDD format.
                If None, defaults to today's date. Defaults to None.

        Returns:
            pandas.DataFrame: A DataFrame containing the query results with carrier information
                for the requested subscriber numbers.

        Raises:
            TypeError: If subscribers_numbers is not iterable or cannot be processed as
                an iterable of integers.
            ValueError: If reference_date is provided but not in a valid date format.

        Example:
            >>> numbers = [11987654321, 11987654322, 11987654323]
            >>> result = db.query_numbers_carriers(numbers)
            >>> result = db.query_numbers_carriers(numbers, reference_date=20231201)
        """
        # Check if it's iterable
        if not hasattr(subscribers_numbers, "__iter__"):
            raise TypeError(
                f"Expected an iterable of integers (list, tuple, set, etc.), "
                f"received {type(subscribers_numbers).__name__}"
            )

        # Convert to Numpy Array for validation (optional, uncomment if needed)
        try:
            numbers_to_query = np.array(subscribers_numbers, dtype=np.int64)
        except Exception as e:
            raise TypeError(f"Error converting to Numpy Array: {e}")

        if reference_date is None:
            # Get today's date
            reference_date = int(date.today().strftime("%Y%m%d"))
        else:
            reference_date = QueryABRDataBase.validate_date(reference_date)

        with duckdb.connect(self.database) as conn:
            conn.execute(CREATE_TEMP_TABLE)
            conn.execute(INSERT_DATA_INTO_TEMP_TABLE)
            results = conn.execute(QUERY_NUMBERS, [reference_date]).fetch_df()
        return results

    @staticmethod
    def validate_date(reference_date: int | str):
        """
        Validate and normalize a date in YYYYMMDD format.

        Args:
            reference_date (int | str): Date to validate. Can be an integer or string
                                        representing a date in YYYYMMDD format.

        Returns:
            int: The validated date as an integer in YYYYMMDD format.

        Raises:
            TypeError: If reference_date is not an int or str.
            ValueError: If the date string contains non-digit characters,
                        if the date is not exactly 8 digits long,
                        or if the date is not a valid date in YYYYMMDD format.

        Examples:
            >>> validate_date(20231225)
            20231225
            >>> validate_date("20231225")
            20231225
            >>> validate_date("2023-12-25")  # Raises ValueError
            >>> validate_date(2023125)       # Raises ValueError (7 digits)
            >>> validate_date(20231301)      # Raises ValueError (invalid date)
        """

        # Convert to string for validation
        if isinstance(reference_date, int):
            date_str = str(reference_date)
        elif isinstance(reference_date, str):
            # Check if string contains only digits
            if not reference_date.isdigit():
                raise ValueError(
                    f"Date string must contain only digits: {reference_date}"
                )
            date_str = reference_date
        else:
            raise TypeError(f"Expected int or str, got {type(reference_date)}")

        # Check length
        if len(date_str) != 8:
            raise ValueError(
                f"Date must be 8 digits (YYYYMMDD), got {len(date_str)} digits: {date_str}"
            )

        # Try to parse the date
        try:
            datetime.strptime(date_str, "%Y%m%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format YYYYMMDD: {date_str}. Error: {e}")

        return int(date_str)
