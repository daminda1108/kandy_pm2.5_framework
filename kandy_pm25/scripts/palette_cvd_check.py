"""Colour-vision-deficiency check on the locked palette set (never run before)."""
import numpy as np, matplotlib.cm as cm

# Brettel/Vienot-style CVD simulation matrices (linear RGB)
M = {
 "deuteranopia": np.array([[0.625,0.375,0.0],[0.70,0.30,0.0],[0.0,0.30,0.70]]),
 "protanopia":   np.array([[0.567,0.433,0.0],[0.558,0.442,0.0],[0.0,0.242,0.758]]),
 "tritanopia":   np.array([[0.95,0.05,0.0],[0.0,0.433,0.567],[0.0,0.475,0.525]]),
}
def srgb2lin(c): return np.where(c<=0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
def lin2srgb(c): return np.where(c<=0.0031308, c*12.92, 1.055*np.clip(c,0,1)**(1/2.4)-0.055)
def lum(rgb):  # perceptual lightness proxy
    l=srgb2lin(rgb); return 0.2126*l[...,0]+0.7152*l[...,1]+0.0722*l[...,2]

PAL = {"YlOrRd":"sequential (PM heatmaps)", "inferno":"sequential (emission)",
       "magma":"sequential (UQ)", "RdBu":"diverging (signed)", "turbo":"episode scale"}
print(f"{'palette':<10}{'role':<28}{'vision':<14}{'mono-L':>8}{'L-range':>9}{'min dE':>8}")
for name,role in PAL.items():
    x=np.linspace(0,1,64); rgb=cm.get_cmap(name)(x)[:,:3]
    for vis in ["normal"]+list(M):
        s = rgb if vis=="normal" else np.clip(lin2srgb(srgb2lin(rgb)@M[vis].T),0,1)
        L=lum(s)
        d=np.diff(L)
        monotone = bool((d>=-1e-3).all() or (d<=1e-3).all())
        # smallest perceptual step between ADJACENT samples (proxy for banding/confusion)
        de=np.sqrt(((np.diff(s,axis=0))**2).sum(axis=1)).min()
        flag = "" if (monotone or name=="RdBu") else "  <-- NOT MONOTONE"
        print(f"{name if vis=='normal' else '':<10}{role if vis=='normal' else '':<28}"
              f"{vis:<14}{str(monotone):>8}{L.max()-L.min():9.3f}{de:8.4f}{flag}")
    print()
print("Interpretation: sequential maps must stay MONOTONE in lightness under every simulation,")
print("so a reader with CVD still reads high-vs-low correctly. Diverging maps (RdBu) are")
print("legitimately non-monotone by design -- what matters there is that the two arms remain")
print("distinguishable, which red-blue does and red-green does not.")
