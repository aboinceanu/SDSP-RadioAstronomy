import sys
import os
import pyqtgraph as pg
from pyqtgraph import GraphicsLayoutWidget
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtUiTools import QUiLoader
from processing import Processor
class MainApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.processor = Processor()

        loader = QUiLoader()
        loader.registerCustomWidget(GraphicsLayoutWidget)
        self.window = loader.load("design.ui")
        self.window.fileSelectBtn.clicked.connect(self.open_file_dialog)

        self.window.checkMatched.stateChanged.connect(self.update_images)
        self.window.checkMVDR.stateChanged.connect(self.update_images)
        self.window.checkClean.stateChanged.connect(self.update_images)

        self.window.spinResolution.valueChanged.connect(self.on_resolution_update)
        self.window.spinCleanIterations.valueChanged.connect(self.on_CLEAN_parameters_update)
        self.window.doubleSpinCleanLoopGain.valueChanged.connect(self.on_CLEAN_parameters_update)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Select File",
            "",
            "MATLAB Files (*.mat);; All Files (*.*)"
        )

        if file_path:
            file_name = os.path.basename(file_path)
            self.window.statusLabel.setText(f"Successfully uploaded: {file_name}")

            loaded_vars = self.processor.load_dataset(file_path)
            print(f"Loaded variables: {loaded_vars}")
        else:
            self.window.statusLabel.setText(f"Upload failed. Please try again.")

    def on_resolution_update(self, value):
        self.processor.update_res(value)
        self.update_images()

    def on_CLEAN_parameters_update(self):
        iterations = self.window.spinCleanIterations.value()
        loopgain = self.window.doubleSpinCleanLoopGain.value()

        print(f"--> GUI Registered: Iterations={iterations}, LoopGain={loopgain}")  # Check if this prints!

        self.processor.update_clean_parameters(iterations, loopgain)

        if self.window.checkClean.isChecked():
            self.update_images()

    def update_images(self):
        if self.processor.covariance_matrix is None:
            return

        self.window.imageContainer.clear()
        active_algorithms = []
        if self.window.checkMatched.isChecked(): active_algorithms.append("matched")
        if self.window.checkMVDR.isChecked(): active_algorithms.append("mvdr")
        if self.window.checkClean.isChecked(): active_algorithms.append("clean")

        num_cols = 2

        for i, algo in enumerate(active_algorithms):
            row = i // num_cols
            col = i % num_cols

            image_data = self.processor.compute_image(algorithm=algo)

            plot_item = self.window.imageContainer.addPlot(row=row, col=col)
            plot_item.setTitle(algo.upper())
            plot_item.setAspectLocked(True)

            img = pg.ImageItem(image_data)
            img.setColorMap(pg.colormap.get('inferno'))
            plot_item.addItem(img)

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    main_app = MainApplication()
    main_app.run()