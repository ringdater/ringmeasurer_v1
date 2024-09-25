from typing import List

from tensorflow.keras.layers import (
    BatchNormalization,
    concatenate,
    Conv2D,
    Conv2DTranspose,
    Dropout,
    Input,
    MaxPool2D,
    SeparableConv2D,
    SpatialDropout2D,
    UpSampling2D,
)
from tensorflow.keras.models import Model


def conv2d_act_bn(
    x, filters, kernel_size, ctype="default", act=None, strides=1, bn=True
):
    if ctype == "default":
        c = Conv2D
    elif ctype == "separable":
        c = SeparableConv2D
    else:
        raise ValueError(f"Invalid convolution type given: {ctype:s}")

    x = c(
        filters=filters,
        kernel_size=kernel_size,
        strides=strides,
        padding="same",
        activation=act,
    )(x)
    if bn:
        x = BatchNormalization()(x)

    return x


def unet(
    input_shape: List[int],
    filters: List[int],
    num_classes: int = 1,
    act: str = "relu",
    output_act: str = "sigmoid",
    kernel_size=(5, 5),
    conv_type: str = "default",  # or separable
    dropout: float = 0.0,
    dropout_type: str = "default",
    dropout_on_decoder: bool = False,
    upsample_method: str = "conv2dt",
) -> Model:
    """Construct a standard U-Net model

    Parameters:
        input_shape:
            Shape of input images, e.g., [256, 256, 3]
        filters:
            List of filter sizes, e.g. [16, 32, 64, 128, 256, 512]
        num_classes (optional):
            Number of output classes to predict (default 1)
        act (optional):
            Tensorflow activation function name, e.g. "relu"
        output_act (optional):
            Tensorflow activation function for the output layer, e.g. "sigmoid"
        kernel_size (optional):
            Size of convolutional layers, e.g. (3, 3)
        conv_type (optional):
            Type of downsampling convolutions to perform. Choose from:
                - "default": standard convolutions (Conv2D)
                - "separable": separable convolutions (SeparableConv2D)
                            these are computationally cheaper
        dropout (optional):
            Proportion of weights to drop out.
        dropout_type (optional):
            Type of dropout. Choose from:
                - "default": standard dropout, purely random (Dropout)
                - "spatial": spatially correlated dropout (SpatialDropout2D)
        dropout_on_decoder (optional):
            Whether to apply dropout on the decoding layers.
        upsample_method (optional):
            Upsampling method, choose from:
                - "conv2dt": 2d convolutional transpose (Conv2DTranspose)
                - "upsample": standard upsampling (UpSampling2D)

    Returns:
        A tensorflow U-Net model.

    """
    if dropout_type == "default":
        dropout_class = Dropout
    else:
        dropout_class = SpatialDropout2D

    input_tensor = Input(shape=input_shape)

    residuals = []

    # use the last (largest) filter for the middle block
    filters, largest_filter = filters[:-1], filters[-1]

    # encoder
    x = input_tensor

    for fs in filters:
        x = conv2d_act_bn(x, fs, kernel_size, act=act, ctype=conv_type)

        if dropout > 0:
            x = dropout_class(dropout)(x)

        x = conv2d_act_bn(x, fs, kernel_size, act=act, ctype=conv_type)

        residuals.append(x)

        x = MaxPool2D(pool_size=(2, 2), padding="same")(x)

    # middle
    x = conv2d_act_bn(x, largest_filter, kernel_size, act=act, ctype=conv_type)

    # decoder
    for residual, fs in zip(residuals[::-1], filters[::-1]):
        # choose between upsampling (cheaper) or 2d convolution transpose
        if upsample_method == "upsample":
            x = UpSampling2D(size=(2, 2))(x)
            x = conv2d_act_bn(
                x, fs, kernel_size, act=act, ctype=conv_type, bn=False
            )

        else:
            x = Conv2DTranspose(
                fs, kernel_size, activation=act, strides=(2, 2), padding="same",
            )(x)

        # join on the residual from the opposite layer
        x = concatenate([x, residual])

        x = conv2d_act_bn(x, fs, kernel_size, act=act, ctype=conv_type)

        if dropout_on_decoder and dropout > 0:
            x = dropout_class(dropout)(x)

    output_tensor = Conv2D(
        num_classes, kernel_size, activation=output_act, padding="same"
    )(x)

    model = Model(
        inputs=[input_tensor], outputs=[output_tensor], name="SimpleUNet"
    )

    return model
