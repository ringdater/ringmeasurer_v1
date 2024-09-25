import os
from typing import Tuple

import numpy as np
import tensorflow as tf

from . import preprocessing, tf_util_gcp


def _bytes_feature(value):
    """Returns a bytes_list from a string / byte."""
    if isinstance(value, type(tf.constant(0))):
        value = (
            value.numpy()
        )  # BytesList won't unpack a string from an EagerTensor.
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _int64_list_feature(values):
    """Returns an int64_list from a bool / enum / int / uint."""
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[*values]))


def create_tfrecord_feature(image, ring_mask, line_mask, bb_inds, image_name):
    feature = {
        "image": _bytes_feature(tf.io.serialize_tensor(image)),
        "rings": _bytes_feature(tf.io.serialize_tensor(ring_mask)),
        "lines": _bytes_feature(tf.io.serialize_tensor(line_mask)),
        "bb_inds": _int64_list_feature(bb_inds.ravel()),
        "image_name": tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[str(image_name).encode()])
        ),
    }
    return feature


def parse_tfrecord_feature(example, keys_to_extract=["image", "rings"]):
    feature_description = {
        "image": tf.io.FixedLenFeature([], tf.string),
        "rings": tf.io.FixedLenFeature([], tf.string),
        "lines": tf.io.FixedLenFeature([], tf.string),
        "bb_inds": tf.io.FixedLenFeature((4,), tf.int64),
        "image_name": tf.io.FixedLenFeature([], tf.string),
    }

    feature_description = {
        k: v for k, v in feature_description.items() if k in keys_to_extract
    }

    example = tf.io.parse_single_example(example, feature_description)

    if "image" in keys_to_extract:
        example["image"] = tf.io.parse_tensor(
            example["image"], out_type=tf.uint8
        )
    if "rings" in keys_to_extract:
        example["rings"] = tf.io.parse_tensor(
            example["rings"], out_type=tf.bool
        )
    if "lines" in keys_to_extract:
        example["lines"] = tf.io.parse_tensor(
            example["lines"], out_type=tf.bool
        )
    if "bb_inds" in keys_to_extract:
        example["bb_inds"] = tf.reshape(example["bb_inds"], (2, 2))

    return example


def get_ds_length(filenames, count=0):
    for fpath in filenames:
        # get the filename only
        fn = os.path.basename(fpath)

        # remove the extension
        fn = fn.split(".")[0]

        # should be structured like: name_number_amount-of-samples
        name, idx, amount = fn.split("_")

        count += int(amount)

    return count


def get_base_dataset(filenames, AUTOTUNE, keys_to_extract=["image", "rings"]):
    def parse_tfrec(x):
        return parse_tfrecord_feature(x, keys_to_extract)

    def extract_keys(x):
        return tuple(x[key] for key in keys_to_extract)

    ds = tf.data.TFRecordDataset(filenames, num_parallel_reads=AUTOTUNE)
    ds = ds.map(parse_tfrec, num_parallel_calls=AUTOTUNE)
    ds = ds.map(extract_keys, num_parallel_calls=AUTOTUNE)

    return ds


def order_2d_curve(points: np.ndarray, start_idx: int) -> np.ndarray:
    """
    points: numpy array (n, d) of 'n' points
    start_idx: index of one of the end points of the line
    """
    n = points.shape[0]

    # which points have yet been assigned
    unused_mask = np.ones(n, dtype="bool")
    # their indices
    point_inds = np.arange(n)
    # ordered indices of the points
    ordered_inds = np.zeros(n, dtype="int")

    # first location = given
    ordered_inds[0] = start_idx
    unused_mask[start_idx] = False

    # last point evaluated (at the beginning this is the one we were given)
    last_idx = start_idx

    for i in range(1, n):
        # find the distances between all remaining (unassigned) points
        # and the last assigned
        d = np.linalg.norm(points[unused_mask] - points[last_idx], axis=1)

        # find the corresponding index in the original array (points)
        nearest_idx = point_inds[unused_mask][np.argmin(d)]

        # store it, mark it as assigned, and set the last assigned to it
        ordered_inds[i] = nearest_idx
        unused_mask[nearest_idx] = False
        last_idx = nearest_idx

    return ordered_inds


