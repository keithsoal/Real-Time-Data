import sys
import time
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
import serial
from brewer2mpl import qualitative
from scipy import signal


class ModeTRACK(QtGui.QMainWindow):
    def __init__(self, parent=None, serialObj=[]):
        super(ModeTRACK, self).__init__(parent)

        self.arduinoData = serialObj
        self.counter = 0

        # Set up GUI configuration
        self.mainbox = QtGui.QWidget()
        self.setCentralWidget(self.mainbox)
        self.mainbox.setLayout(QtGui.QVBoxLayout())

        self.canvas = pg.GraphicsLayoutWidget()  # create GrpahicsLayoutWidget obejct
        self.mainbox.layout().addWidget(self.canvas)

        self.label = QtGui.QLabel()  # placeholder Qlabel object to display framerate
        self.mainbox.layout().addWidget(self.label)

        #  Set up plot
        self.analogPlot = self.canvas.addPlot(title='Real-time plot')
        # self.analogPlot.setYRange(-100, 1123)  # set axis range
        # self.analogPlot.setXRange(-100, 1123)
        self.analogPlot.showGrid(x=True, y=True, alpha=0.5)
        x_axis = self.analogPlot.getAxis('bottom')
        y_axis = self.analogPlot.getAxis('left')

        x_axis.setLabel(text='x-axis reading')  # set axis labels
        y_axis.setLabel(text='y-axis reading')

        # ticks = [[(0, '0'), (1023, '1023')], [(200, '200'), (400, '400'), (600, '600'), (800, '800')]]
        # x_axis.setTicks(ticks)  # set ticks manually (first major-ticks than minor-ticks)
        # y_axis.setTicks(ticks)

        # initialize sensor data variables
        self.numPoints = 40  # number of points that should be plottet at the same time stamp
        self.max_number_families = 300
        self.x = np.array([], dtype=int)  # create empty numpy array to store xAxis data
        # Check if multiple channels are recorded
        while (self.arduinoData.inWaiting() == 0):  # wait until there is data available
            pass  # do nothing
        invalid_data = True
        while (invalid_data):
            arduinoString = self.arduinoData.readline()  # read the text line from serial port
            if sys.version_info >= (3, 0):
                arduinoString = arduinoString.decode('utf-8', 'backslashreplace')
            dataArray = arduinoString.split(',')
            if type(dataArray) != str:
                invalid_data = False

        d = np.array(dataArray, dtype=np.float32)
        # data = np.array(dataArray, dtype=np.float32)
        print(f"D SIZE {(d.size / 2)}")
        if d.size > 1:
            yAxis = d[0:int(d.size / 2)]
            fam_index = d[int(d.size / 2):]
        else:
            yAxis = d
            fam_index = 1

        if d.size == 1:
            self.y = np.array([], dtype=int)  # create empty numpy array to store yAxis data
        else:
            self.y = np.empty((0, self.max_number_families), np.float32)

        # print(f"d vector {d.size}")

        bmap = qualitative.Dark2[yAxis.size]
        self.drawplot = {}
        self.pen = {}
        print(f"YAXIS SIZE {yAxis.size}")
        for r in range(yAxis.size):
            self.pen[r] = pg.mkPen(color=bmap.colors[r], style=QtCore.Qt.DashLine)
            print(f"bmap output {type(bmap.colors[r])}")
            self.drawplot[r] = self.analogPlot.plot(pen=self.pen[r], symbol='s', symbolBrush=tuple(bmap.colors[r]),
                                                    symbolPen=tuple(bmap.colors[r]))  # yellow line plot ('b')

        print(f"COULD THIS BE IT {len(self.drawplot)}")
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

    def _update(self):
        print(f"update triggered")
        while (self.arduinoData.inWaiting() == 0):  # wait until there is data available
            pass  # do nothing
        arduinoString = self.arduinoData.readline()  # read the text line from serial port
        if sys.version_info >= (3, 0):
            arduinoString = arduinoString.decode('utf-8', 'backslashreplace')
        dataArray = arduinoString.split(',')  # split it into an array

        xAxis = self.counter
        # xAxis = int(dataArray[1])  # convert first element to an integer
        # yAxis = int(dataArray[0])  # convert and flip yAxis signal
        data = np.array(dataArray, dtype=np.float32)
        if data.size > 1:
            yAxis = data[0:int(data.size / 2)]
            fam_index = data[int(data.size / 2):]
            # print(f"data {data}")
            # print(f"yAxis {yAxis}")
            # print(f"fam_index {fam_index}")
        else:
            yAxis = data
            fam_index = 1
        print(f"data {yAxis.shape}")

        self.x = np.append(self.x, xAxis)  # append new data point to the array
        if self.x.size >= self.numPoints:  # make sure that the size of the array includes the most recent data points
            self.x = np.append(self.x[1:self.numPoints], xAxis)
        else:
            self.x = np.append(self.x, xAxis)

        if yAxis.size == 1:
            self.y = np.append(self.y, yAxis)  # append new data point to the array
            if self.y.size >= self.numPoints:  # make sure that the size of the array includes the most recent data points
                self.y = np.append(self.y[1:self.numPoints], yAxis)
            else:
                self.y = np.append(self.y, yAxis)
        else:
            print(f"DRAWPLOT HERE {len(self.drawplot)}")
            print(f"yAxisSIZE HERE {yAxis.size}")
            if len(self.drawplot) < yAxis.size:
                bmap = qualitative.Dark2[yAxis.size]
                print(f"DRAWPLOT range {range(yAxis.size - len(self.drawplot))}")
                for r in range(yAxis.size - len(self.drawplot)):
                    print(f"r in loop {r}")
                    print(f"range index {len(self.drawplot) + 1 + r}")
                    self.pen[len(self.drawplot) + r] = pg.mkPen(
                        color=bmap.colors[len(self.drawplot) + r])  # style=QtCore.Qt.DashLine
                    self.drawplot[len(self.drawplot) + r] = self.analogPlot.plot(pen=self.pen[len(self.drawplot) + r],
                                                                                 symbol='s',
                                                                                 symbolBrush=tuple(bmap.colors[len(
                                                                                     self.drawplot) + r]),
                                                                                 symbolPen=tuple(bmap.colors[len(
                                                                                     self.drawplot) + r]))  # yellow line plot ('b')

            # concat_z = np.zeros([1,self.y.shape[1]-yAxis.size])
            # full_row = np.append(yAxis, concat_z)
            # reshape_row = full_row[]

            concat_row = np.zeros(self.y.shape[1])
            # print(f"fam_index {int(fam_index.tolist())}")
            print(f"yAxis {yAxis}")
            fam_int = fam_index.astype(int)
            concat_row[fam_int.tolist()] = yAxis
            # print(f"sort_row {concat_row}")

            # np.place(arr, arr > 2, [44, 55])

            # self.y = np.vstack([self.y, np.append(yAxis, concat_z)])
            self.y = np.vstack([self.y, concat_row])
            if self.y.shape[
                0] >= self.numPoints:  # make sure that the size of the array includes the most recent data points
                self.y = np.vstack([self.y[1:self.numPoints, :], concat_row])
            else:
                self.y = np.vstack([self.y, concat_row])

        self.y = self.y.astype('float')
        self.y[self.y == 0] = 'nan'
        print(f"FAM_INDEX {fam_index}")
        print(f"LEN DRAWPLOT {len(self.drawplot)}")
        for r in range(len(self.drawplot)):
            self.drawplot[r].setData(self.x, self.y[:, r])  # draw current data set
            # self.drawplot[fam_index[r]].setData(self.x, self.y[:,r])
        # self.drawplot.setData(self.x, self.y[:, 1])

        self._framerate()  # update framerate, see corresponding function
        self.counter += 1

        # self._save_image()    # uncomment this to save each frame as an .png image in your current directory. Note that the framerate drops significantly by doing so

