import sys
import serial
import time

import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
import multiprocessing as mp

from pyqtgraph.Qt import QtCore, QtGui
from brewer2mpl import qualitative
from scipy import signal


class TimeData(QtGui.QMainWindow):
    def __init__(self, parent=None, Qdata=[]):
        super(TimeData, self).__init__(parent)

        self.queue = Qdata
        self.numPoints = 200*3
        self.timeCount = 0
        self.xcount = 0

        # Set up GUI configuration
        self.mainbox = QtGui.QWidget()
        self.setCentralWidget(self.mainbox)
        self.mainbox.setLayout(QtGui.QVBoxLayout())

        self.canvas = pg.GraphicsLayoutWidget()  # create GrpahicsLayoutWidget obejct
        self.mainbox.layout().addWidget(self.canvas)

        self.label = QtGui.QLabel()  # placeholder Qlabel object to display framerate
        self.mainbox.layout().addWidget(self.label)

        #  Set up plot
        self.analogPlot = self.canvas.addPlot(title='Time Data',row=1,col=1)
        self.analogPlot2 = self.canvas.addPlot(title='Spectra',row=2,col=1)
        # self.analogPlot.setYRange(-100, 1123)  # set axis range
        # self.analogPlot.setXRange(-100, 1123)

        self.analogPlot.showGrid(x=True, y=True, alpha=0.5)
        self.analogPlot2.showGrid(x=True, y=True, alpha=0.5)
        self.analogPlot2.setLogMode(x=None,y=True)

        x_axis = self.analogPlot.getAxis('bottom')
        y_axis = self.analogPlot.getAxis('left')
        x_axis2 = self.analogPlot2.getAxis('bottom')
        y_axis2 = self.analogPlot2.getAxis('left')

        x_axis.setLabel(text='Time [s]')  # set axis labels
        y_axis.setLabel(text='Acceleration [m/s^2]')
        x_axis2.setLabel(text='Frequency [Hz]')  # set axis labels
        y_axis2.setLabel(text='Amplitude [(m/s^2)/Hz]')

        self.y = np.array([], dtype=float)
        self.x = np.array([], dtype=float)

        bmap = qualitative.Dark2[3]
        self.pen = pg.mkPen(color=bmap.colors[0])
        self.drawplot = self.analogPlot.plot(pen=self.pen)
        self.drawplot2 = self.analogPlot2.plot(pen=self.pen)

        # initialize frame counter variables
        self.counter = 0
        self.fps = 0.
        self.lastupdate = time.time()

        # set up image exporter (necessary to be able to export images)
        QtGui.QApplication.processEvents()
        self.exporter = pg.exporters.ImageExporter(self.canvas.scene())
        self.image_counter = 1

        # start updating
        self._update()

    def _framerate(self):
        now = time.time()  # current time since the epoch in seconds
        dt = (now - self.lastupdate)
        if dt <= 0:
            dt = 0.000000000001
        fps2 = 1.0 / dt
        self.lastupdate = now
        self.fps = self.fps * 0.9 + fps2 * 0.1
        tx = 'Mean Frame Rate:  {fps:.3f} FPS'.format(fps=self.fps)
        self.label.setText(tx)
        QtCore.QTimer.singleShot(1, self._update)
        self.counter += 1

    def _save_image(self):
        filename = 'img' + ("%04d" % self.image_counter) + '.png'
        self.exporter.export(filename)
        self.image_counter += 1

    def calcSpectra(self):
        # power Spectra Density
        fs = 150
        if len(self.y) < 2048:
            nfft = len(self.y)
        else:
            nfft = 2048

        f, Pxx_den = signal.welch(self.y.T, fs, 'hann', nperseg=nfft)
        return f, Pxx_den

    def _update(self):

        sample = queue.get()
        self.x = sample["x"]
        self.y = sample["y"]

        # Calculate spectra of current DataY
        self.f, self.psd = self.calcSpectra()

        #self.drawplot.setData(self.x, self.y)
        self.drawplot.setData(self.x, self.y)
        self.drawplot2.setData(self.f, self.psd)

        self._framerate()  # update framerate, see corresponding function
        self.timeCount += 1

        # self._framerate()  # update framerate, see corresponding function
        # self.timeCount += 1
        # self._save_image()    # uncomment this to save each frame as an .png image in your current directory. Note that the framerate drops significantly by doing so

def getMCUData(queue):
        ser = serial.Serial(port='COM12')
        ser.flushInput()
        print('Serial connected')

        y = np.array([], dtype=float)
        x = np.array([], dtype=float)
        xcount = 0
        numPoints = 150 * 10
        sensor_number = 0
        previous_time = time.time()


        while True: #self.ser.in_waiting:
            try:
                ser_bytes = ser.readline()
                #print(f"Checking Byte Size {len(ser_bytes)}")
                if len(ser_bytes) > 5:
                    try:
                        data = ser_bytes[0:len(ser_bytes) - 3].decode("utf-8")
                        Darray = np.fromstring(data, dtype=float, sep=',')
                        #queue.put(Darray, block=False)
                        #print(f"Darray {Darray}")

                        x = np.append(x, xcount)
                        if x.size >= numPoints:
                            x = np.append(x[1:numPoints], xcount)
                        xcount += 1
                        #print(f"DataX buffer {self.x}")

                        y = np.append(y, Darray[sensor_number])
                        if y.size >= numPoints:
                            y = np.append(y[1:numPoints], Darray[sensor_number])
                        #queue.put(y,block=False)
                        now = time.time()
                        #print(f"Sample Rate {1/(previous_time-now)}")
                        previous_time = now
                        queue.put_nowait({"x": x, "y": y})
                        #print(f"DataY buffer {y}")

                    except:
                        continue
            except:
                continue


if __name__ == '__main__':
    max_size = 1000
    queue = mp.JoinableQueue(max_size)
    task = mp.Process(target=getMCUData,
                      args=(queue,),
                      daemon=True)
    task.start()

    app = QtGui.QApplication(sys.argv)
    plot = TimeData(Qdata=queue)
    plot.show()
    sys.exit(app.exec_())

