import torch
import torch.nn as nn
import torch.nn.functional as F

from .utils import accuracy, grad_reverse


class SteganographerV1(nn.Module):
    r"""
    This module takes in a batch of cover images and data vectors. It returns
    the corresponding steganographic images and two loss values corresponding
    to the decoding loss and classifier loss.

    The input images should be scaled to a (-1.0, 1.0) while the data vector
    should only contain values in the set {0, 1}.

    Input: (N, 3, height, width), (N, data_depth, height, width)
    Output: (N, 3, height, width), (1), (1)
    """

    def __init__(self, data_depth, hidden_dim):
        super(SteganographerV1, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(
                in_channels=3 +
                data_depth,
                out_channels=hidden_dim,
                kernel_size=3,
                padding=1),
            nn.SELU(),
            nn.Conv2d(
                in_channels=hidden_dim,
                out_channels=3,
                kernel_size=3,
                padding=1),
        )

        self.decoder = nn.Sequential(
            nn.Conv2d(
                in_channels=3,
                out_channels=hidden_dim,
                kernel_size=3,
                padding=1),
            nn.SELU(),
            nn.Conv2d(
                in_channels=hidden_dim,
                out_channels=data_depth,
                kernel_size=3,
                padding=1),
        )

        self.classifier = nn.Sequential(
            nn.Conv2d(
                in_channels=3,
                out_channels=hidden_dim,
                kernel_size=3,
                padding=1),
            nn.SELU(),
            nn.Conv2d(
                in_channels=hidden_dim,
                out_channels=2,
                kernel_size=3,
                padding=1),
        )

    def forward(self, image, data):
        batch_size = image.size()[0]
        x = torch.cat((image, data), dim=1)

        # normalize image from (0.0, 1.0) to (-1.0, 1.0)
        image = image * 2.0 - 1.0

        # encode the cover image into a stego image, decode into predictions
        encoded = torch.tanh(
            torch.tan(image) +
            torch.tanh(
                self.encoder(x)) /
            10.0)

        # move up or down by up to 1 bit (helps deal with quantization)
        noise = torch.zeros(encoded.size())
        noise = noise.uniform_(-0.5 / 255.0, 0.5 / 255.0).to(image.device)

        if not self.training:
            # in eval mode, make sure to quantize it
            encoded = (encoded * 125.0 + 125.0).long()
            encoded = encoded.float() / 125.0 - 1.0

        decoded = self.decoder(encoded + noise)

        # try to discriminate between the real image and the stego image
        y_pred_pos = torch.mean(
            torch.mean(
                self.classifier(image),
                dim=2),
            dim=2)
        y_pred_neg = torch.mean(
            torch.mean(
                self.classifier(
                    grad_reverse(encoded)),
                dim=2),
            dim=2)

        # compute the decoding loss (e.g. whether we recovered the input) and
        # the classifier loss (e.g. whether we can tell them apart)
        decoding_loss = F.binary_cross_entropy_with_logits(decoded, data)
        classifier_loss = F.cross_entropy(
            torch.cat([y_pred_pos, y_pred_neg], dim=0),
            torch.LongTensor(
                [0] *
                batch_size +
                [1] *
                batch_size).to(
                image.device)
        )

        return (encoded + 1.0) / 2.0, accuracy(decoded, data), decoding_loss, classifier_loss
