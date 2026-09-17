from PyQt5.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QGraphicsOpacityEffect,
)

from datastore import datastore



class SlideshowWidget(QWidget):
    IMAGE_DURATION_MS = 5_000
    FADE_DURATION_MS = 1_500

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Digital Picture Frame")
        self.setStyleSheet("background-color: black;")

        # Current position in the slideshow.
        self.events = []
        self.event_index = 0
        self.photo_index = 0

        # ---------------------------------------------------------
        # Image labels
        #
        # Two labels occupy exactly the same space. During a
        # transition, the new image is placed on top and its
        # opacity is animated from 0 -> 1.
        # ---------------------------------------------------------

        self.current_label = QLabel(self)
        self.next_label = QLabel(self)

        #Pixmaps containing the unscaled image.
        self.current_pixmap_unscaled = None
        self.next_pixmap_unscaled = None

        for label in (self.current_label, self.next_label):
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background-color: black;")
            label.setScaledContents(False)

        self.current_label.show()
        self.next_label.hide()

        self.current_opacity = QGraphicsOpacityEffect(self.current_label)
        self.current_label.setGraphicsEffect(self.current_opacity)
        self.current_opacity.setOpacity(1.0)

        self.next_opacity = QGraphicsOpacityEffect(self.next_label)
        self.next_label.setGraphicsEffect(self.next_opacity)
        self.next_opacity.setOpacity(0.0)

        # ---------------------------------------------------------
        # Text overlay
        # ---------------------------------------------------------

        self.text_overlay = QWidget(self)
        self.text_overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 150);
            }
        """)

        self.event_label = QLabel(self.text_overlay)
        self.event_label.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
            background: transparent;
        """)

        self.placeholder_label = QLabel(self.text_overlay)
        self.placeholder_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            background: transparent;
        """)

        text_layout = QVBoxLayout(self.text_overlay)
        text_layout.setContentsMargins(20, 12, 20, 12)
        text_layout.setSpacing(2)

        text_layout.addWidget(self.event_label)
        text_layout.addWidget(self.placeholder_label)

        # ---------------------------------------------------------
        # Timer
        # ---------------------------------------------------------

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_next)

        # ---------------------------------------------------------
        # Animation
        # ---------------------------------------------------------

        self.fade_animation = QPropertyAnimation(
            self.next_opacity,
            b"opacity",
            self,
        )

        self.fade_animation.setDuration(self.FADE_DURATION_MS)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.finished.connect(self.finish_transition)

        self.load_data()

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def load_data(self):
        """
        Load events and their photos from the datastore.

        The datastore is assumed to return events in the desired
        database order.
        """

        self.events = datastore.get_events()

        if not self.events:
            self.event_label.setText("No events")
            self.placeholder_label.setText("")
            return

        # Remove events which don't contain any photos.
        self.events = [
            event
            for event in self.events
            if datastore.get_images_for_event(event["id"])
        ]

        if not self.events:
            self.event_label.setText("No photos")
            self.placeholder_label.setText("")
            return

        self.event_index = 0
        self.photo_index = 0

        self.show_current_photo()

    # ------------------------------------------------------------------
    # Current photo
    # ------------------------------------------------------------------

    def get_current_event(self):
        return self.events[self.event_index]

    def get_current_photos(self):
        event = self.get_current_event()
        return datastore.get_images_for_event(event["id"])

    def get_current_photo(self):
        photos = self.get_current_photos()
        return photos[self.photo_index]

    def show_current_photo(self):
        """
        Display the current photo immediately without a transition.
        """

        event = self.get_current_event()
        photo = self.get_current_photo()

        pixmap = QPixmap(photo["path_optimized"])

        if pixmap.isNull():
            return

        # Keep the original pixmap
        self.current_pixmap_unscaled = pixmap

        # Display a scaled copy.
        self.current_label.setPixmap(
            self.scaled_pixmap(self.current_pixmap_unscaled)
        )

        self.event_label.setText(event["title"])
        self.placeholder_label.setText("Placeholder")

        self.current_label.show()
        self.next_label.hide()

        self.current_opacity.setOpacity(1.0)
        self.next_opacity.setOpacity(0.0)

        self.timer.start(self.IMAGE_DURATION_MS)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def show_next(self):
        """
        Advance to the next photo.

        Photos are displayed in database order. Once the last photo
        of an event is reached, move to the first photo of the next
        event.
        """

        next_event_index = self.event_index
        next_photo_index = self.photo_index + 1

        current_photos = self.get_current_photos()

        if next_photo_index >= len(current_photos):
            # Move to next event.
            next_event_index += 1
            next_photo_index = 0

            if next_event_index >= len(self.events):
                # Loop back to first event.
                next_event_index = 0

        next_event = self.events[next_event_index]
        next_photos = datastore.get_images_for_event(next_event["id"])

        if not next_photos:
            return

        next_photo = next_photos[next_photo_index]

        self.start_fade(
            next_photo,
            next_event,
            next_event_index,
            next_photo_index,
        )

    # ------------------------------------------------------------------
    # Fade transition
    # ------------------------------------------------------------------

    def start_fade(
        self,
        photo,
        event,
        event_index,
        photo_index,
    ):
        """
        Put the next image into the second QLabel and fade it over
        the currently displayed image.
        """

        pixmap = QPixmap(photo["path_optimized"])

        if pixmap.isNull():
            return

        # Put the next image into the upper QLabel.
        self.next_label.setPixmap(self.scaled_pixmap(pixmap))

        # Update text before the transition.
        self.event_label.setText(event["title"])
        self.placeholder_label.setText("Placeholder")

        self.next_opacity.setOpacity(0.0)
        self.next_label.show()
        self.next_label.raise_()

        # Keep the text above both image labels.
        self.text_overlay.raise_()

        # Remember where the new image belongs.
        self.pending_event_index = event_index
        self.pending_photo_index = photo_index

        self.fade_animation.stop()
        self.fade_animation.start()

    def finish_transition(self):
        """
        Once the fade has completed, the next QLabel becomes the
        current QLabel.

        Rather than physically swapping widgets, we simply copy the
        state so that the labels continue alternating.
        """

        self.event_index = self.pending_event_index
        self.photo_index = self.pending_photo_index

        # The image which was "next" is now the visible/current image.
        self.current_label.setPixmap(self.next_label.pixmap())
        self.current_opacity.setOpacity(1.0)

        self.next_label.hide()
        self.next_opacity.setOpacity(0.0)

        # Start the 30 second display period for the new image.
        self.timer.start(self.IMAGE_DURATION_MS)

    # ------------------------------------------------------------------
    # Scaling
    # ------------------------------------------------------------------

    def scaled_pixmap(self, pixmap):
        """
        Scale the image to fit the available widget while preserving
        its aspect ratio.
        """

        return pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

    # ------------------------------------------------------------------
    # Resize handling
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        """
        Keep the two image labels and the text overlay covering the
        appropriate parts of the window.
        """

        super().resizeEvent(event)

        self.current_label.setGeometry(self.rect())
        self.next_label.setGeometry(self.rect())

        # Bottom-left text overlay.
        margin = 20
        overlay_width = min(700, self.width() - 2 * margin)
        overlay_height = 100

        self.text_overlay.setGeometry(
            margin,
            self.height() - overlay_height - margin,
            overlay_width,
            overlay_height,
        )

        # Scale from the original high-resolution pixmap.
        if self.current_pixmap_unscaled is not None:
            self.current_label.setPixmap(
                self.scaled_pixmap(self.current_pixmap_unscaled)
            )

        if self.next_pixmap_unscaled is not None:
            self.next_label.setPixmap(
                self.scaled_pixmap(self.next_pixmap_unscaled)
            )



app = QApplication([])

slideshow = SlideshowWidget()
slideshow.showFullScreen()

# Start the event loop.
app.exec()
