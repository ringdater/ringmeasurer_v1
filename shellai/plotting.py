import gc

import matplotlib.pyplot as plt
import numpy as np
from skimage.filters import threshold_otsu


def show_segmentation_result(image, gt_mask, pred_mask, axes, threshold="otsu"):
    assert len(axes) == 4

    # squeeze out any excess dimensions, e.g. when there is 1 colour channel
    pred_mask = pred_mask.squeeze()
    gt_mask = gt_mask.squeeze()

    if not isinstance(gt_mask, bool):
        gt_mask = gt_mask > 0

    a1, a2, a3, a4 = axes

    a1.imshow(image)
    a1.set_title("Original Image")

    a2.imshow(gt_mask, cmap="gray")
    a2.set_title("Ground Truth")

    z = np.copy(pred_mask)
    a3.imshow(z, cmap="gray")
    a3.set_title(f"Prediction ($\\tau$={threshold:0.2f})")

    if not isinstance(pred_mask, bool):
        if threshold == "otsu":
            threshold = threshold_otsu(pred_mask)

        pred_mask = pred_mask >= threshold

    image_masked = overlayImage(image, gt_mask, [0, 1, 0], alpha=1)
    image_masked = overlayImage(image_masked, pred_mask, [0, 0, 1], alpha=0.5)

    a4.imshow(image_masked)

    a4.set_title("Overlaid masks")
    a4.plot(0, 0, "g", label="GT")
    a4.plot(0, 0, "b", label="Pred")
    a4.legend(loc="upper right", fontsize=8)


def plot_auc(data, ax, title="Network prediction performance"):
    for fpr, tpr, auc, label in data:
        ax.plot(fpr, tpr, label=f"{label:s} (AUC: {auc:0.2f})")

    ax.plot([0, 1], [0, 1], "k", alpha=0.25, lw=0.25)

    ax.set_title("Network prediction performance")
    ax.set_xlabel("False Positive Rate", fontsize=11)
    ax.set_ylabel("True Positive Rate", fontsize=11)
    ax.legend(loc="lower right", fontsize=12)

    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.grid(alpha=0.25, zorder=0)

    ax.set_xticks(np.arange(0, 1.1, 0.1))
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.set_title(title, fontsize=14)


def overlayImage(im, mask, col, alpha):
    """
    Taken from: https://stackoverflow.com/a/28133733/2161490
    im = (n, m, 3), image
    mask = (n, m), binary mask
    col = (3, ), rgb colour
    alpha = float,
    """
    # extend mask to the entire image (i.e. repeat for the last dim 3 times)
    mask_rgb = np.tile(mask[..., np.newaxis], 3)

    # values of the image we don't want masked
    im_unmasked = (~mask_rgb) * im

    # linearly interpolate between the original image and the overlaid image
    im_overlay = np.array(col) * mask_rgb
    im_masked = mask_rgb * im
    image_masked_interpolated = alpha * im_overlay + (1 - alpha) * im_masked

    # combine and return the masked and unmasked values
    return im_unmasked + image_masked_interpolated


def display(real_images, real_masks, predicted_masks, n=10, first=False):
    """
    Displays n random images from each one of the supplied arrays.
    """
    assert (real_images.shape[0] == real_masks.shape[0]) and (
        real_masks.shape[0] == predicted_masks.shape[0]
    ), (real_images.shape, real_masks.shape, predicted_masks.shape)
    if first:
        indices = np.arange(n)
    else:
        indices = np.random.randint(len(real_images), size=n)
    images = real_images[indices, :].squeeze()
    masks = real_masks[indices, :].squeeze()
    preds = predicted_masks[indices, :].squeeze()

    fig, ax = plt.subplots(3, n, figsize=(20, 5), constrained_layout=True)
    for i, (image, mask, pred) in enumerate(zip(images, masks, preds)):
        ax[0, i].imshow(image)
        ax[1, i].imshow(mask, cmap="gray")
        ax[2, i].imshow(pred, cmap="gray")

    for a in ax.flat:
        a.get_xaxis().set_visible(False)
        a.get_yaxis().set_visible(False)

    plt.show()


def create_prediction_images(
    image,
    ring_mask,
    patch_coords,
    predictions,
    show=False,
    save=False,
    savename="predictions.png",
    dpi=300,
    figsize=(10, 7),
):
    # get the bounds of the patches
    min_c, min_r = np.min(patch_coords[:, 0]), np.min(patch_coords[:, 2])
    max_c, max_r = np.max(patch_coords[:, 1]), np.max(patch_coords[:, 3])

    im_shape = image.shape[:3]

    predicted_mask = np.zeros(im_shape, dtype="float")
    counts = np.zeros(im_shape, dtype="int")

    # extract and store the predictions, as well as how often each
    # pixel has had a prediction added to it
    for pred, [c0, c1, r0, r1] in zip(predictions, patch_coords):

        predicted_mask[r0:r1, c0:c1] += pred
        counts[r0:r1, c0:c1] += 1

    count_mask = counts > 0
    predicted_mask[count_mask] /= counts[count_mask]

    if show or save:
        # set up the slicing (to avoid plotting empty parts)
        s0, s1 = slice(min_r, max_r + 1), slice(min_c, max_c + 1)

        fig, ax = plt.subplots(
            3, 1, figsize=figsize, sharex=True, sharey=True, dpi=dpi
        )
        ax[0].imshow(image[s0, s1, :])
        ax[1].imshow(ring_mask[s0, s1], cmap="gray_r")
        ax[2].imshow(predicted_mask[s0, s1], cmap="gray_r")
        ax[0].set_title("Original image")
        ax[1].set_title("Original mask (Ground truth)")
        ax[2].set_title("Predicted mask (Automatically segmented)")
        plt.tight_layout()

        if save:
            plt.savefig(savename)
            print("Predictions saved to:", savename)

        if show:
            plt.show()

        plt.close(fig)
        del fig, ax

    del counts, count_mask
    gc.collect()

    return predicted_mask, (min_c, max_c, min_r, max_r)
