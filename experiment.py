"""
Goldbach experiment (variant: every even integer >= 8 is the sum of two
distinct primes), following the definitions of the README.

For each N with 4 <= N <= 2^K (default K = 14) it computes:

  D_N   = { M = (Q - P)/2 : P, Q prime, 2 < P < N < Q < 2N } ∩ {1, ..., N-3}
  S_N   = { M in {1, ..., N-3} : N - M and N + M are both prime }
          (the M values that give a Goldbach partition 2N = P + Q, P < Q)
  C_N   = { N - P : P prime, 3 <= P <= N-1 },   |C_N| = pi(N-1) - 1

  G(N)   = log^2(2N) - ((N-3) - |D_N|)      (log = natural logarithm)
  G_S(N) = log^2(2N) - ((N-3) - |S_N|)

and reports:

  1. Table 1: minimum of G(N) on the disjoint intervals
     [4, 8], (8, 16], (16, 32], ..., (2^(K-1), 2^K]
     (and the same table for G_S).
  2. Whether every N in range has a partition (S_N non-empty).
  3. For how many N the intersection C_N ∩ D_N contains an M with N + M
     composite (a member of D_N that does not give a partition), with the
     first examples.
  4. The pigeonhole count check |C_N| > (N-3) - |D_N| for every N in range.
  5. The thresholds N_0 for the inequalities
        N/(log N + 2)     > log^2(2N)
        N/(log N + 2) - 2 > log^2(2N)
     (the second one covers |C_N| = pi(N-1) - 1 >= pi(N) - 2),
     and a check of pi(x) > x/(log x + 2) for 2 <= x <= 2^(K+1).
  6. C_N, D_N, S_N and C_N ∩ D_N for the base cases N = 4, ..., 12.

Only the Python standard library is needed (Python 3.10+).

Usage:
    python experiment.py            # K = 14
    python experiment.py --max-exp 12
"""

import argparse
import bisect
import logging
import math
import time


LOG_FILE = "experimental_results.log"


def setup_logger(log_file=LOG_FILE):
    """Logger that writes to the log file and to the console."""
    logger = logging.getLogger("goldbach")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def sieve(limit):
    """is_prime[k] for 0 <= k <= limit."""
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0:2] = b"\x00\x00"
    for i in range(2, math.isqrt(limit) + 1):
        if is_prime[i]:
            is_prime[i * i::i] = bytearray(len(range(i * i, limit + 1, i)))
    return is_prime


def fmt_set(s):
    return "{" + ",".join(str(x) for x in sorted(s)) + "}"


def interval_index(n):
    """Interval k: [4, 8] for k = 2, (2^k, 2^(k+1)] for k >= 3."""
    if n <= 8:
        return 2
    return (n - 1).bit_length() - 1


def interval_label(k):
    if k == 2:
        return "[4, 8]"
    return f"({2 ** k}, {2 ** (k + 1)}]"