class TimeData(QtGui.QMainWindow):
    def __init__(self, parent=None, serialObj=[]):
        super(TimeData, self).__init__(parent)

        self.arduinoData = serialObj
        self.numPoints = 200*10
        self.timeCount = 0

        # Set up GUI configuration
        self.mainbox = QtGui.QWidget()
        self.setCentralWidget(self.mainbox)
        self.mainbox.setLayout(QtGui.QVBoxLayout())

        self.canvas = pg.GraphicsLayoutWidget()  # create GrpahicsLayoutWidget obejct
        self.mainbox.layout().addWidget(self.canvas)

        self.label = QtGui.QLabel()  # placeholder Qlabel object to display framerate
        self.mainbox.layout().addWidget(self.label)

        #  Set up plot
        self.analogPlot = self.canvas.addPlot(title='Real-time plot')
        # self.analogPlot.setYRange(-100, 1123)  # set axis range
        # self.analogPlot.setXRange(-100, 1123)
        self.analogPlot.showGrid(x=True, y=True, alpha=0.5)
        x_axis = self.analogPlot.getAxis('bottom')
        y_axis = self.analogPlot.getAxis('left')

        x_axis.setLabel(text='x-axis reading')  # set axis labels
        y_axis.setLabel(text='y-axis reading')

        self.y = np.array([], dtype=float)
        self.x = np.array([], dtype=float)

        bmap = qualitative.Dark2[3]
        self.pen = pg.mkPen(color=bmap.colors[0])
        self.drawplot = self.analogPlot.plot(pen=self.pen)


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

    def _update(self):

        while (self.arduinoData.inWaiting() == 0):  # wait until there is data available
            pass  # do nothing
        arduinoString = self.arduinoData.readline()  # read the text line from serial port
        if sys.version_info >= (3, 0):
            arduinoString = arduinoString.decode('utf-8', 'backslashreplace')
        dataArray = arduinoString.split(',')  # split it into an array

        xAxis = self.timeCount

        try:
            yAxis = np.array(dataArray, dtype=np.float32)

            self.x = np.append(self.x, xAxis)  # append new data point to the array
            if self.x.size >= self.numPoints:  # make sure that the size of the array includes the most recent data points
                self.x = np.append(self.x[1:self.numPoints], xAxis)

            if yAxis.size == 1:
                self.y = np.append(self.y, yAxis)  # append new data point to the array
                if self.y.size >= self.numPoints:  # make sure that the size of the array includes the most recent data points
                    self.y = np.append(self.y[1:self.numPoints], yAxis)

            self.drawplot.setData(self.x, self.y)  # draw current data set

            self._framerate()  # update framerate, see corresponding function
            self.timeCount += 1

        except Exception:
            print(f"lost some data")
            pass



        # self._save_image()    # uncomment this to save each frame as an .png image in your current directory. Note that the framerate drops significantly by doing so

