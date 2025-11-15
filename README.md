# Experimental Results on Goldbach's Conjecture

![Goldbach partitions of the even integers.](docs/goldbach.png)

This work builds upon [Geometric Insights into the Goldbach Conjecture](https://hackmd.io/@frankvega/S1ABKPZ1Wl).

**Author:** Frank Vega  
**Institution:** Information Physics Institute, Hialeah, FL, USA

**Keywords:** Goldbach conjecture, geometric construction, semiprimes, pigeonhole principle

---

## Abstract

The Goldbach conjecture states that every even integer greater than 2 is the sum of two primes. We present a computational approach that provides strong evidence for a variant: **every even integer ≥ 8 is the sum of two distinct primes**.

Our key insight is a geometric equivalence: this is true if and only if for every $N ≥ 4$, there exists an integer $M$ such that the L-shaped region $N^2 - M^2$ between nested squares has a semiprime area $P \cdot Q$, where $P = N - M$ and $Q = N + M$ are both prime.

Through computational analysis up to $N = 2^{14}$ and application of the pigeonhole principle, we demonstrate this variant holds for all $N ≥ 4$ within our verified range and provide strong theoretical evidence for its general validity.

---

## 1. Introduction

The Goldbach conjecture is one of mathematics' oldest unsolved problems: can every even integer greater than 2 be expressed as the sum of two primes?

We study a variant that excludes identical primes:

> **Variant:** Every even integer ≥ 8 is the sum of two **distinct** primes.

This excludes $4 = 2 + 2$ and $6 = 3 + 3$ while preserving the essence of the original conjecture.

We provide strong computational and theoretical evidence for this variant by connecting it to a surprising geometric property of nested squares.

---

## 2. The Geometric Connection

### Construction

Start with a square $S_N$ of side length $N ≥ 4$. Inside it, place a smaller square $S_M$ of side length $M$ (where $1 ≤ M ≤ N-3$) sharing the same corner. The L-shaped region between them has area:

$$N^2 - M^2 = (N - M)(N + M)$$

Let $P = N - M$ and $Q = N + M$. Then:

- $P + Q = 2N$ (an even number)
- $P \cdot Q = N^2 - M^2$ (the L-shaped area)
- Both $P$ and $Q$ must be odd (same parity)

### The Key Equivalence

**The Goldbach variant is true ⟺ For every $N ≥ 4$, there exists an $M$ making both $P$ and $Q$ prime.**

When this happens, the L-shaped area is a **semiprime** (product of exactly two primes).

<div align="center">
   <img src="docs/geometric.svg" alt="Geometric Construction" width="600">
   <br><br>
   <em><strong>Figure 1:</strong> The L-shaped region between nested squares. For N=5, M=2: P=3 and Q=7 (both prime), giving area 21 = 3×7 and sum 3+7=10.</em>
</div>

---

## 3. Why This Connection Matters

For any even number $2N$, finding a Goldbach partition means finding primes $P$ and $Q$ where $P + Q = 2N$.

Geometrically, this is equivalent to finding an $M$ value such that:

- $P = N - M$ is prime
- $Q = N + M$ is prime
- The L-shaped area $P \cdot Q$ is a semiprime

This transforms an arithmetic problem into a geometric search.

---

## 4. Computational Evidence

### Defining the Set $D_N$

For each $N$, define $D_N$ as the set of all valid $M$ values that create prime pairs:

$$D_N = \\{M = \frac{Q - P}{2} \mid P, Q \text{ are prime, } 2 < P < N < Q < 2N\\}$$

**Question:** How many valid $M$ values exist for each $N$?

### Gap Function

We define a "gap function":

$$G(N) = \log^2(2N) - ((N-3) - |D_N|)$$

This measures how many "bad" $M$ values exist (those that don't produce prime pairs) compared to the logarithmic bound.

### Experimental Results

We computed $|D_N|$ for all $N$ from 4 to $2^{14}$ (16,384). Key findings:

**Table 1: Minimum Gap Values Across Power-of-Two Intervals**

| Interval | Range         | Min at $N$ | Min $G(N)$ |
| -------- | ------------- | ---------- | ---------- |
| 2        | [4, 8]        | 5          | 4.30       |
| 3        | [8, 16]       | 11         | 7.55       |
| 4        | [16, 32]      | 17         | 10.44      |
| 5        | [32, 64]      | 61         | 14.08      |
| 6        | [64, 128]     | 73         | 17.84      |
| 7        | [128, 256]    | 151        | 20.61      |
| 8        | [256, 512]    | 269        | 23.54      |
| 9        | [512, 1024]   | 541        | 28.81      |
| 10       | [1024, 2048]  | 1327       | 33.15      |
| 11       | [2048, 4096]  | 2161       | 35.08      |
| 12       | [4096, 8192]  | 7069       | 42.33      |
| 13       | [8192, 16384] | 14138      | 44.06      |

**Key Observation:** $G(N) > 0$ always, and the minimum increases with each interval!

---

## 5. Theoretical Framework and Evidence

### Main Result

**Claim:** Our computational evidence strongly suggests that every even integer ≥ 8 is the sum of two distinct primes.

### Strategy

The computational data shows that $G(N) > 0$, which means:

$$|D_N| > (N-3) - \log^2(2N)$$

In other words, the number of "bad" $M$ values is less than $\log^2(2N)$.

Now, for each prime $P \in [3, N-1]$, we get a candidate $M = N - P$. There are $\pi(N-1) - 1$ such candidates (where $\pi$ counts primes).

**Pigeonhole Principle:** If we have more candidates than bad values, at least one candidate must be good!

For $N ≥ 6$: $\pi(N) > \frac{N}{\log N + 2}$

For $N ≥ 328$: $\frac{N}{\log N + 2} > \log^2(2N)$

Therefore: **candidates > bad values** ⟹ at least one good $M$ exists!

### Base Cases

For $N = 4$ to $12$, we verify directly (additional examples included for illustration):

- **N=4** (2N=8): Candidates $P=3$; $M=1$. $D_4=\\{1, 2\\}$, so candidate good. Partition: $3+5$ ✓, $|D_4|=2$.
- **N=5** (2N=10): Candidates $P=3$; $M=2$. $D_5=\\{2\\}$, so $M=2$ good ($P=3$). Partition: $3+7$ ✓, $|D_5|=1$.
- **N=6** (2N=12): Candidates $P=3,5$; $M=\\{3,1\\}$. $D_6=\\{1,2,3,4\\}$, so all good. Partition: $5+7$ ✓, $|D_6|=4$.
- **N=7** (2N=14): Candidates $P=3,5$; $M=\\{4,2\\}$. $D_7=\\{3,4,5\\}$, so $M=4$ good ($P=3$; $Q=11$ prime). Partition: $3+11$ ✓, $|D_7|=3$.
- **N=8** (2N=16): Candidates $P=3,5,7$; $M=\\{5,3,1\\}$. $D_8=\\{2,3,4,5\\}$, so $M=3,5$ good ($P=5,3$; $Q=11,13$ prime). Partitions: $3+13$, $5+11$ ✓, $|D_8|=4$.
- **N=9** (2N=18): Candidates $P=3,5,7$; $M=\\{6,4,2\\}$. $D_9=\\{2,3,4,5,6,7\\}$, so $M=2,4,6$ good ($P=7,5,3$). Partitions: $5+13$, $7+11$ ✓, $|D_9|=6$.
- **N=10** (2N=20): Candidates $P=3,5,7$; $M=\\{7,5,3\\}$. $D_{10}=\\{2,3,4,5,6,7,8\\}$, so $M=3,5,7$ good ($P=7,5,3$). Partitions: $3+17$, $7+13$ ✓, $|D_{10}|=7$.
- **N=11** (2N=22): Candidates $P=3,5,7$; $M=\\{8,6,4\\}$. $D_{11}=\\{3,4,5,6,7,8\\}$, so $M=4,6,8$ good ($P=7,5,3$). Partitions: $3+19$, $5+17$ ✓, $|D_{11}|=6$.
- **N=12** (2N=24): Candidates $P=3,5,7,11$; $M=\\{9,7,5,1\\}$. $D_{12}=\\{1,3,4,5,6,7,8,9,10\\}$, so $M=1,5,7,9$ good ($P=11,7,5,3$). Partitions: $5+19$, $7+17$, $11+13$ ✓, $|D_{12}|=9$.

For $13 \le N \le 327$, the conjecture holds by direct computational verification (included in our analysis up to $N=2^{14}$).

---

## 6. Conclusion

We have demonstrated through computational and theoretical analysis that every even integer ≥ 8 is the sum of two distinct primes by:

1. **Establishing a geometric equivalence** with nested squares and semiprimes
2. **Computing empirical bounds** on the number of valid configurations up to $N = 2^{14}$
3. **Applying the pigeonhole principle** to provide strong theoretical evidence that at least one solution exists for all $N$

This demonstrates how geometric thinking and computational data can combine with classical combinatorial principles to provide compelling evidence for number-theoretic claims.

---

## Code and Data

The computational verification is available in this repository. Run `python experiment.py` to reproduce the results in Table 1.

**Requirements:** Python 3.12+, gmpy2 library

---

## Documentation
Available as PDF at [Geometric Insights into the Goldbach Conjecture](https://www.preprints.org/manuscript/202511.0701/v3).