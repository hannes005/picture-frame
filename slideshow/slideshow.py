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

        # Current position in the slideshow and next position to show.
        self.events = []
        self.current_event_index = 0
        self.current_image_index = 0
        self.next_event_index = 0
        self.next_image_index = 0

        #Pixmaps containing the unscaled image. 
        #Scaled versions will be assigned to the image_labels when loading or resizing an image.
        self.current_image_pixmap_unscaled = None
        self.nnext_image_pixmap_unscaled = None

        # ---------------------------------------------------------
        # Image labels
        #
        # Two labels occupy exactly the same space. During a
        # transition, the new image is placed on top and its
        # opacity is animated from 0 -> 1.
        # ---------------------------------------------------------

        self.current_image_label = QLabel(self)
        self.next_image_label = QLabel(self)
        
        for label in (self.current_image_label, self.next_image_label):
            label.setAlignment(Qt.AlignCenter) 
            label.setStyleSheet("background-color: black;")
            label.setScaledContents(False)
            pass

        self.current_image_label.show()
        self.next_image_label.hide()

        self.current_image_label_opacity = QGraphicsOpacityEffect(self.current_image_label)
        self.current_image_label.setGraphicsEffect(self.current_image_label_opacity)
        self.current_image_label_opacity.setOpacity(1.0)

        self.next_image_label_opacity = QGraphicsOpacityEffect(self.next_image_label)
        self.next_image_label.setGraphicsEffect(self.next_image_label_opacity)
        self.next_image_label_opacity.setOpacity(0.0)

        # ---------------------------------------------------------
        # Text overlay
        # ---------------------------------------------------------

        self.text_overlay = QWidget(self)
        self.text_overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 00);
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
        self.timer.timeout.connect(self.show_next_image)

        # ---------------------------------------------------------
        # Animation
        # ---------------------------------------------------------

        self.fade_animation = QPropertyAnimation(
            self.next_image_label_opacity,
            b"opacity",
            self,
        )

        self.fade_animation.setDuration(self.FADE_DURATION_MS)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.finished.connect(self.finish_transition)

        # ---------------------------------------------------------
        # Load Data and Display first image
        # ---------------------------------------------------------

        self.show_current_image()


    def get_current_event(self):
        try:
            return self.events[self.current_event_index]
        except:
            return None

    def get_next_event(self):
        try:
            return self.events[self.next_event_index]
        except:
            return None

    def get_current_image(self):
        try:
            event = self.get_current_event()
            images = datastore.get_images_for_event(event["id"])
            image = images[self.current_image_index]
            return image
        except:
            return None

    def get_next_image(self):
        try:
            event = self.get_next_event()
            images = datastore.get_images_for_event(event["id"])
            image = images[self.next_image_index]
            return image
        except:
            return None



    def load_data(self):
        """
        Load events and their photos from the datastore.
        """

        self.events = datastore.get_events()


        # Stop, if there are no events.
        if not self.events:
            return

        #Remove events which don't contain any photos.
        self.events = [
            event
            for event in self.events
            if datastore.get_images_for_event(event["id"])
        ]

        # Stop, if there are no events left after removing empty events
        if not self.events:
            return

        print(self.events)

        # At this point there is at least 1 event with at least 1 image in it.



    def show_current_image(self):
        """
        Display the current photo immediately without a transition.
        """

        #Get a fresh reload of data from the db in case of changes just made.
        self.load_data()

        # Stop, if there are no events.
        current_event = self.get_current_event()
        if not current_event:
            self.event_label.setText("No images")
            self.placeholder_label.setText("")
            self.timer.start(self.IMAGE_DURATION_MS)
            return

        current_image = self.get_current_image()
        # Stop, if there are no photos
        if not current_image:
            self.event_label.setText("No images")
            self.placeholder_label.setText("")
            self.timer.start(self.IMAGE_DURATION_MS)
            return

        # Load image to "unscaled" pixmap.
        if QPixmap(current_image["path_optimized"]).isNull():
            self.timer.start(self.IMAGE_DURATION_MS)
            return
        self.current_image_pixmap_unscaled = QPixmap(current_image["path_optimized"])

        # Display a scaled copy of the "unscaled" pixmap.
        self.current_image_label.setPixmap(
            self.scale_pixmap(self.current_image_pixmap_unscaled)
        )

        # Update event text
        self.event_label.setText(current_event["title"])
        self.placeholder_label.setText("Placeholder")

        # Set opacities
        self.current_image_label_opacity.setOpacity(1.0)
        self.next_image_label_opacity.setOpacity(0.0)

        # Set show status
        #self.current_image_label.show()
        #self.next_image_label.show()

        self.timer.start(self.IMAGE_DURATION_MS)


    def show_next_image(self):
        """
        Advance to the next photo.

        Photos are displayed in database order. Once the last photo
        of an event is reached, move to the first photo of the next
        event.
        """

        #Get a fresh reload of data from the db in case of changes just made.
        self.load_data()

        # Update the 
        self.calculate_next_indexes()
        self.start_fade()


    def calculate_next_indexes(self):
        """
        Updates next_image_index and next_event_index based on current_image_index and current_event_index.
        """

        # Get number of images in current event. If there are no events. Reset to 0.
        current_event = self.get_current_event()
        if not current_event:
            next_event_index = 0
            next_image_index = 0
            return
            
        number_current_event_images = len(datastore.get_images_for_event(current_event["id"]))

        # Set index of next image in this event
        next_image_index = self.current_image_index + 1

        # If index of next image exceeds number of images in current event, go to next event and reset next image index
        next_event_index = self.current_event_index    
        if next_image_index >= number_current_event_images:
            # Move to next event.
            next_event_index += 1
            next_image_index = 0

            if next_event_index >= len(self.events):
                # Loop back to first event.
                next_event_index = 0

        #Save to class parameters
        self.next_event_index = next_event_index
        self.next_image_index = next_image_index
        

    def start_fade(self):
        """
        Put the next image into the second QLabel and fade it over
        the currently displayed image.
        """

 

        # Get next event and next image
        next_event = self.get_next_event()
        if not next_event:
            self.timer.start(self.IMAGE_DURATION_MS)
            return

        next_image = self.get_next_image()
        if not next_image:
            self.timer.start(self.IMAGE_DURATION_MS)
            return

        # Load next image, save the unscaled version
        self.next_image_pixmap_unscaled = QPixmap(next_image["path_optimized"])
        if self.next_image_pixmap_unscaled.isNull():
            self.timer.start(self.IMAGE_DURATION_MS)
            return

        # Put a scaled copy to the next image label
        self.next_image_label.setPixmap(self.scale_pixmap(self.next_image_pixmap_unscaled))

        # Make next image label transparent.
        self.next_image_label_opacity.setOpacity(0.0)
        self.next_image_label.show()
        #self.next_image_label.raise_()

        # Update event text before the transition.
        self.event_label.setText(next_event["title"])
        self.placeholder_label.setText("Placeholder")
        #self.text_overlay.raise_()

        self.fade_animation.stop()
        self.fade_animation.start()

    def finish_transition(self):
        """
        Once the fade has completed, the next QLabel becomes the
        current QLabel.

        Rather than physically swapping widgets, we simply copy the
        state so that the labels continue alternating.
        """

        # Copy intexes from "next" to "current"
        self.current_event_index = self.next_event_index
        self.current_image_index = self.next_image_index

        # Copy pixmap from "next" to "current". 
        self.current_image_label.setPixmap(self.next_image_label.pixmap())
        self.current_image_label_opacity.setOpacity(1.0)

        # Hide next image label.
        self.next_image_label.hide()
        self.next_image_label_opacity.setOpacity(0.0)

        # Start the 30 second display period for the new image.
        self.timer.start(self.IMAGE_DURATION_MS)



    def scale_pixmap(self, pixmap):
        """
        Scale the image to fit the available widget while preserving
        its aspect ratio.
        """

        return pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )



    def resizeEvent(self, event):
        """
        Keep the two image labels and the text overlay covering the
        appropriate parts of the window.
        """

        super().resizeEvent(event)

        self.current_image_label.setGeometry(self.rect())
        self.next_image_label.setGeometry(self.rect())

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

        # Update scaled pixmaps from the unscaled ones.
        if self.current_image_pixmap_unscaled is not None:
            self.current_image_label.setPixmap(
                self.scale_pixmap(self.current_image_pixmap_unscaled)
            )

        if self.nnext_image_pixmap_unscaled is not None:
            self.next_image_label.setPixmap(
                self.scale_pixmap(self.nnext_image_pixmap_unscaled)
            )



app = QApplication([])

slideshow = SlideshowWidget()
slideshow.showFullScreen()

# Start the event loop.
app.exec()
