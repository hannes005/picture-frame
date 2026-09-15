from PyQt5.QtWidgets import QApplication, QWidget



# You need one (and only one) QApplication instance per application. [] means: No command line agruments are passed.
app = QApplication([])

# Create a Qt widget, which will be our window.
window = QWidget()

# IMPORTANT!!!!! Windows are hidden by default.
window.show()

# Start the event loop.
app.exec()

