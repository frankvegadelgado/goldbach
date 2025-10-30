import gmpy2
import math
import logging


class FileLogger:
    """
    A simple logger class that logs messages to a file and prints them to console.
    """

    def __init__(self, log_file="experimental_results.log", log_level=logging.INFO):
        """
        Initializes the FileLogger with an optional log file name and log level.

        Args:
            log_file (str, optional): The filename of the log file. Defaults to "experimental_results.log".
            log_level (int, optional): The logging level. Defaults to logging.INFO.
        """
        logging.basicConfig(
            filename=log_file,
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def info(self, msg, *args, **kwargs):
        """
        Logs an informational message to the file and prints it to console.

        Args:
            msg (str): The message to be logged.
            *args: Additional arguments to be formatted with the message.
            **kwargs: Additional keyword arguments (ignored for file logging).
        """
        formatted_msg = msg.format(*args)
        self.logger.info(formatted_msg)
        print(formatted_msg)


def generate_primes_up_to(limit):
    """
    Generate all prime numbers less than or equal to the given limit using gmpy2.

    Args:
        limit (int): The upper limit for prime generation.

    Returns:
        list: A list of prime numbers <= limit.
    """
    primes = []
    p = gmpy2.mpz(3)
    while p <= limit:
        primes.append(p)
        p = gmpy2.next_prime(p)
    return primes


def generate_primes_in_interval(start, end):
    """
    Generate all prime numbers strictly greater than start and less than end using gmpy2.

    Args:
        start (int): The lower bound (exclusive).
        end (int): The upper bound (exclusive).

    Returns:
        list: A list of prime numbers in (start, end).
    """
    primes_in_interval = []
    p = gmpy2.next_prime(start)
    while p < end:
        primes_in_interval.append(p)
        p = gmpy2.next_prime(p)
    return primes_in_interval


def compute_differences(primes_in_interval, all_primes, n):
    """
    Compute the set of unique values (p - q) // 2 for p in primes_in_interval and q in all_primes.

    Args:
        primes_in_interval (list): List of primes in the current interval.
        all_primes (list): List of all primes up to the current n.
        n (int): An integer between the intervals
        
    Returns:
        set: Set of unique difference values.
    """
    diff = set()
    for p in primes_in_interval:
        for q in all_primes:
            value = (p - q) // 2
            if q == n or value in diff:
                continue
            diff.add(value)
    return diff


def test(min_exp, max_exp):
    """
    Main execution function for the prime gap experiment.
    Tests a mathematical claim on prime gaps from 2^min_exp to 2^max_exp.
    """
    # Validate the Input
    if not isinstance(min_exp, int) or not isinstance(max_exp, int):
        raise ValueError("Input must be two integers.")
    if min_exp <= 0 or max_exp <= 0:
        raise ValueError("Input must be two natural numbers.")
    if min_exp >= max_exp:
        raise ValueError(f"Invalid arguments: The first input integer value must be lesser than second one.")
    
    # Initialize logger
    printer = FileLogger()

    # Experiment parameters
    upper_bound = 2 ** max_exp
    start = 2 ** min_exp
    ngap = 0
    min_gap = 2 * start
    log2 = min_exp

    printer.info(f'Starting test for 2^{min_exp} to 2^{max_exp}')

    # Generate initial primes <= start
    primes = generate_primes_up_to(start)

    # Generate initial primes in (start, 2*start)
    primes_in_interval = generate_primes_in_interval(start, 2 * start)

    # Next prime after the initial interval
    r = gmpy2.next_prime(2 * start - 1) if primes_in_interval else gmpy2.next_prime(start)

    # Main iteration over n from start to upper_bound
    for n in range(start, upper_bound + 1):
        # Add the next prime if n matches the smallest in the interval
        if primes_in_interval and primes_in_interval[0] == n:
            primes.append(primes_in_interval[0])
            del primes_in_interval[0]

        # Generate additional primes if needed (primes < 2*n)
        while r < 2 * n:
            primes_in_interval.append(r)
            r = gmpy2.next_prime(r)

        # Compute set of differences {(p - q)/2} for p in primes_in_interval, q in primes
        D = compute_differences(primes_in_interval, primes, n)

        # Test the experimental claim: gap = (log(2n))^2 - (n - len(D))
        log_square = (math.log(2 * n)) ** 2
        gap = log_square - (n - len(D))

        if gap <= 0:
            printer.info(f'The Experimental Result failed for {n}: {n - len(D)} >= {log_square}')
            raise RuntimeError("The Experimental Result failed.")
        elif min_gap > gap:
            ngap = n
            min_gap = gap

        # Logging progress when crossing powers of 2
        current_log2 = math.floor(math.log2(n))
        if current_log2 > log2:
            log2 = current_log2
            printer.info(
                f'Minimum gap between 2^{log2-1} and 2^{log2} for N = {ngap} with G(N) = {min_gap}'
            )
            min_gap = 2 * n

    printer.info(f'Finished test for 2^{min_exp} to 2^{max_exp}')


if __name__ == "__main__":
    test(2, 14)