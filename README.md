# Image Approximation using k-Means + Hill Climbing

![Lavender Field](/example/lavender.png?raw=true "Lavender Field")

This is another take on [https://www.reddit.com/r/programming/comments/bstbki/mona_lisa_made_out_of_260_smaller_mona_lisas], using a different method.

## Synopsis

```
usage: transmogrify.py [-h] [-i ITERATIONS] [-c COLORS] -s SOURCE [-m MIN]
                       atoms [atoms ...]
transmogrify.py: error: the following arguments are required: -s/--source, atoms
```

where `SOURCE` is an RGB image and each `atom` is a RGBA image. The output (STDOUT) is a stream of PNGs, which may piped to `ffmpeg` or a different encoder.

## Usage

The following command should produce an MP4/H264 video compatible with WhatsApp / Android.

```
python3 -Bu transmogrify.py -s example/lavender.png blossom.png | ffmpeg -f image2pipe -i - -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -c:v libx264 -profile:v baseline -level 3.0 -pix_fmt yuv420p lavender.mp4
```

## Explanation

Even though this problem can be solved using genetic algorithms (as described in the reddit thread linked above), a simple mix combination of k-Means and Hill Climbing suffices to produce effective results:

1. Compute a limited palette of `k` dominant colors using k-Means. This is basically [color quantization](https://en.wikipedia.org/wiki/Color_quantization).
2. Fill the background of the output with the mean color. This speeds up convergence a bit.
3. Select a random atom (constituent image), apply a random affine transform (translation + rotation), colorize the atom using a one of the palette's colors.
4. Optimize the squared loss between source and output using hill climbing.

## Problems and optimizations

1. The color quantization step is very slow on large images, so we apply it to a downscaled version of the source image if it is larger than 256x256
2. The hill climbing is slow due to its sequential nature (Perhaps it is possible to parallelize using [Beam Search](https://en.wikipedia.org/wiki/Beam_search)?)

## References

Credit goes to _Grafixart-Photo_ on reddit for ["The Lavender Field of Valensole"](https://www.reddit.com/r/europe/comments/d8ilaz/the_lavender_field_of_valensole_france/) 