def get_test_patch_locations(
    mask_image: np.ndarray,  # assuming (h, w, 3)
    patch_shape: Tuple[int, int],
    stride_step: int,
):
    """
    inputs:
        mask_image: mask image (not binary mask!), containing **one** drawn
                    line along which we wish to extract patches.
        patch_shape: shape of the patch to extract, e.g. (256, 256)
        stride_step: spacing between patches, e.g. 256//4

    Note that the coordinates of the drawn line are sorted from (ideally) the
    left-hand side of the image, although this may not always be the case.

    returns:
        patch_coords: (m, 4) ndarray. each row contains [c0, c1, r0, r1],
                      defining an image patch image[r0:r1, c0:c1].
        lc: (m, 2) ndarray containing the centre point, of each patch, i.e.
            patch_coords[i, 0] = lc[i, 1] - (patch_shape[1] // 2)
            patch_coords[i, 1] = lc[i, 1] + (patch_shape[1] // 2)
            patch_coords[i, 2] = lc[i, 0] - (patch_shape[0] // 2)
            patch_coords[i, 3] = lc[i, 0] + (patch_shape[0] // 2)
        full_lc: (n, 2) ndarray containing every coordinate of the drawn line
    """

    # convert the masks to sparse binary masks
    line_mask = preprocessing.threshold_drawn_mask_and_skeletonize(
        mask_image, sparse=False
    )
    assert isinstance(line_mask, np.ndarray)

    # extract the coordinates along the line
    lc = np.stack(np.where(line_mask)).T

    # get the end coordinates of the line
    line_ends = preprocessing.get_line_ends(line_mask)[0]

    # we want to start with the end that is nearest the right-hand side of the
    # image so we make plotting and results processing consistant
    good_end = line_ends[np.argmin(line_ends[:, 1])]

    # get the index of lc that corresponds to one of the ends
    lc_end_idx = np.where(np.all(lc == good_end, axis=1))[0][0]

    # order the points
    lc_ordered_inds = order_2d_curve(lc, lc_end_idx)
    lc = lc[lc_ordered_inds]

    # apply striding
    full_lc = lc
    lc = full_lc[::stride_step, :]

    # patch locations, centred on each coordinate along the line
    pr0 = lc[:, 0] - patch_shape[0] // 2
    pr1 = lc[:, 0] + patch_shape[0] // 2
    pc0 = lc[:, 1] - patch_shape[1] // 2
    pc1 = lc[:, 1] + patch_shape[1] // 2

    assert np.all((pc1 - pc0) == patch_shape[0])
    assert np.all((pr1 - pr0) == patch_shape[1])

    # keep only those inside the image bounds
    valid_mask = np.ones(pc0.size, dtype="bool")
    valid_mask &= pc0 >= 0
    valid_mask &= pr0 >= 0
    valid_mask &= pr1 < mask_image.shape[0]
    valid_mask &= pc1 < mask_image.shape[1]

    pc0, pc1 = pc0[valid_mask], pc1[valid_mask]
    pr0, pr1 = pr0[valid_mask], pr1[valid_mask]
    lc = lc[valid_mask, :]

    patch_coords = np.stack([pc0, pc1, pr0, pr1]).T

    return patch_coords, lc, full_lc


def extract_patches_from_image(patch_coords: np.ndarray, image: np.ndarray):
    n = patch_coords.shape[0]

    patch_shape = (
        (patch_coords[0, 3] - patch_coords[0, 2]),
        (patch_coords[0, 1] - patch_coords[0, 0]),
        3,
    )

    X = np.zeros((n, *patch_shape), dtype=image.dtype)

    for i, (c0, c1, r0, r1) in enumerate(patch_coords):
        X[i] = image[r0:r1, c0:c1]

    return X


def create_patch_image(
    patches: np.ndarray, patch_coords: np.ndarray, image_shape: Tuple,
) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """
        patches = (n, ph, pw, d), with d optional
        patch_coords = (n, 4), where p_c[i] = [c0, c1, r0, r1]
        image_shape = (ih, iw, ...)
    """

    h, w = image_shape[:2]
    d = patches.shape[3:]

    # get the bounds of the patches
    min_c, min_r = np.min(patch_coords[:, 0]), np.min(patch_coords[:, 2])
    max_c, max_r = np.max(patch_coords[:, 1]), np.max(patch_coords[:, 3])

    composite = np.zeros((h, w, *d), dtype="float")
    counts = np.zeros((h, w), dtype="int")

    # extract and store the predictions, as well as how often each
    # pixel has had a prediction added to it
    for patch, [c0, c1, r0, r1] in zip(patches, patch_coords):
        composite[r0:r1, c0:c1] += patch
        counts[r0:r1, c0:c1] += 1

    count_mask = counts > 0
    composite[count_mask] /= counts[count_mask]

    return composite, (min_c, max_c, min_r, max_r)


def convert_patches_into_tf_ds(
    patch_coords: np.ndarray, image: np.ndarray, batch_size: int = 128
):
    X = extract_patches_from_image(patch_coords, image)

    AUTOTUNE = tf.data.AUTOTUNE
    ds = tf.data.Dataset.from_tensor_slices((X,))
    ds = ds.map(tf_util_gcp.preprocess_image, num_parallel_calls=AUTOTUNE)
    ds = ds.batch(batch_size, drop_remainder=False)
    ds = ds.prefetch(AUTOTUNE)

    return ds


