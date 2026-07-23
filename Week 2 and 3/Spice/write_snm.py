import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# ---------------------------------------------------------
# Read data
# ---------------------------------------------------------
dc1 = np.loadtxt("dc1_out.txt")
dc2 = np.loadtxt("dc2_out.txt")

# RED CURVE
# x = V(gb1)
# y = V(q1)
xr = dc1[:,1]
yr = dc1[:,3]

# BLUE CURVE
# x = V(gb1)
# y = V(q2)
xb = dc2[:,1]
yb = dc2[:,0]

# ---------------------------------------------------------
# Sort
# ---------------------------------------------------------
idx = np.argsort(xr)
xr = xr[idx]
yr = yr[idx]

idx = np.argsort(xb)
xb = xb[idx]
yb = yb[idx]

fred = interp1d(
    xr, yr,
    bounds_error=False,
    fill_value=np.nan)

fblue = interp1d(
    xb, yb,
    bounds_error=False,
    fill_value=np.nan)

xmin = max(xr.min(), xb.min())
xmax = min(xr.max(), xb.max())

best_side = 0.0
best_square = None

# ---------------------------------------------------------
# Search largest square
# ---------------------------------------------------------
for x0 in np.linspace(xmin, xmax, 4000):

    yr0 = fred(x0)

    if np.isnan(yr0):
        continue

    # Try increasing square size
    for side in np.linspace(0.001, 1.2, 2500):

        x1 = x0 + side

        if x1 > xmax:
            break

        yb1 = fblue(x1)

        if np.isnan(yb1):
            continue

        # top of square
        y_top = yr0 + side

        # square fits if top-right corner lies on blue curve
        if abs(yb1 - y_top) < 2e-3:

            if side > best_side:
                best_side = side
                best_square = (x0, yr0)

print("--------------------------------")
print("WRITE SNM =", best_side, "V")
print("--------------------------------")

# ---------------------------------------------------------
# Plot
# ---------------------------------------------------------
plt.figure(figsize=(7,7))

plt.plot(xr, yr, 'r', lw=2, label='Q1')
plt.plot(xb, yb, 'b', lw=2, label='Q2')

if best_square is not None:

    x0, y0 = best_square
    s = best_side

    plt.plot(
        [x0, x0+s, x0+s, x0, x0],
        [y0, y0, y0+s, y0+s, y0],
        'g', lw=3)

    plt.scatter([x0, x0+s],
                [y0, y0+s],
                color='k')

plt.axis('equal')
plt.grid(True)
plt.xlabel("Voltage (V)")
plt.ylabel("Voltage (V)")
plt.legend()
plt.show()
