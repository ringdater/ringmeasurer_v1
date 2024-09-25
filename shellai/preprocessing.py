import os
from typing import List, Tuple, Union

import imageio
import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse
import skimage.color
import skimage.measure
import skimage.morphology
from PIL import Image
from scipy.spatial._qhull import _Qhull


def get_matching_strings_from_list(
    L: List[str], thing: str, expected_number: int = 1
) -> List[str]:
    # note: no wildcards!
    filtered = [x for x in L if thing.lower() in x.lower()]
    n_matches = len(filtered)

    if n_matches != expected_number:
        raise ValueError(
            f"Expected only {expected_number:d} match(es) of '{thing}'"
            f" in {L}, but found {n_matches}."
        )

    return filtered


def load_image_data(
    base_folder: str,
    folder_name: str,
    return_images: bool = True,
    no_rings: bool = False,
) -> List:
    path = os.path.join(base_folder, folder_name)

    if not os.path.exists(path):
        raise ValueError(f"Path does not exist: {path}")

    # get the files in the directory
    flist = [
        name
        for name in os.listdir(path)
        if os.path.isfile(os.path.join(path, name))
    ]

    # get each filename
    mask_file = get_matching_strings_from_list(flist, "_mask.")[0]
    image_file = get_matching_strings_from_list(flist, "_image.")[0]
    filename_list = [image_file, mask_file]

    if not no_rings:
        rings_file = get_matching_strings_from_list(flist, "_extended_rings.")[
            0
        ]
        filename_list.append(rings_file)

    # get the prefix filename for each file and check they are equal
    # as a final sanity check
    prefixes = [s.split("_")[0] for s in filename_list]

    if not all(prefixes[0] == p for p in prefixes):
        raise ValueError(
            f"Not all files share the same prefix: {filename_list}"
        )

    # finally, return the images or full file paths
    if return_images:
        # avoid compressionbomb warnings
        Image.MAX_IMAGE_PIXELS = None

        # list of imageio.core.Array objects. these subtype np.ndarray and so
        # we need to convert them to standard numpy arrays
        images = [
            np.array(imageio.imread(os.path.join(path, name)))
            for name in filename_list
        ]

        return images

    return filename_list


def threshold_drawn_mask_and_skeletonize(
    mask_image: np.ndarray, threshold: float = 0.2, sparse=True
) -> Union[np.ndarray, scipy.sparse.csc_matrix]:
    # rescales to [0, 1], i.e. [black, white]
    bw = skimage.color.rgb2gray(mask_image)

    # get the binary mask of pixels that are below the threshold
    # i.e. that have been draw on in black on a white background
    mask = bw < threshold

    # skeletonize the mask -- the 'lee' method avoids spurs when
    # skeletonizing rectangles (at least in the images I've tried)
    skel = skimage.morphology.skeletonize(mask, method="lee")
    skel = skel.astype("bool")

    if sparse:
        # create the sparse version of the matrix
        return scipy.sparse.csc_matrix(skel, dtype="bool")

    return skel


def get_line_ends(
    mask: np.ndarray, plot: bool = False, dpi: int = 500
) -> np.ndarray:
    # how to determine if we have a line end after skeletonization:
    # - look in a 3x3 window centred on a pixel
    # - if we only have one pixel connected to it then it must be a line end

    # copy the mask and remove border pixels
    mask = np.copy(mask)
    mask[0, :] = mask[:, 0] = mask[-1, :] = mask[:, -1] = False

    rr, cc = np.where(mask)  # rows, cols indices of the marked pixels
    pixel_inds = np.stack([rr, cc]).T

    # offsets of the neighbours of a central pixel (i.e. [0, 0])
    neighbour_inds = np.array(
        [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]
    )

    # get all the neighbours of the pixels -- shape (npixels, 8, 2)
    pixel_neighbour_inds = (
        pixel_inds[:, np.newaxis, :] + neighbour_inds[np.newaxis, :, :]
    )

    # extract the pixels from the mask -- shape (npixels, 8)
    pixel_neighbours = mask[
        pixel_neighbour_inds[:, :, 0], pixel_neighbour_inds[:, :, 1]
    ]

    # count the number of neighbours -- shape (npixels, )
    pixel_neighbour_counts = np.count_nonzero(pixel_neighbours, axis=1)

    # pixels at the end of a line will have only 1 neighbour
    end_pixels = pixel_inds[pixel_neighbour_counts == 1, :]

    # pair up the end points.

    # if we've only got 2 end points, job done
    if end_pixels.shape[0] == 2:
        end_pairs = np.array([[end_pixels[0], end_pixels[1]]])

    # else we label each pixel in the marked up mask based on its
    # connected components -- so lines will all be the same label
    # we can exploit the fact that, because we've already found the end
    # coordinates, we can just index the label mask for each end point
    # and get their corresponding labels.
    else:
        # labels go from [1, nlabels+1] inclusive (0 is background)
        mask_labels, nlabels = skimage.measure.label(  # type: ignore
            mask, return_num=True, connectivity=2
        )

        # build up a list of end pixel pairs such that the i'th pair of points
        # is end_pairs[i] = [[r0, c0], [r1, c1]] -- [row, col]
        end_pairs = np.zeros((nlabels, 2, 2))

        # pointer to know if we've already seen a point in that
        # connected component or yet (for indexing correctly!)
        e = np.zeros(nlabels, dtype="int")

        for r, c in end_pixels:
            # get the index of the pair to select (-1 because starting at 1)
            idx = mask_labels[r, c] - 1

            # store it
            end_pairs[idx, e[idx], :] = r, c

            # increment pointer
            e[idx] += 1

        # set the plotting image
        mask = mask_labels

    if plot:
        _, ax = plt.subplots(1, 1, figsize=(10, 5), dpi=dpi)
        ax.imshow(mask, cmap="hot")
        for [[r0, c0], [r1, c1]] in end_pairs:
            ax.plot([c0, c1], [r0, r1], ls="", marker="x")
        plt.show()

    return end_pairs


