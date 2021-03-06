import torch
import torch.nn as nn
from run_scripts import tensorboard_writer


class RICNN_RD(nn.Module):

    def __init__(self, num_conv_layer, num_filters,
                 filter_size, padding_size=None, use_batch_norm=None, input_size=(2, 1024, 128)):
        super(RICNN_RD, self).__init__()
        self.tensorboardx_logging_active = False
        self.forward_calls = 0
        self.max_batch_size = 8

        if use_batch_norm is not None:
            self.use_batch_norm = use_batch_norm
        else:
            self.use_batch_norm = True

        if num_conv_layer is not None:
            self.num_conv_layer = num_conv_layer
        else:
            self.num_conv_layer = 6

        if filter_size is not None:
            self.filter_size = filter_size
        else:
            self.filter_size = (3, 3)

        if padding_size is not None:
            self.padding_size = padding_size
        else:
            x_padding_same = int(self.filter_size[0]/2)
            y_padding_same = int(self.filter_size[1]/2)
            self.padding_size = (x_padding_same, y_padding_same)

        if num_filters is not None:
            self.num_filters = num_filters
        else:
            self.num_filters = 16

        self.input_size = input_size

        self.convolutions = nn.ModuleList()
        in_channels = input_size[0]

        layer = nn.Sequential(
            nn.Conv2d(in_channels, self.num_filters, kernel_size=self.filter_size, stride=1, padding=self.padding_size),
            nn.ReLU())
        self.convolutions.append(layer)

        for c in range(self.num_conv_layer-2):
            layer = nn.Sequential(
                nn.Conv2d(self.num_filters, self.num_filters, kernel_size=self.filter_size, stride=1, padding=self.padding_size),
                nn.BatchNorm2d(self.num_filters),
                nn.ReLU())
            self.convolutions.append(layer)

        layer = nn.Sequential(
            nn.Conv2d(self.num_filters, in_channels, kernel_size=self.filter_size, stride=1, padding=self.padding_size))
        self.convolutions.append(layer)

    def forward(self, x):
        num_channels = self.input_size[0]
        num_fts = self.input_size[1]
        num_ramps = self.input_size[2]

        # conv layer
        out = x.reshape((-1, 1, num_fts, num_channels * num_ramps))
        if num_channels == 2:
            out = torch.cat((out[:, :, :, :num_ramps], out[:, :, :, num_ramps:]), 1)
        for c in range(self.num_conv_layer):
            out = self.convolutions[c](out)
            if self.tensorboardx_logging_active:
                tensorboard_writer.add_histogram('conv.{}'.format(c), out.detach().cpu().numpy(), self.forward_calls)
        if num_channels == 2:
            out = torch.cat((out[:, 0], out[:, 1]), 2)
        else:
            out = out[:, 0]
        self.forward_calls += 1
        return out

    def reset(self):
        for c in range(self.num_conv_layer):
            for cc in list(self.convolutions[c]):
                try:
                    cc.reset_parameters()
                except:
                    pass

    def set_tensorboardx_logging_active(self, active):
        self.tensorboardx_logging_active = active


class MAG_CNN_RD(RICNN_RD):

    def __init__(self, num_conv_layer, num_filters, filter_size):
        super(MAG_CNN_RD, self).__init__(num_conv_layer, num_filters, filter_size,
                                      padding_size=None, use_batch_norm=None, input_size=(1, 1024, 128))