def first_threshold(f, start, stop):
    """Smallest x0 in [start, stop] with f(x) True for all x0 <= x <= stop."""
    last_fail = start - 1
    for x in range(start, stop + 1):
        if not f(x):
            last_fail = x
    return last_fail + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-exp", type=int, default=14,
                        help="compute up to N = 2^MAX_EXP (default 14)")
    parser.add_argument("--threshold-limit", type=int, default=10 ** 6,
                        help="search range for the analytic thresholds (default 10^6)")
    args = parser.parse_args()

    log = setup_logger()
    K = args.max_exp
    N_MAX = 2 ** K
    t0 = time.time()
    log.info(f"Starting: 4 <= N <= 2^{K} = {N_MAX}")

    is_prime = sieve(2 * N_MAX)
    primes = [p for p in range(2 * N_MAX + 1) if is_prime[p]]

    # Bit mask of all primes: bit p set  <=>  p prime.
    all_mask = 0
    for p in primes:
        all_mask |= 1 << p

    # Bits at even positions, used to read M = d/2 from differences d.
    even_mask = int("01" * (N_MAX + 2), 2)

    min_G = {}       # k -> (G, N)
    min_GS = {}      # k -> (G_S, N)
    no_partition = []
    pigeonhole_fail = []
    spurious_count = 0
    spurious_examples = []
    base_cases = []

    current_k = None
    for N in range(4, N_MAX + 1):
        # Primes P with 2 < P < N, primes Q with N < Q < 2N.
        small = primes[1:bisect.bisect_left(primes, N)]          # primes[0] = 2
        b_mask = (all_mask >> (N + 1)) << (N + 1)
        b_mask &= (1 << (2 * N)) - 1                           # N < Q < 2N

        # Differences d = Q - P as bits.
        diff = 0
        for p in small:
            diff |= b_mask >> p

        # D_N: M = d/2 with 1 <= M <= N-3, i.e. even d with 2 <= d <= 2N-6.
        range_mask = ((1 << (2 * N - 5)) - 1) & ~0b11
        d_bits = diff & even_mask & range_mask
        size_D = d_bits.bit_count()

        # S_N and C_N (candidates come from primes 3 <= P <= N-1).
        size_S = 0
        spurious_here = []
        for p in small:
            M = N - p
            if M > N - 3:
                continue
            good = bool(is_prime[N + M])
            if good:
                size_S += 1
            elif (d_bits >> (2 * M)) & 1:
                spurious_here.append(M)
        size_C = len(small)

        log2N = math.log(2 * N) ** 2
        bad_D = (N - 3) - size_D
        bad_S = (N - 3) - size_S
        G = log2N - bad_D
        GS = log2N - bad_S

        k = interval_index(N)
        if k not in min_G or G < min_G[k][0]:
            min_G[k] = (G, N)
        if k not in min_GS or GS < min_GS[k][0]:
            min_GS[k] = (GS, N)

        if size_S == 0:
            no_partition.append(N)
        if not size_C > bad_D:
            pigeonhole_fail.append(N)
        if spurious_here:
            spurious_count += 1
            if len(spurious_examples) < 10:
                spurious_examples.append((N, sorted(spurious_here)))

        if N <= 12:
            D = {j // 2 for j in range(2, 2 * N - 5, 2) if (d_bits >> j) & 1}
            C = {N - p for p in small}
            S = {N - p for p in small if is_prime[2 * N - p]}
            base_cases.append((N, C, D, S))

        if k != current_k:
            current_k = k
            log.info(f"  interval {k} {interval_label(k)} ... ({time.time() - t0:.1f} s)")

    # ---------------------------------------------------------------- report
    log.info("")
    log.info("Table 1: minimum of G(N) = log^2(2N) - ((N-3) - |D_N|) per interval")
    log.info("| Interval | Range | Min at $N$ | Min $G(N)$ |")
    log.info("| :--- | :--- | :--- | :--- |")
    for k in sorted(min_G):
        g, n = min_G[k]
        log.info(f"| {k} | ${interval_label(k)}$ | {n} | {g:.2f} |   (G = {g:.6f})")

    log.info("")
    log.info("Same table for G_S(N) = log^2(2N) - ((N-3) - |S_N|), S_N = Goldbach M values")
    for k in sorted(min_GS):
        g, n = min_GS[k]
        log.info(f"| {k} | ${interval_label(k)}$ | {n} | {g:.2f} |")

    log.info("")
    log.info(f"N without a partition into two distinct primes: {no_partition or 'none'}")
    log.info(f"N with |C_N| <= (N-3) - |D_N| (pigeonhole count fails): "
             f"{len(pigeonhole_fail)}" + (f", first: {pigeonhole_fail[:10]}" if pigeonhole_fail else ""))
    log.info(f"N where C_N ∩ D_N contains an M with N+M composite: {spurious_count}")
    for n, ms in spurious_examples:
        log.info(f"  N = {n}: M = {ms}")

    log.info("")
    L = args.threshold_limit
    f1 = lambda x: x / (math.log(x) + 2) > math.log(2 * x) ** 2
    f2 = lambda x: x / (math.log(x) + 2) - 2 > math.log(2 * x) ** 2
    log.info(f"Smallest N_0 with N/(log N + 2) > log^2(2N) for all N_0 <= N <= {L}: "
             f"{first_threshold(f1, 2, L)}")
    log.info(f"Smallest N_0 with N/(log N + 2) - 2 > log^2(2N) for all N_0 <= N <= {L}: "
             f"{first_threshold(f2, 2, L)}")

    pi = 0
    pi_fail = []
    for x in range(2, 2 * N_MAX + 1):
        if is_prime[x]:
            pi += 1
        if not pi > x / (math.log(x) + 2):
            pi_fail.append(x)
    log.info(f"x in [2, {2 * N_MAX}] with pi(x) <= x/(log x + 2): {pi_fail or 'none'}")

    log.info("")
    log.info("Base cases (C_N, D_N, S_N, C_N ∩ D_N):")
    for N, C, D, S in base_cases:
        log.info(f"  N = {N}: C = {fmt_set(C)}, D = {fmt_set(D)}, "
                 f"S = {fmt_set(S)}, C∩D = {fmt_set(C & D)}")

    log.info("")
    log.info(f"Finished in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