def extract_rings_patchbased(
    line_coords: np.ndarray,
    image: np.ndarray,
    patch_size: int = 3,
    method: str = "mean",
) -> np.ndarray:
    """
    extracts values from patches with side lengths 'patch_size' at each
    coordinate, combining their values with the specified 'method'

    line_coords: ndarray, shape (n, 2) of n lots of (y, x) patch centre coords
    image: ndarray, shape (h, w, ...)
    patch_size: int, length of patch sides, must be odd
    method: str, one of ['mean', 'max'], method by which to combine patch
            values
    """

    if patch_size % 2 == 0:
        raise ValueError(f"size of patch must be odd, given: {patch_size:d}")

    valid_methods = ["mean", "max"]
    if method not in valid_methods:
        raise ValueError(
            f"Invalid method given ({method}), valid: {valid_methods}"
        )

    # generate the offsets of the patch coordinates, centred on [0, 0]
    # yc and xc have shape (patch_size**2)
    sidelength = patch_size // 2
    slce = slice(-sidelength, sidelength + 1)
    yc, xc = [coords.ravel() for coords in np.mgrid[slce, slce]]

    # set up the patch coordinates, shape (line_coords.shape[0], patch_size**2)
    py = line_coords[:, 0][:, np.newaxis] + yc[np.newaxis, :]
    px = line_coords[:, 1][:, np.newaxis] + xc[np.newaxis, :]

    # calculate which parts (if any) of the patch are outside the image
    invalid_mask = np.zeros(py.shape, dtype="bool")
    invalid_mask |= py < 0
    invalid_mask |= px < 0
    invalid_mask |= py >= image.shape[0]
    invalid_mask |= px >= image.shape[1]

    # now fix the indexing to reside in the patch so we can grab all
    # values in a vectorised fashion. note that we're not including them in
    # calculations due to the masked stuff below so the the 0s is arbitrary
    py[invalid_mask] = 0
    px[invalid_mask] = 0

    # extract the patches -- shape (line_coords.shape[0], patch_size**2, ...)
    flattened_patches = image[py, px]

    # create a masked array with a mask indicating which patch elements
    # are invalid
    masked_flattened_patches = np.ma.masked_array(
        flattened_patches, mask=invalid_mask
    )

    # carry out the summary method on the masked array
    if method == "mean":
        result = np.ma.mean(masked_flattened_patches, axis=1)

    else:  # method == "max"
        result = np.ma.max(masked_flattened_patches, axis=1)

    # only keep the values, get rid of the masked stuff
    result = result.data

    return result


def place_patches_in_row_image(
    image, patch_centres, patch_coords, patch_shape, use_only=-1
):
    patch_coords = patch_coords.astype("int")

    # Euclidean distance between each patch (in pixels)
    patch_dists = np.linalg.norm(np.diff(patch_centres, axis=0), axis=1)
    patch_dists = np.round(patch_dists, decimals=0).astype("int")

    # keep only the first "use_only" for debugging *(defaults to all patches)
    patch_centres = patch_centres[:use_only]
    patch_coords = patch_coords[:use_only]
    patch_dists = patch_dists[: use_only - 1]

    total_size = patch_shape[1] + sum(patch_dists)
    slice_shape = (patch_shape[0], total_size)

    if image.ndim == 2:
        image = image.reshape(*image.shape, 1)

    d = image.shape[2:]

    sliced_image = np.zeros((*slice_shape, *d), dtype="float")
    counts = np.zeros_like(sliced_image, dtype="int")

    # starting position
    c = patch_shape[1] // 2 + patch_dists[1] // 2

    # place the 1st entire patch in, up to before the 2nd one starts
    c0, _, r0, r1 = patch_coords[0]
    sliced_image[:, :c] = image[r0:r1, c0 : c0 + c]

    # place the entire last patch in
    e = patch_shape[1] // 2 - patch_dists[-1] // 2
    _, c1, r0, r1 = patch_coords[-1]
    sliced_image[:, -e:] = image[r0:r1, c1 - e : c1]

    for (c0, c1, r0, r1), (_, px), d in zip(
        patch_coords[1:], patch_centres[1:], patch_dists
    ):
        dhalf = d // 2
        offset_for_odd = d % 2 != 0

        slce = slice(c, c + d)
        s2 = slice(px - dhalf - offset_for_odd, px + dhalf)

        sliced_image[:, slce] += image[r0:r1, s2]
        counts[:, slce, :] += 1

        c += d

    cmask = counts > 0
    sliced_image[cmask] = sliced_image[cmask] / counts[cmask]

    # cast to input image type
    sliced_image = sliced_image.astype(image.dtype)

    return sliced_image
