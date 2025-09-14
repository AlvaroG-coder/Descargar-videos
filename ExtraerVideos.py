import os
import sys
import yt_dlp
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QProgressBar, QMessageBox, QHBoxLayout,
    QFileDialog
)
from PySide6.QtCore import QThread, Signal

# Clase para manejar la descarga en un hilo aparte
class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal(str)

    # El constructor ahora recibe también la carpeta de destino
    def __init__(self, url, option, destination_folder):
        super().__init__()
        self.url = url
        self.option = option
        self.destination_folder = destination_folder # Almacena la carpeta de destino

    def run(self):
        def hook(d):
            if d['status'] == 'downloading':
                percent_str = d.get('_percent_str', '0%').replace('%', '').strip()
                if percent_str:
                    try:
                        percent = int(float(percent_str))
                        self.progress.emit(percent)
                    except ValueError:
                        pass
            elif d['status'] == 'finished':
                self.finished.emit("Descarga completa :D")

        # Configura la ruta de salida con 'outtmpl'
        # Esto le dice a yt-dlp dónde guardar el archivo
        ydl_opts = {
            'progress_hooks': [hook],
            'outtmpl': os.path.join(self.destination_folder, '%(title)s.%(ext)s')
        }
        
        if self.option == "Audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        else:
            ydl_opts.update({'format': 'best'})

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

# Interfaz gráfica principal
class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Youtube Downloader con yt-dlp + PySide6")
        self.setGeometry(200, 200, 400, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Ingresa la URL del video:")
        layout.addWidget(self.label)

        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)

        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Selecciona carpeta de destino")
        browse_button = QPushButton("📂 Buscar")
        browse_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_button)

        layout.addWidget(QLabel("📁 Carpeta de destino:"))
        layout.addLayout(folder_layout)

        self.option_box = QComboBox()
        self.option_box.addItems(["Video", "Audio"])
        layout.addWidget(self.option_box)

        self.download_btn = QPushButton("Descargar")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.progress.setValue(0)

        self.setLayout(layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if folder:
            self.folder_input.setText(folder)

    def start_download(self):
        url = self.url_input.text().strip()
        option = self.option_box.currentText()
        carpeta = self.folder_input.text().strip()

        # Verifica si la URL o la carpeta están vacías
        if not url or not carpeta: 
            QMessageBox.warning(self, "Error", "Por favor, ingresa una URL y selecciona una carpeta de destino.")
            return

        # Pasa la carpeta al hilo de descarga
        self.thread = DownloadThread(url, option, carpeta)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.show_message)
        self.thread.start()

    def show_message(self, msg):
        QMessageBox.information(self, "Estado", msg)
        self.progress.setValue(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloaderApp()
    window.show()
    sys.exit(app.exec())