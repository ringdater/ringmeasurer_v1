import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.callbacks import Callback

from . import plotting


@tf.function
def preprocess_image(image, image_size=[256, 256]):
    # EXPLICIT IMAGE SIZES ARE NEEDED FOR THE TPU
    image = tf.reshape(image, shape=(*image_size, 3))

    # convert image to float and normalize
    image = tf.cast(image, dtype=tf.float32)
    image = tf.divide(image, 255.0)
    return image


@tf.function
def preprocess_mask(mask, mask_size=[256, 256]):
    # EXPLICIT IMAGE SIZES ARE NEEDED FOR THE TPU
    mask = tf.reshape(mask, shape=(*mask_size, 1))
    return mask


@tf.function
def preprocess_step(image, mask, image_size=[256, 256]):
    image = preprocess_image(image, image_size)
    mask = preprocess_mask(mask, image_size)

    return image, mask


@tf.function
def perform_augmentation(image, label, rng):
    # https://www.tensorflow.org/tutorials/images/data_augmentation
    # draw a random seed so we do the same flips for the image and mask

    # total pairs of seeds we need (one pair per operation)
    n_seeds = 5
    S = tf.reshape(
        rng.make_seeds(2 * n_seeds)[0], (n_seeds, 2)  # shape (n_seeds, 2)
    )

    # -------------------------- FLIPPING
    # apply flips to image
    image = tf.image.stateless_random_flip_left_right(image, seed=S[0])
    image = tf.image.stateless_random_flip_up_down(image, seed=S[1])

    # and the mask (casting to something that can be flipped first)
    label_dtype = label.dtype
    label = tf.cast(label, image.dtype)
    label = tf.image.stateless_random_flip_left_right(label, seed=S[0])
    label = tf.image.stateless_random_flip_up_down(label, seed=S[1])
    label = tf.cast(label, label_dtype)

    # -------------------------- COLOUR
    # first, we randomly increase / decrease contrast by (up to) double / half
    image = tf.image.stateless_random_contrast(
        image, lower=0.5, upper=2, seed=S[2]
    )

    # next we randomly increase/decrease the saturation similarly
    image = tf.image.stateless_random_saturation(
        image, lower=0.5, upper=2, seed=S[3]
    )

    # finally, we randomly change the brightness
    image = tf.image.stateless_random_brightness(
        image, max_delta=0.1, seed=S[4]
    )

    # end by ensuring image values still lie in [0, 1]
    image = tf.clip_by_value(image, 0.0, 1.0)

    return image, label


def get_train_gcp_ds(ds, batch_size, AUTOTUNE=-1, rng=None):
    # shuffle
    ds = ds.shuffle(1024)

    # preprocessing step
    ds = ds.map(preprocess_step, num_parallel_calls=AUTOTUNE)

    # if we haven't been given a specific generator, then get a new one.
    if rng is None:
        rng = tf.random.Generator.from_non_deterministic_state()

    # perform the augmentation
    ds = ds.map(
        lambda image, mask: perform_augmentation(image, mask, rng),
        num_parallel_calls=AUTOTUNE,
    )

    # batch it up
    ds = ds.batch(batch_size, drop_remainder=True)
    ds = ds.prefetch(AUTOTUNE)

    return ds


def get_val_gcp_ds(ds, batch_size, AUTOTUNE=-1):
    # we may have additional arguments in a validation ds loader, such as
    # the bounding box indices as well. so create a wrapper function that
    # ignores the additional arguments
    def pp_step_with_optional_extra_args(image, label, *args):
        return (*preprocess_step(image, label), *args)  # type: ignore

    ds = ds.map(pp_step_with_optional_extra_args, num_parallel_calls=AUTOTUNE)

    # batch it up
    ds = ds.batch(batch_size, drop_remainder=True)
    ds = ds.prefetch(AUTOTUNE)

    return ds


class CallbackPlotter(Callback):
    def __init__(self, plot_every=10):
        self.plot_every = plot_every
        super(Callback, self).__init__()

    def on_epoch_end(self, epoch, logs=None):
        if (epoch > 0) and (epoch % self.plot_every) == 0:
            self._plot()

    def on_train_begin(self, logs=None):
        self._plot()

    def on_train_end(self, logs=None):
        self._plot()

    def _plot(self):
        raise NotImplementedError


class CallbackPlotPredictions(CallbackPlotter):  # type:ignore
    def __init__(self, base_val_ds, AUTOTUNE=-1, num_to_plot=10, plot_every=10):
        super(CallbackPlotPredictions, self).__init__(plot_every=plot_every)
        self.n = num_to_plot
        self.ds = base_val_ds.map(preprocess_step, num_parallel_calls=AUTOTUNE)

    def _plot(self):
        temp_ds = self.ds.shuffle(self.n).batch(self.n, drop_remainder=True)
        batch = temp_ds.take(1)

        plotting_images, plotting_targets = next(batch.as_numpy_iterator())
        predictions = self.model(plotting_images, training=False)  # type:ignore

        predictions = predictions.numpy()

        plotting.display(
            plotting_images, plotting_targets, predictions, n=self.n,
        )


class CallbackPlotHistory(CallbackPlotter):  # type:ignore
    def __init__(self, history_callback, plot_every=10):
        super(CallbackPlotHistory, self).__init__(plot_every=plot_every)

        self.h = history_callback

    def on_train_begin(self, logs=None):
        # do not plot on training begin because we don't have any history yet
        return

    def _plot(self):
        keys = [key for key in self.h.history if "val" not in key]

        if len(keys) == 0:
            return

        start = 0
        n = len(self.h.history[keys[0]])

        fig, axes = plt.subplots(
            1, len(keys), figsize=(15, 5), sharex=True, sharey=False
        )
        axes = axes if len(keys) > 1 else [axes]
        for ax, key in zip(axes, keys):  # type:ignore
            ax.plot(
                range(start, n),
                self.h.history[key][start:],
                label="Training",
                alpha=0.5,
            )
            ax.plot(
                range(start, n),
                self.h.history[f"val_{key:s}"][start:],
                label="Validation",
                alpha=0.5,
            )
            ax.legend(loc="best")
            ax.set_title(key)

            ax.semilogy()
            ax.set_xlabel("epochs")
        plt.show()
