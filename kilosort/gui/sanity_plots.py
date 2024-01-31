
# import matplotlib
# matplotlib.use('Qt5Agg')
# import matplotlib.pyplot as plt
# #plt.style.use('dark_background')
# from matplotlib.backends.backend_qt5agg import (
#     FigureCanvasQTAgg, NavigationToolbar2QT
#     )
# from matplotlib.figure import Figure
import pyqtgraph as pg
import matplotlib
import numpy as np
from numba import njit
from numba.typed import List
import torch
from PyQt5 import QtWidgets


_COLOR_CODES = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
# Adapted from https://www.pythonguis.com/tutorials/plotting-matplotlib/
# class MplCanvas(FigureCanvasQTAgg):
#     def __init__(self, parent, nrows, ncols, width=5, height=4, dpi=100):
#         self.parent = parent
#         fig = Figure(figsize=(width,height), dpi=dpi, layout='constrained')
#         self.axes = fig.subplots(nrows, ncols)
#         super().__init__(fig)


class PlotWindow(QtWidgets.QWidget):
    def __init__(self, *args, title=None, width=500, height=400, **kwargs):
        super().__init__()
        if title is not None:
            self.setWindowTitle(title)
        self.setFixedWidth(width)
        self.setFixedHeight(height)

        layout = QtWidgets.QVBoxLayout()
        self.plot_widget = pg.GraphicsLayoutWidget(parent=self)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

        self.hide()


# TODO: Axis labels don't actually show up anywhere, still debugging

def plot_drift_amount(plot_window, dshift, settings):
    # Drift amount for each block of probe over time
    p1 = plot_window.plot_widget.addPlot(
        row=0, col=0, labels={'left': 'Depth shift (microns)', 'bottom': 'Time (s)'}
        )
    fs = settings['fs']
    NT = settings['batch_size']
    t = np.arange(dshift.shape[0])*(NT/fs)

    for i in range(dshift.shape[1]):
        color = _COLOR_CODES[i % len(_COLOR_CODES)]
        p1.plot(t, dshift[:,i], pen=color)

    plot_window.show()


def plot_drift_scatter(plot_window, st0, settings):

    # TODO: this "works", but there's no way to color by amplitude that I've
    #       been able to find

    # p1 = plot_window.plot_widget.addPlot(
    #     row=0, col=0, labels={'left': 'Depth (microns)', 'bottom': 'Time (s)'}
    # )
    # points = p1.plot(st0[:,0], st0[:,5], pen=None, symbol='o')
    # points.setSymbolSize(1)
    # plot_window.show()


    # TODO: Looks like this way is almost working? But it's so slow it's not
    #       worth doing, and I still can't get the points to actually show up.

    # # Invert color scheme for this plot, want white background
    # pg.setConfigOption('background', 'w')
    # pg.setConfigOption('foreground', 'k')

    # p1 = plot_window.plot_widget.addPlot(
    #     row=0, col=0, labels={'left': 'Depth (microns)', 'bottom': 'Time (s)'}
    # )
    # scatter = pg.ScatterPlotItem()

    # # Build list of spot dicts to add to scatter.
    # # TODO: Simpler way to do this? Couldn't figure out another way to color
    # #       by a 3rd variable.
    # x = st0[:,0]  # spike time
    # y = st0[:,5]  # depth of spike center
    # z = st0[:,2]  # spike amplitude

    # # Apply colormap and log normalization to amplitude
    # cm = matplotlib.colormaps['Greys']
    # LN = matplotlib.colors.LogNorm(vmin=10, vmax=100, clip=True)
    # print(f'min max before: {z.min()}, {z.max()}')
    # z = np.array([cm(LN(a)) for a in z])
    # print(f'values after: {z[0]}, {z[723]}, {z[-100]}')

    # # Build list of spots for plot
    # spots = [
    #     {'pos': (x[i], y[i]), 'size': 1, 'pen': {'color': z[i]}, 'brush': z[i]}
    #     for i in range(x.size)
    # ]

    # # Add spots to plot area
    # scatter.addPoints(spots)
    # p1.addItem(scatter)
    # plot_window.show()

    # pg.setConfigOption('background', 'k')
    # pg.setConfigOption('foreground', 'w')

    # TODO: third option, try making it into a heatmap

    # NOTE: No... this is dumb. Wouldn't be able to load the full thing into
    #       memory, would have to do it in batches similar to the raw traces and
    #       that's getting way too complicated for a simple scatterplot.
    # p1 = plot_window.plot_widget.addPlot(
    #     row=0, col=0, labels={'left': 'Depth (microns)', 'bottom': 'Time (s)'}
    # )
    # x = st0[:,0]  # spike time in seconds
    # y = st0[:,5]  # depth of spike center in microns
    # z = st0[:,2]  # spike amplitude
    # # Convert to heatmap with 5ms time bins, 5 micron depth bins
    # nx = int(np.ceil((x.max() - x.min())/0.005))
    # _, x_bins = np.histogram(x, bins=nx)
    # a = _make_heatmap(x, y, z, x_bin=0.005, y_bin=5)


@njit
def _make_heatmap(x, y, z, x_bins, y_bins):
    # Assumes x, y, z are all 1-dimensional and equal length
    
    for i in x.size:
        pass


def plot_diagnostics(plot_window, wPCA, Wall0, clu0, settings):
    # Temporal features (top left)
    p1 = plot_window.plot_widget.addPlot(
        row=0, col=0, labels={'bottom': 'Time (s)'}
        )
    p1.setTitle('Temporal Features')
    t = np.arange(wPCA.shape[1])/(settings['fs']/1000)
    for i in range(wPCA.shape[0]):
        color = _COLOR_CODES[i % len(_COLOR_CODES)]
        p1.plot(t, wPCA[i,:], pen=color)

    # Spatial features (top right)
    p2 = plot_window.plot_widget.addPlot(
        row=0, col=1, labels={'bottom': 'Unit Number', 'left': 'Channel Number'}
        )
    p2.setTitle('Spatial Features')
    features = torch.linalg.norm(Wall0, dim=2).cpu().numpy()
    img = pg.ImageItem(image=features.T)
    p2.addItem(img)

    # Comput spike counts and mean amplitudes
    n_units = int(clu0.max()) + 1
    spike_counts = np.zeros(n_units)
    for i in range(n_units):
        spike_counts[i] = (clu0[clu0 == i]).size
    mean_amp = torch.linalg.norm(Wall0, dim=(1,2)).cpu().numpy()

    # Unit amplitudes (bottom left)
    p3 = plot_window.plot_widget.addPlot(
        row=1, col=0, labels={'bottom': 'Unit Number', 'left': 'Amplitude (a.u.)'}
        )
    p3.setTitle('Unit Amplitudes')
    p3.plot(mean_amp)

    # Amplitude vs Spike Count (bottom right)
    p4 = plot_window.plot_widget.addPlot(
        row=1, col=1,
        labels={'bottom': 'Log(1 + Spike Count)', 'left': 'Amplitude (a.u.)'}
        )
    p4.setTitle('Amplitude vs Spike Count')
    p4.plot(np.log(1 + spike_counts), mean_amp, pen=None, symbol='o')

    # Finished, draw plot
    plot_window.show()