def extract_patch_indices(
    image_shape: Tuple[int, int],
    patch_shape: Tuple[int, int],
    stride: Tuple[int, int] = (1, 1),
) -> np.ndarray:
    # col, row
    ic, ir = image_shape[:2]
    pc, pr = patch_shape
    sc, sr = stride

    # define the start and end point of patches
    pc0, pc1 = np.arange(0, ic - pc, sc), np.arange(pc, ic, sc)
    pr0, pr1 = np.arange(0, ir - pr, sr), np.arange(pr, ir, sr)

    # sanity check
    assert pc0.size == pc1.size
    assert pr0.size == pr1.size

    # now we need to repeat the heights for each width -- repeat transforms
    # [1,2,3] to [1,1,1,2,2,2,3,3,3]
    _pc0 = np.repeat(pc0, repeats=pr0.size)
    _pc1 = np.repeat(pc1, repeats=pr0.size)

    # and the width for each height -- note that tile transforms the other
    # way: [1,2,3] to [1,2,3,1,2,3,1,2,3]
    _pr0 = np.tile(pr0, reps=pc0.size)
    _pr1 = np.tile(pr1, reps=pc1.size)

    # reshapes into (2, 2, n)
    Z = np.array([[_pc0, _pr0], [_pc1, _pr1]])

    # change into (n, 2, 2) such that Z[i] = [[c0, r0], [c1, r1]]
    Z = np.rollaxis(Z, 2, 0)

    return Z


def points_in_hull(points: np.ndarray, hull: _Qhull) -> np.ndarray:
    # taken from: https://stackoverflow.com/a/67457811/2161490
    equations = hull.get_simplex_facet_array()[2].T
    return np.all(points @ equations[:-1] < -equations[-1], axis=1)


def patch_corner_in_hull(Z: np.ndarray, hull: _Qhull):
    # assume Z[0] = [[c0, r0], [c1, r1]]
    valid_mask = np.zeros(Z.shape[0], dtype="bool")

    # we need:
    # [c0, r0], [c0, r1], [c1, r0], [c1, r1]
    # example: A = np.array([[1, 2], [3, 4]])
    # we need: [1, 2], [1, 4], [3, 2], [3, 4]

    for corner_inds in [
        [[0, 0], [0, 1]],
        [[0, 1], [0, 1]],
        [[1, 0], [0, 1]],
        [[1, 1], [0, 1]],
    ]:
        r, c = corner_inds
        points = Z[:, r, c]
        valid_mask |= points_in_hull(points, hull)

    return valid_mask


def remove_empty_patches(
    image: np.ndarray,
    patch_coords: np.ndarray,
    empty_patch_colours: List[np.ndarray] = [
        np.array([0, 0, 0]),
        np.array([255, 255, 255]),
    ],
    proportion: float = 0.5,
) -> np.ndarray:
    # remove all patches that are a least 'proportion' empty,
    # where empty is defined as [0, 0, 0]

    # binary mask of pixels that are all black
    empty_mask = np.zeros(image.shape[:2], dtype="bool")
    for colour in empty_patch_colours:
        # binary or
        pixel_matching_colour = image == colour[np.newaxis, np.newaxis, :]
        empty_mask |= np.all(pixel_matching_colour, axis=2)

    # storage
    valid_mask = np.ones(patch_coords.shape[0], dtype="bool")

    # get the dimensions of the first (and thus all patches) patch and
    # calculate their product to get the number of pixels in each patch
    total_pixels = np.prod(patch_coords[0, 1, :] - patch_coords[0, 0, :])

    for i, [[c0, r0], [c1, r1]] in enumerate(patch_coords):
        # extract the mask of pixels that are all empty (i.e. equal to 0)
        patch_empty_mask = empty_mask[c0:c1, r0:r1]

        # find the proportion that are empty
        prop_empty = np.count_nonzero(patch_empty_mask) / total_pixels

        if prop_empty >= proportion:
            valid_mask[i] = False

    return valid_mask


def extract_patches(image: np.ndarray, bb_inds: np.ndarray) -> np.ndarray:
    # number of patches and their height and widths
    n_patches = bb_inds.shape[0]
    h = bb_inds[0, 1, 0] - bb_inds[0, 0, 0]
    w = bb_inds[0, 1, 1] - bb_inds[0, 0, 1]

    # assumption: all patches defined by bb_inds are the same height and width
    assert np.all((bb_inds[:, 1, 0] - bb_inds[:, 0, 0]) == h)
    assert np.all((bb_inds[:, 1, 1] - bb_inds[:, 0, 1]) == w)

    # storage array size, the last elements of the tuple
    # will be empty if the image only has two dimensions
    out_shape = (n_patches, h, w, *image.shape[2:])

    out = np.empty(out_shape, dtype=image.dtype)
    for i, [[r0, c0], [r1, c1]] in enumerate(bb_inds):
        out[i] = image[r0:r1, c0:c1]

    return out
