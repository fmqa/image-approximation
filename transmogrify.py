#!/usr/bin/env python3

import operator
import sys
import random
import argparse
from math import inf, sqrt
import numpy as np
from PIL import Image
from PIL.ImageOps import colorize
from scipy.cluster.vq import kmeans, whiten

def hc(cmp=operator.le):
    """Hill-climbing algorithm."""
    M = True                            # Is Minimum?
    Smin = Sn = None                    # Minimum State
    Emin = En = inf                     # Minimum Energy
    while True:
        # Yield current optimization point, get next state.
        Sn, En = (yield Smin, Emin, M)
        # If current state energy <= next state energy: State transition
        M = False
        if cmp(En, Emin):
            Emin = En
            Smin = Sn
            M = True

def cq(array, k=72, iter=20):
    """Color quantization. Compute k dominant colors of RGB array (Color quantization) using k-Means."""
    sigma = array.std(axis=0)
    array = whiten(array)
    c, d = kmeans(array, k, iter)
    c *= sigma
    return c

def neighbor(S, atoms, colors, wmin=8, hmin=8, random=random):
    """Get neighbor state of S."""
    T = S.copy()
    atom = random.choice(atoms)
    # Affine transform -- Rotate
    atom = atom.rotate(random.randrange(360))
    try:
        alpha = atom.getchannel("A")
    except ValueError:
        alpha = None
    # Colorize
    atom = colorize(atom.convert("L"), random.choice(colors), random.choice(colors))
    if alpha is not None:
        atom.putalpha(alpha)
    # Affine transform -- Scale
    f = random.random()
    w = int(max(wmin, f * min(S.width, atom.width)))
    h = int(max(hmin, f * min(S.height, atom.height)))
    atom = atom.resize((w, h), Image.LANCZOS)
    # Affine transform -- Translate
    x = random.randrange(T.width - atom.width)
    y = random.randrange(T.height - atom.height)
    T.paste(atom, (x, y), atom)
    # Mutated image
    return T

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Approximate source image from atoms, output a PNG stream.")
    parser.add_argument("-i", "--iterations", type=int, default=inf, help="Iteration count.")
    parser.add_argument("-c", "--colors", type=int, default=72, help="Color count.")
    parser.add_argument("-s", "--source", type=Image.open, required=True, help="Source image.")
    parser.add_argument("-m", "--min", type=int, default=8, help="Minimum size of atom.")
    parser.add_argument("atoms", type=Image.open, nargs="+", help="Atoms to use.")
    
    args = parser.parse_args()
    
    source = args.source.convert("RGB")
    
    # If image is larger than 256x256, perform color quantization
    # on a rescaled version of the image.
    if source.width * source.height > 256 ** 2:
        f = sqrt((256 ** 2) / (source.width * source.height))
        chroma = source.resize((int(source.width * f), int(source.height * f)), Image.LANCZOS)
        print("Use rescaled image for color quantization: factor={:0.3}, size={}".format(f, chroma.size), file=sys.stderr) 
    else:
        chroma = source
    
    # Color quantization.
    print("Computing palette...", file=sys.stderr)
    colors = list(map(tuple, cq(np.asarray(chroma).reshape((-1, 3)), args.colors)))
    
    # Convert all atom images to RGBA.
    atoms = [atom.convert("RGBA") for atom in args.atoms]
    
    print("Starting genetic search with I={} iterations".format(args.iterations), file=sys.stderr)
    
    # Hill climbing loop.
    i = 0
    opt = hc()
    opt.send(None)
    S = Image.new(source.mode, source.size, tuple(map(int, np.mean(np.asarray(source), axis=(0, 1)))))
    while i < args.iterations:
        # Squared distance.
        E = float(np.sum((np.asarray(source) - np.asarray(S)) ** 2))
        # Send current state/energy to hill climbing coroutine.
        S, E, M = opt.send((S, E))
        # Write new image only if new local minimum detected.
        if M:
            print("{}: I={}, E={}".format("RA"[M], i, E), file=sys.stderr)
            S.save(getattr(sys.stdout, "buffer", sys.stdout), format="PNG")
        # Generate successor state.
        S = neighbor(S, atoms, colors, args.min, args.min)
        i += 1

