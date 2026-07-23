"""
SNM (Static Noise Margin) extractor for 6T SRAM HOLD butterfly curves.

INPUT FILES (produced by ngspice `wrdata` in your .control block):
  curve_hold_1.txt  -> dc1 sweep data
  curve_hold_2.txt  -> dc2 sweep data

Each file has 4 columns because ngspice duplicates the swept node's
voltage when you request that same node as one of your output vectors.
Crucially, the duplicate can land in DIFFERENT column positions
depending on which vector you swept and which you listed first in
`wrdata file.txt vecA vecB`:

  File 1 (sweep on Q1, request v(q1) v(qb1)):
      col0=sweep, col1=v(q1) [dup], col2=v(q1) [dup], col3=v(qb1)  <- real y in LAST col

  File 2 (sweep on Q2, request v(qb2) v(q2)):
      col0=sweep, col1=v(qb2) [real y], col2=v(q2) [dup], col3=v(q2) [dup]  <- real y in col1!

The ORIGINAL script only checked the "duplicates in col0,1,2" pattern
and always returned the last column as y. That's wrong for File 2's
layout above (duplicates are in col0,2,3 -- not col0,1,2), so it would
silently grab the WRONG column for curve B, distorting it and shrinking
the inscribed squares. This version checks for both duplicate patterns
explicitly so it picks the correct "real" column regardless of layout.

METHOD: 45-degree rotation technique for max inscribed square.
For a given lobe, rotate both curves by -45 degrees. The largest square
with sides parallel to the original axes that fits between the curves
has a side length = (max vertical separation between rotated curves
within that lobe) / sqrt(2).

OUTPUT:
  - SNM_0, SNM_1 printed in mV
  - snm_butterfly_plot.png showing both curves + the two inscribed
    squares drawn to scale.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.interpolate import interp1d

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
DC1_FILE = 'curve_hold_1.txt'
DC2_FILE = 'curve_hold_2.txt'
VDD = 1.8


def load_wrdata(path, tol=1e-9):
    """Robustly load ngspice `wrdata` output with 4 columns, where one
    of the columns is a duplicate of the sweep value (col0) and the
    OTHER non-duplicate column is the real y-data we want.

    Handles BOTH possible duplicate layouts:
      Pattern A: col0 == col1 == col2  -> real y is col3
      Pattern B: col0 == col2 == col3  -> real y is col1
    (and falls back gracefully if neither matches exactly.)
    """
    data = np.loadtxt(path)
    if data.ndim == 1:
        data = data.reshape(1, -1)

    ncols = data.shape[1]
    x = data[:, 0]  # the sweep variable is always col0

    if ncols >= 4:
        col0, col1, col2, col3 = data[:, 0], data[:, 1], data[:, 2], data[:, 3]

        pattern_A = np.allclose(col0, col1, atol=tol) and np.allclose(col1, col2, atol=tol)
        pattern_B = np.allclose(col0, col2, atol=tol) and np.allclose(col2, col3, atol=tol)

        if pattern_A and not pattern_B:
            y = col3
        elif pattern_B and not pattern_A:
            y = col1
        elif pattern_A and pattern_B:
            # degenerate (e.g. all columns equal) -- shouldn't normally
            # happen for butterfly data; default to last column
            y = col3
        else:
            # Neither clean duplicate pattern matched. Pick whichever
            # non-sweep column has the LARGEST dynamic range, since
            # the real signal varies a lot while a sweep-duplicate is
            # by definition identical to col0.
            candidates = {1: col1, 2: col2, 3: col3}
            ranges = {k: np.ptp(v) for k, v in candidates.items()}
            # exclude columns that are near-identical to col0 (likely dup)
            non_dup = {k: v for k, v in ranges.items()
                       if not np.allclose(candidates[k], col0, atol=tol)}
            best_col = max(non_dup, key=non_dup.get) if non_dup else 3
            y = candidates[best_col]
    else:
        y = data[:, 2]

    return x, y


def find_crossings(x_common, yA, yB, vdd=1.8, edge_margin=0.05):
    diff = yA - yB
    sign = np.sign(diff)
    idx = np.where(np.diff(sign) != 0)[0]
    crossings = []
    for i in idx:
        x0, x1 = x_common[i], x_common[i + 1]
        d0, d1 = diff[i], diff[i + 1]
        if d1 == d0:
            continue
        xc = x0 - d0 * (x1 - x0) / (d1 - d0)
        if xc < edge_margin or xc > (vdd - edge_margin):
            continue
        crossings.append(xc)
    return np.array(crossings)


def max_inscribed_square_side(xA, yA, xB, yB, x_lo, x_hi, n=400):
    """
    Largest axis-aligned square inscribed strictly between curve A and
    curve B, restricted to x in [x_lo, x_hi].

    IMPORTANT: this is a brute-force search over candidate (x_start,
    side) pairs, NOT the 45-degree-rotation max-gap shortcut used
    previously. The rotation shortcut only gives the correct answer
    when the point of maximum vertical separation between the curves
    also happens to be a point where both curves stay within bounds
    across the FULL candidate square's width. Whenever one curve is
    still transitioning steeply right at that point (a narrow
    "pinch"), the rotation method reports a square far smaller than
    what's actually inscribable in a wider, flatter region elsewhere
    in the lobe -- which is exactly the bug that under-reported SNM
    here (it found 0.41V at a single narrow pinch point near x=1.06,
    while a true square of side ~0.75V fits over x=[0.92,1.67] where
    both curves are much flatter). Brute force checks every candidate
    width directly against the curves' actual extent over that width,
    so it can't make that mistake.

    Returns (side_length, x_center, y_center) for plotting.
    """
    fA = interp1d(xA, yA, bounds_error=False, fill_value=np.nan)
    fB = interp1d(xB, yB, bounds_error=False, fill_value=np.nan)

    if x_hi <= x_lo:
        return 0.0, np.nan, np.nan

    # Determine orientation: in this lobe, is curve A above or below B?
    x_mid = (x_lo + x_hi) / 2
    yA_mid, yB_mid = fA(x_mid), fB(x_mid)
    if np.isnan(yA_mid) or np.isnan(yB_mid):
        probe = np.linspace(x_lo, x_hi, 5)
        yA_p, yB_p = fA(probe), fB(probe)
        valid = ~np.isnan(yA_p) & ~np.isnan(yB_p)
        if not valid.any():
            return 0.0, np.nan, np.nan
        a_above = np.nanmean(yA_p[valid] - yB_p[valid]) > 0
    else:
        a_above = yA_mid > yB_mid

    x_starts = np.linspace(x_lo, x_hi, n)
    max_side = 0.0
    best = (np.nan, np.nan)

    side_candidates = np.linspace(x_hi - x_lo, 0.001, n)  # largest first

    for side in side_candidates:
        if side <= max_side:
            continue
        found = False
        for x0 in x_starts:
            x1 = x0 + side
            if x1 > x_hi:
                break
            xx = np.linspace(x0, x1, 25)
            yA_xx = fA(xx)
            yB_xx = fB(xx)
            if np.isnan(yA_xx).any() or np.isnan(yB_xx).any():
                continue
            if a_above:
                top_limit = yA_xx.min()
                bot_limit = yB_xx.max()
            else:
                top_limit = yB_xx.min()
                bot_limit = yA_xx.max()
            avail = top_limit - bot_limit
            if avail >= side:
                max_side = side
                y_center = (top_limit + bot_limit) / 2
                best = (x0 + side / 2, y_center)
                found = True
                break
        if found:
            break

    return max_side, best[0], best[1]


def main():
    q1, qb1 = load_wrdata(DC1_FILE)
    # File 2's sweep variable (col0) is physically the QBAR node (it's
    # driving inverter 2's input), and its measured output (the "real"
    # column we extract) is physically the Q node. Both curves are
    # near-identical full-swing inverter VTCs in their OWN sweep/output
    # coordinates -- that's expected and correct. To overlay curve B on
    # the SAME (Q, Qbar) axes as curve A, we must swap which one is x
    # and which is y for this file only:
    qb2_swept, q2_measured = load_wrdata(DC2_FILE)
    q2, qb2 = q2_measured, qb2_swept

    o1 = np.argsort(q1); q1, qb1 = q1[o1], qb1[o1]
    o2 = np.argsort(q2); q2, qb2 = q2[o2], qb2[o2]

    # Sanity print so you can visually confirm each curve looks right
    # (qb should start near VDD, end near 0, or vice versa - NOT flat)
    print(f"Curve A (dc1): q1 range [{q1.min():.3f},{q1.max():.3f}]  "
          f"qb1 range [{qb1.min():.3f},{qb1.max():.3f}]")
    print(f"Curve B (dc2): q2 range [{q2.min():.3f},{q2.max():.3f}]  "
          f"qb2 range [{qb2.min():.3f},{qb2.max():.3f}]")

    x_lo_all = max(q1.min(), q2.min())
    x_hi_all = min(q1.max(), q2.max())
    x_common = np.linspace(x_lo_all, x_hi_all, 4000)

    fA = interp1d(q1, qb1, bounds_error=False, fill_value=np.nan)
    fB = interp1d(q2, qb2, bounds_error=False, fill_value=np.nan)
    yA_c = fA(x_common)
    yB_c = fB(x_common)

    valid = ~np.isnan(yA_c) & ~np.isnan(yB_c)
    x_common, yA_c, yB_c = x_common[valid], yA_c[valid], yB_c[valid]

    crossings = find_crossings(x_common, yA_c, yB_c)
    print(f"\nCrossing points found at V(Q) = {np.round(crossings, 4)}")

    if len(crossings) == 0:
        raise RuntimeError(
            "No crossing found between the two curves -- check that "
            "dc1 and dc2 data actually overlap in range and the curves "
            "intersect somewhere in the middle of the sweep."
        )

    mid_idx = np.argmin(np.abs(crossings - (x_lo_all + x_hi_all) / 2))
    x_split = crossings[mid_idx]
    print(f"Using split point at V(Q) = {x_split:.4f}")

    side_0, xc0, yc0 = max_inscribed_square_side(
        q1, qb1, q2, qb2, x_lo_all, x_split)
    side_1, xc1, yc1 = max_inscribed_square_side(
        q1, qb1, q2, qb2, x_split, x_hi_all)

    print("\n=== Hold SNM Results ===")
    print(f"SNM (lobe 0, lower-left):  {side_0 * 1000:.1f} mV   "
          f"(square center ~ Q={xc0:.3f}V, Qbar={yc0:.3f}V)")
    print(f"SNM (lobe 1, upper-right): {side_1 * 1000:.1f} mV   "
          f"(square center ~ Q={xc1:.3f}V, Qbar={yc1:.3f}V)")
    print(f"Hold SNM (worst-case, reported value): "
          f"{min(side_0, side_1) * 1000:.1f} mV")

    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    ax.plot(q1, qb1, 'r-', linewidth=1.5, label='v(qb1) vs v(q1)  [dc1]')
    ax.plot(q2, qb2, 'b-', linewidth=1.5, label='v(qb2) vs v(q2)  [dc2]')

    def draw_square(side, xc, yc, color):
        if side <= 0 or np.isnan(xc):
            return
        half = side / 2
        sq = patches.Rectangle((xc - half, yc - half), side, side,
                                linewidth=1.5, edgecolor=color,
                                facecolor='none', linestyle='--')
        ax.add_patch(sq)

    draw_square(side_0, xc0, yc0, 'lime')
    draw_square(side_1, xc1, yc1, 'yellow')

    ax.set_xlabel('V(Q)  [V]')
    ax.set_ylabel('V(Qbar)  [V]')
    ax.set_title(
        f'Hold SNM Butterfly Curve\n'
        f'SNM_0={side_0*1000:.1f} mV   SNM_1={side_1*1000:.1f} mV   '
        f'Worst-case={min(side_0,side_1)*1000:.1f} mV'
    )
    ax.set_xlim(0, VDD)
    ax.set_ylim(0, VDD)
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='center right', fontsize=9)

    plt.tight_layout()
    plt.savefig('snm_butterfly_plot.png', dpi=150)
    print("\nPlot saved to snm_butterfly_plot.png")


if __name__ == '__main__':
    main()
