import glob
import os

import numpy as np
import pandas as pd


def normalize_vector(x: np.ndarray) -> np.ndarray:
    """scales the vector x such that its largest (smallest) value is 1 (0)"""
    xmin, xmax = np.min(x), np.max(x)

    return (x - xmin) / (xmax - xmin)


def parse_measurement_csv_from_directory(
    dirpath: str,
    glob_mask: str = "*_measurement*.csv",
    column_name: str = "Length",
) -> np.ndarray:
    files = glob.glob(os.path.join(dirpath, glob_mask))

    # simple error handling to ensure we have a matching file
    if len(files) == 0:
        raise ValueError(
            f"No files matching {glob_mask:s} found in {dirpath:s}"
        )

    elif len(files) > 1:
        raise ValueError(f"More than one csv file found: {files}")

    df = pd.read_csv(files[0])

    lengths = np.array(df[column_name].values)  # type:ignore

    return lengths


def get_predicted_ring_distances(flc, peak_inds, scaling, reversed=True):
    # the peak indices correspond to the locations in the ring array that are peaks
    # the ring array is the same length as the flc array, so we can just index flc
    # to get the locations of the pixels in the original image that contain peaks
    peak_pixel_locations = flc[peak_inds]

    # now we need to find the distance between consecutive rings, this gives us the
    # ring widths.

    # diffs[i] = [(ppl[i+1, 0] - ppl[i, 0]), (ppl[i+1, 1] - ppl[i+1, 1])
    diffs = np.diff(peak_pixel_locations, axis=0)

    # Euclidean distance (PIXELS) between rings
    predicted_ring_distances_px = np.sqrt(np.sum(np.square(diffs), axis=1))

    # convert to um
    predicted_ring_distances_um = predicted_ring_distances_px * scaling

    if reversed:
        # reverse it to match gt ordering
        predicted_ring_distances_um = predicted_ring_distances_um[::-1]

    return predicted_ring_distances_um
