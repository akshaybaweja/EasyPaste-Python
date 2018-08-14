from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import time
import traceback, sys


class WorkerSignals(QObject):

	finished = pyqtSignal()
	error = pyqtSignal(tuple)
	result = pyqtSignal(object)
	progress = pyqtSignal(int)


class Worker(QRunnable):

	def __init__(self, fn, *args, **kwargs):
		super(Worker, self).__init__()

		# Store constructor arguments (re-used for processing)
		self.fn = fn
		self.args = args
		self.kwargs = kwargs
		self.signals = WorkerSignals()

		# Add the callback to our kwargs
		self.kwargs['progress_callback'] = self.signals.progress

	@pyqtSlot()
	def run(self):

		try:
			result = self.fn(*self.args, **self.kwargs)
		except:
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			self.signals.result.emit(result)  # Return the result of the processing
		finally:
			self.signals.finished.emit()  # Done

class SystemTrayWindow():

	def __init__(self):

		self.icon = QIcon("save2.png")

		self.tray = QSystemTrayIcon()
		self.tray.setIcon(self.icon)
		self.tray.setVisible(True)

		self.menu = QMenu()

		self.quit_button = QAction("Quit")
		self.quit_button.triggered.connect(self.exit)

		self.about_button = QAction("About")
		self.about_button.triggered.connect(self.about)

		self.menu.addAction(self.about_button)
		self.menu.addSeparator()
		self.menu.addAction(self.quit_button)
		

		self.tray.setContextMenu(self.menu)

	def exit(self):
		sys.exit()

	def about(self):
		pass


class MainWindow(QMainWindow):


	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)

		self.counter = 0

		layout = QVBoxLayout()

		self.l = QLabel("Start")
		b = QPushButton("DANGER!")
		b.pressed.connect(self.oh_no)

		layout.addWidget(self.l)
		layout.addWidget(b)

		w = QWidget()
		w.setLayout(layout)

		self.setCentralWidget(w)

		self.show()

		self.threadpool = QThreadPool()
		print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

		self.timer = QTimer()
		self.timer.setInterval(1000)
		self.timer.timeout.connect(self.recurring_timer)
		self.timer.start()

	def progress_fn(self, n):
		print("%d%% done" % n)

	def execute_this_fn(self, progress_callback):
		for n in range(0, 5):
			time.sleep(1)
			progress_callback.emit(n*100/4)

		return "Done."

	def print_output(self, s):
		print(s)

	def thread_complete(self):
		print("THREAD COMPLETE!")

	def oh_no(self):
		# Pass the function to execute
		worker = Worker(self.execute_this_fn) # Any other args, kwargs are passed to the run function
		worker.signals.result.connect(self.print_output)
		worker.signals.finished.connect(self.thread_complete)
		worker.signals.progress.connect(self.progress_fn)

		# Execute
		self.threadpool.start(worker)


	def recurring_timer(self):
		self.counter +=1
		self.l.setText("Counter: %d" % self.counter)


app = QApplication([])

# window = MainWindow()
tray = SystemTrayWindow()

app.exec_()