class Spectra(QtGui.QMainWindow):
    def __init__(self, parent=None, serialObj=[]):
        super(Spectra, self).__init__(parent)

        self.arduinoData = serialObj
        self.numPoints = 200*10
        self.timeCount = 0
        self.f = np.array([])
        self.spec = np.array([])
        self.timestamp = time.time()

        # Set up GUI configuration
        self.mainbox = QtGui.QWidget()
        self.setCentralWidget(self.mainbox)
        self.mainbox.setLayout(QtGui.QVBoxLayout())

        self.canvas = pg.GraphicsLayoutWidget()  # create GrpahicsLayoutWidget obejct
        self.mainbox.layout().addWidget(self.canvas)

        self.label = QtGui.QLabel()  # placeholder Qlabel object to display framerate
        self.mainbox.layout().addWidget(self.label)

        #  Set up plot
        self.analogPlot = self.canvas.addPlot(title='Real-time plot')
        self.analogPlot.setYRange(0, 3)  # set axis range
        # self.analogPlot.setXRange(-100, 1123)
        self.analogPlot.showGrid(x=True, y=True, alpha=0.5)
        x_axis = self.analogPlot.getAxis('bottom')
        y_axis = self.analogPlot.getAxis('left')

        x_axis.setLabel(text='x-axis reading')  # set axis labels
        y_axis.setLabel(text='y-axis reading')
        self.analogPlot.setLogMode(False, True)

        self.y = np.array([], dtype=float)
        self.x = np.array([], dtype=float)

        bmap = qualitative.Dark2[3]
        self.pen = pg.mkPen(color=bmap.colors[0])
        self.drawplot = self.analogPlot.plot(pen=self.pen)


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

    def _update(self):
        #current_time = time.time()
        #print(f"Aquired sample rate {1 / (current_time - self.lastupdate)}")
        #self.lastupdate = current_time

        while (self.arduinoData.inWaiting() == 0):  # wait until there is data available
            pass  # do nothing
        arduinoString = self.arduinoData.readline()  # read the text line from serial port
        if sys.version_info >= (3, 0):
            arduinoString = arduinoString.decode('utf-8', 'backslashreplace')
        dataArray = arduinoString.split(',')  # split it into an array
        print(f"dataArray {dataArray}")
        print(f"dataArray length {len(dataArray[0])}")
        xAxis = self.timeCount

        # self._framerate()  # update framerate, see corresponding function
        # self.timeCount += 1

        if 3 < len(dataArray[0]) < 8:
            yAxis = np.array(dataArray, dtype=np.float32)

            if yAxis.size == 1:
                self.y = np.append(self.y, yAxis)  # append new data point to the array
                if self.y.size >= self.numPoints:  # make sure that the size of the array includes the most recent data points
                    self.y = np.append(self.y[1:self.numPoints], yAxis)

            windowLength = 1024
            if self.y.size > windowLength:
                # compute stectra
                # self.f, self.spec = signal.welch(self.y, fs=200, window='hann', nperseg=windowLength,
                #                                  noverlap=(windowLength / 100) * 30)
                print(f"self.y size {self.y.size}")
                self.f, self.spec = signal.welch(self.y, fs=200, nperseg=1024)
                # print(f"spectra {self.spec}")
                print(f"Delta f {self.f[1]}")
                #print(f"Aquired sample rate {1/(time.time()-self.lastupdate)}")
                #self.lastupdate = time.time()

                self.drawplot.setData(self.f, self.spec)  # draw current data set

            self._framerate()  # update framerate, see corresponding function
            self.timeCount += 1



        # self._save_image()    # uncomment this to save each frame as an .png image in your current directory. Note that the framerate drops significantly by doing so

if __name__ == '__main__':
    arduinoData = serial.Serial("COM8",9600);  # 9600 or 115200 Creating our serial object named arduinoData, make sure that port and baud rate is set up according to your arduino data stream
    arduinoData.flush()
    app = QtGui.QApplication(sys.argv)
    #plot = ModeTRACK(serialObj=arduinoData)
    #plot = TimeData(serialObj=arduinoData)
    plot = Spectra(serialObj=arduinoData)
    plot.show()
    sys.exit(app.exec_())