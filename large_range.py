r"""
Large-range computation for the half-difference set E_N and the centered
count R(2N).

Definitions (as in the paper), for N >= 4:
    A_N = {1, ..., N-3}
    E_N = { (Q-P)/2 in A_N : P, Q prime, 2 < P < N < Q < 2N }
    H(N) = log^2(2N) - ((N-3) - |E_N|)
    R(2N) = #{ P prime : 3 <= P < N, 2N - P prime }        (= |C_N ∩ D_N|)

The script computes, for every N with 4 <= N <= N_max (default 10^6):

  1. |E_N| and H(N), by maintaining the counts
         cnt[d] = #{(P, Q) : P prime, 2 < P < N < Q < 2N, Q prime, Q - P = d}
     incrementally as N grows; E_N corresponds to the even d with
     2 <= d <= 2N-6 and cnt[d] > 0.
  2. The minimum of H(N), the maximum of |A_N \ E_N| = (N-3) - |E_N|, and
     the minimum of |E_N|/N on every dyadic interval [4,8], (2^m, 2^(m+1)].
  3. For the N attaining the minimum of H(N) on each interval, the
     missing values A_N \ E_N themselves.
  4. R(2N) for every N, from one FFT of the prime indicator, and the ratio
         R(2N) / HL(2N),
         HL(2N) = omega * prod_{p | N, p > 2} (p-1)/(p-2) * I(2N),
         I(n)   = integral_2^{n-2} dt / (log t * log(n-t)),
     omega = prod_{p > 2} (1 - 1/(p-1)^2), with I computed by 64-point
     Gauss-Legendre quadrature. Per interval: min, max and mean of the ratio,
     and min R(2N).

Requirements: Python 3.10+ and NumPy.

Usage:
    python car/large_range.py                    # N_max = 10^6
    python car/large_range.py --max-n 10000000   # about an hour or more
"""

import argparse
import logging
import math
import os
import time

import numpy as np


HERE = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(HERE, "large_range_results.log")


def setup_logger():
    logger = logging.getLogger("large_range")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def sieve(limit):
    s = np.ones(limit + 1, dtype=bool)
    s[:2] = False
    for i in range(2, math.isqrt(limit) + 1):
        if s[i]:
            s[i * i::i] = False
    return s


def interval_index(n):
    return 2 if n <= 8 else (n - 1).bit_length() - 1


def interval_label(k):
    return "[4, 8]" if k == 2 else f"(2^{k}, 2^{k + 1}]"


def goldbach_ordered_counts(is_prime, n_max):
    """g[n] = #{(p, q) : p, q odd primes, p + q = n} for n <= 2 n_max."""
    ind = is_prime[: 2 * n_max + 1].astype(np.float64)
    ind[2] = 0.0
    size = 1 << (len(ind) * 2 - 1).bit_length()
    f = np.fft.rfft(ind, size)
    g = np.fft.irfft(f * f, size)[: 2 * n_max + 1]
    return np.rint(g).astype(np.int64)


