import sys, os
import traceback
import pyqtgraph as pg
import pyqtgraph.exporters
import matplotlib as plt
import numpy as np
from pyqtgraph import GraphicsLayoutWidget
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QRectF, QSizeF, QMarginsF
from PySide6.QtGui import QPainter, QPdfWriter, QPageSize, QPageLayout
from processing import Processor

def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


class MainApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.processor = Processor()

        loader = QUiLoader()
        loader.registerCustomWidget(GraphicsLayoutWidget)
        pg.setConfigOption('foreground', '#000000')
        self.window = loader.load(resource_path("design.ui"))
        self.window.fileSelectBtn.clicked.connect(self.open_file_dialog)
        self.window.imgExportBtn.clicked.connect(self.export_image)
        self.window.imageContainer.setBackground('#FFFFFF')

        self.window.checkMatched.stateChanged.connect(self.update_images)
        self.window.checkMVDR.stateChanged.connect(self.update_images)
        self.window.checkClean.stateChanged.connect(self.update_images)
        self.window.checkAAR.stateChanged.connect(self.update_images)

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
            self.set_status(self.window.statusLabel, f"Successfully uploaded {file_name}!", error=False)
            self.processor.load_dataset(file_path)
        else:
            self.set_status(self.window.statusLabel, "No file selected!", error=True)

    def on_resolution_update(self, value):
        self.processor.update_res(value)
        self.update_images()

    def on_CLEAN_parameters_update(self):
        iterations = self.window.spinCleanIterations.value()
        loopgain = self.window.doubleSpinCleanLoopGain.value()

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
        if self.window.checkAAR.isChecked(): active_algorithms.append("aar")

        num_cols = 2
        cmap = pg.colormap.get('inferno',source='matplotlib')
        n = len(active_algorithms)
        num_rows = (n + 1) // 2 if n > 1 else 1

        for i, algo in enumerate(active_algorithms):
            if n == 1:
                row, col, colspan = 0, 0, 4
            else:
                row = i // 2
                col = (i % 2) * 2
                if n % 2 == 1 and i == n - 1:
                    col = 1
                colspan = 2

            image_data = self.processor.compute_image(algorithm=algo)

            plot_item = self.window.imageContainer.addPlot(row=row, col=col, colspan=colspan)
            plot_item.setTitle(algo.upper())
            plot_item.setAspectLocked(True)
            plot_item.getAxis('left').setWidth(40)
            plot_item.getAxis('bottom').setHeight(30)

            h, w = image_data.shape
            plot_item.setRange(xRange=(-1,1), yRange=(-1,1), padding=0)
            plot_item.disableAutoRange()

            img = pg.ImageItem(image_data)
            img.setPos(-1, -1)
            img.setRect(QRectF(0, 0, 2, 2))
            img.setColorMap(cmap)
            lo = np.nanmin(image_data)
            hi = np.nanpercentile(image_data, 99.5)  # or np.nanmax(image_data)

            bar = pg.ColorBarItem(values=(lo, hi), colorMap=cmap,
                                  interactive=False, label='Power')
            bar.setImageItem(img, insert_in=plot_item)
            plot_item.addItem(img)

        layout = self.window.imageContainer.ci.layout
        for c in range(4):
            layout.setColumnStretchFactor(c, 1)
        for r in range(2):
            layout.setRowStretchFactor(r, 1 if r < num_rows else 0)

    def export_image(self):
        if self.processor.covariance_matrix is None:
            self.set_status(self.window.exportStatusLabel, "Nothing to export: No data", error=True)
            return
        if not self.window.imageContainer.ci.items:
            self.set_status(self.window.exportStatusLabel, "Nothing to export: No algorithm selected", error=True)

        export_file_path, selected_file_type = QFileDialog.getSaveFileName(
            self.window,
            "Export Image",
            "sky image.png",
            "PNG (*.png);; JPG (*.jpg);; PDF (*.pdf)"
        )
        if not export_file_path:
            return

        ext = os.path.splitext(export_file_path)[1].lower()

        if not ext:
            ext = "." + selected_file_type.split("*.")[1].rstrip(")")
            export_file_path += ext

        try:
            if ext == ".pdf":
                self.export_pdf(export_file_path)
            elif ext == (".png", ".jpg", ".jpeg"):
                exporter = pg.exporters.ImageExporter(self.window.imageContainer.scene())
                exporter.parameters()['width'] = 2000
                exporter.export(export_file_path)
            else:
                self.set_status(self.window.exportStatusLabel, f"Invalid file type: {ext}", error=True)
                return

        except Exception as e:
            traceback.print_exc()
            self.set_status(self.window.exportStatusLabel, f"Failed to export image: {e}", error=True)
            return
        self.set_status(self.window.exportStatusLabel, f"Exported image {os.path.basename(export_file_path)}", error=False)

    def render_scene(self, painter, target):
        view = self.window.imageContainer
        painter.fillRect(target, view.backgroundBrush())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene = view.scene()
        scene.render(painter, target, scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def export_pdf(self, path):
        view = self.window.imageContainer
        rect = view.scene().sceneRect()
        dpi = int(view.logicalDpiX())

        writer = QPdfWriter(path)
        writer.setResolution(dpi)
        writer.setPageSize(QPageSize(
            QSizeF(rect.width() / dpi * 25.4, rect.height() / dpi * 25.4),  # px -> mm
            QPageSize.Unit.Millimeter))
        writer.setPageMargins(QMarginsF(0, 0, 0, 0))

        painter = QPainter(writer)
        try:
            self.render_scene(painter, QRectF(0, 0, writer.width(), writer.height()))
        finally:
            painter.end()

    def set_status(self, label, text, error=False):
        label.setText(text)
        label.setStyleSheet("color: #c62828;" if error else "color: #2e7d32;")

    def run(self):
        self.window.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    main_app = MainApplication()
    main_app.run()