def hl_integral(n_values):
    """I(n) = integral_2^{n-2} dt / (log t log(n - t)) by Gauss-Legendre."""
    x, w = np.polynomial.legendre.leggauss(64)
    out = np.empty(len(n_values))
    chunk = 20000
    for s in range(0, len(n_values), chunk):
        n = n_values[s:s + chunk].astype(np.float64)[:, None]
        a, b = 2.0, n - 2.0
        t = (b - a) / 2.0 * x[None, :] + (b + a) / 2.0
        f = 1.0 / (np.log(t) * np.log(n - t))
        out[s:s + chunk] = ((b - a) / 2.0)[:, 0] * (f @ w)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-n", type=int, default=10 ** 6)
    args = parser.parse_args()
    n_max = args.max_n

    log = setup_logger()
    t0 = time.time()
    log.info(f"Starting: 4 <= N <= {n_max}")

    is_prime = sieve(2 * n_max + 2)
    odd = np.nonzero(is_prime)[0]
    odd = odd[odd > 2].astype(np.int64)

    # ---------------------------------------------------------------- E_N
    # State for the current N: L = odd primes < N, U = primes in (N, 2N).
    cnt = np.zeros(2 * n_max + 2, dtype=np.int32)
    nonzero = 0

    def add_pairs(diffs):
        nonlocal nonzero
        nonzero += int(np.count_nonzero(cnt[diffs] == 0))
        cnt[diffs] += 1

    def remove_pairs(diffs):
        nonlocal nonzero
        cnt[diffs] -= 1
        nonzero -= int(np.count_nonzero(cnt[diffs] == 0))

    # Initial N = 4: L = {3}, U = {5, 7}.
    L = [3]
    L_arr = np.array(L, dtype=np.int64)
    U = {5, 7}
    for q in U:
        add_pairs(q - L_arr)

    size_E = np.zeros(n_max + 1, dtype=np.int64)

    for N in range(4, n_max + 1):
        if N > 4:
            # Pass from N-1 to N.
            m = N - 1
            # Q = N leaves U (it is no longer > N).
            if is_prime[N] and N in U:
                U.discard(N)
                remove_pairs(N - L_arr)
            # P = N - 1 joins L (it is now < N).
            if m > 2 and is_prime[m]:
                if U:
                    u = np.fromiter(U, dtype=np.int64)
                    add_pairs(u - m)
                L.append(m)
                L_arr = np.append(L_arr, m)
            # Q = 2N - 2 and 2N - 1 join U (Q < 2N); 2N - 2 is even.
            for q in (2 * N - 1,):
                if is_prime[q]:
                    U.add(q)
                    add_pairs(q - L_arr)
        # E_N: even d with 2 <= d <= 2N-6; the only larger possible d is 2N-4.
        e = nonzero - (1 if cnt[2 * N - 4] > 0 else 0)
        size_E[N] = e
        if (N & (N - 1)) == 0:
            log.info(f"  N = {N} ... ({time.time() - t0:.1f} s)")

    log.info(f"|E_N| done ({time.time() - t0:.1f} s)")

    Ns = np.arange(4, n_max + 1)
    E = size_E[4:]
    H = np.log(2.0 * Ns) ** 2 - ((Ns - 3) - E)
    missing = (Ns - 3) - E
    ratio_E = E / Ns

    # ---------------------------------------------------------------- R(2N)
    g = goldbach_ordered_counts(is_prime, n_max)
    R = (g[2 * Ns] - is_prime[Ns].astype(np.int64)) // 2
    log.info(f"R(2N) done ({time.time() - t0:.1f} s)")

    # Singular factor prod_{p | N, p > 2} (p-1)/(p-2) for every N.
    sing = np.ones(n_max + 1)
    for p in odd[odd <= n_max]:
        sing[p::p] *= (p - 1) / (p - 2)
    omega = float(np.prod(1.0 - 1.0 / (odd.astype(np.float64) - 1.0) ** 2))
    HL = omega * sing[Ns] * hl_integral(2 * Ns)
    ratio_R = R / HL
    log.info(f"omega (primes up to 2 N_max) = {omega:.10f}")
    log.info(f"Hardy-Littlewood values done ({time.time() - t0:.1f} s)")

    # ---------------------------------------------------------------- report
    ks = np.array([interval_index(int(n)) for n in Ns])
    log.info("")
    log.info("Table A: H(N), the exceptional set A_N \\ E_N, and |E_N|/N per interval")
    log.info("| m | Range | N at min H | min H(N) | max |A_N \\ E_N| | log^2(2N) at that N | min |E_N|/N |")
    argmins = []
    for k in sorted(set(ks.tolist())):
        sel = np.nonzero(ks == k)[0]
        i = sel[np.argmin(H[sel])]
        j = sel[np.argmax(missing[sel])]
        argmins.append(int(Ns[i]))
        log.info(f"| {k} | {interval_label(k)} | {Ns[i]} | {H[i]:.6f} | {missing[j]} (N = {Ns[j]}) | "
                 f"{math.log(2 * Ns[j]) ** 2:.2f} | {ratio_E[sel].min():.6f} |")
    log.info(f"H(N) > 0 for every N in range: {bool((H > 0).all())}"
             + ("" if (H > 0).all() else f"; first N with H(N) <= 0: {int(Ns[np.argmax(H <= 0)])}"))
    log.info(f"min |E_N|/N over 3275 <= N <= {n_max}: "
             f"{ratio_E[Ns >= 3275].min():.6f}" if n_max >= 3275 else "")

    log.info("")
    log.info("Missing values A_N \\ E_N at the N attaining min H(N) on each interval:")
    for N in argmins:
        P = odd[odd < N]
        Q = odd[(odd > N) & (odd < 2 * N)]
        size = 1 << (4 * N).bit_length()
        a = np.zeros(2 * N + 1); a[Q] = 1.0
        b = np.zeros(2 * N + 1); b[N - P] = 1.0          # reversed lower primes
        c = np.rint(np.fft.irfft(np.fft.rfft(a, size) * np.fft.rfft(b, size), size)).astype(np.int64)
        # c[Q + N - P] counts pairs with Q - P = d; d = index - N.
        present = set((np.nonzero(c > 0)[0] - N).tolist())
        miss = [M for M in range(1, N - 2) if 2 * M not in present]
        log.info(f"  N = {N}: |A_N \\ E_N| = {len(miss)}, missing M = {miss[:40]}"
                 + (" ..." if len(miss) > 40 else "")
                 + (f", N-3-M = {[N - 3 - M for M in miss[:40]]}" if miss else ""))

    log.info("")
    log.info("Table B: R(2N) and the ratio R(2N)/HL(2N) per interval")
    log.info("| m | Range | min R(2N) (at N) | min ratio | max ratio | mean ratio |")
    for k in sorted(set(ks.tolist())):
        sel = np.nonzero(ks == k)[0]
        i = sel[np.argmin(R[sel])]
        log.info(f"| {k} | {interval_label(k)} | {R[i]} ({Ns[i]}) | {ratio_R[sel].min():.4f} | "
                 f"{ratio_R[sel].max():.4f} | {ratio_R[sel].mean():.4f} |")
    log.info(f"R(2N) >= 1 for every N in range: {bool((R >= 1).all())}")

    # ---------------------------------------------------------------- Table C
    # Missing values forced by the two gap obstructions of the paper:
    #   low block : M = 1, ..., (p+ - p-)/2 - 1     (p- < N < p+ consecutive primes)
    #   top block : M = (q-3)/2 + 1, ..., N - 3     (q = largest prime below 2N)
    allp = np.nonzero(is_prime)[0]
    p_minus = allp[np.searchsorted(allp, Ns, side="left") - 1]
    p_plus = allp[np.searchsorted(allp, Ns, side="right")]
    q = allp[np.searchsorted(allp, 2 * Ns, side="left") - 1]
    low = np.clip((p_plus - p_minus) // 2 - 1, 0, Ns - 3)
    top_start = (q - 3) // 2 + 1
    top = np.maximum(0, (Ns - 3) - top_start + 1)
    overlap = np.maximum(0, low - top_start + 1)
    forced = low + top - overlap
    unexplained = missing - forced
    log.info("")
    log.info("Table C: missing values forced by the gap obstructions per interval")
    log.info("| m | Range | max |A_N \\ E_N| | max forced | max unexplained (at N) | mean unexplained "
             "| share of N with none unexplained | sum forced / sum missing |")
    for k in sorted(set(ks.tolist())):
        sel = np.nonzero(ks == k)[0]
        i = sel[np.argmax(unexplained[sel])]
        tot = missing[sel].sum()
        share = forced[sel].sum() / tot if tot > 0 else float("nan")
        log.info(f"| {k} | {interval_label(k)} | {missing[sel].max()} | {forced[sel].max()} | "
                 f"{unexplained[i]} ({Ns[i]}) | {unexplained[sel].mean():.3f} | "
                 f"{(unexplained[sel] == 0).mean():.4f} | {share:.4f} |")
    log.info(f"forced <= missing for every N in range (consistency check): {bool((unexplained >= 0).all())}")
    big = np.nonzero(unexplained > np.log(2.0 * Ns) ** 2)[0]
    log.info(f"N with more than log^2(2N) unexplained missing values: {len(big)}")
    gap_big = np.nonzero(forced >= np.log(2.0 * Ns) ** 2)[0]
    log.info(f"N with at least log^2(2N) forced missing values: {len(gap_big)}")
    ratio_u = unexplained / np.log(2.0 * Ns) ** 2
    j = int(np.argmax(ratio_u[Ns >= 1000])) + int(np.argmax(Ns >= 1000))
    log.info(f"max unexplained / log^2(2N) over 1000 <= N <= {n_max}: {ratio_u[j]:.4f} at N = {Ns[j]}")

    log.info("")
    log.info(f"Finished in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
