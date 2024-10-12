import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QProgressBar, QSizePolicy, QGraphicsDropShadowEffect, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QColor, QFont, QPainter, QRegion, QPainterPath
from PyQt5.QtCore import Qt, QTimer, QObject, QThread, pyqtSignal, pyqtSlot, QUrl, QSize, QPoint, QRect
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import qtawesome as qta  # Import QtAwesome for FontAwesome icons

# Spotify authentication credentials
client_id = 'your_client_id_here'
client_secret = 'your_client_secret_here'
redirect_uri = 'http://localhost:8888/callback'

# Updated scope with 'user-read-playback-state'
scope = "user-read-currently-playing user-read-playback-state user-modify-playback-state user-library-read user-library-modify"


class Worker(QObject):
    # Define signals to send data back to the main thread
    track_data_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, sp):
        super().__init__()
        self.sp = sp
        self.current_track_id = None  # Keep track of the current track ID

    @pyqtSlot()
    def start(self):
        self.timer = QTimer()
        self.timer.setInterval(1000)  # Update every second
        self.timer.timeout.connect(self.fetch_track_data)
        self.timer.start()

    def fetch_track_data(self):
        try:
            current_track = self.sp.current_user_playing_track()
            if current_track:
                self.track_data_signal.emit(current_track)
            else:
                self.track_data_signal.emit(None)
        except Exception as e:
            # Emit the error signal instead of printing
            self.error_signal.emit(str(e))

    def stop(self):
        self.timer.stop()


class SpotifyApp(QWidget):
    def __init__(self, sp):
        super().__init__()
        self.sp = sp
        self.initUI()
        self.current_album_url = None  # Track current album art URL
        self.connection_error = False  # Track connection status

        # Set up the worker thread
        self.thread = QThread()
        self.worker = Worker(self.sp)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start)
        self.thread.finished.connect(self.worker.deleteLater)
        self.worker.track_data_signal.connect(self.handle_track_data)
        self.worker.error_signal.connect(self.handle_error)
        self.thread.start()

        # Variables for window dragging
        self.offset = None

    def closeEvent(self, event):
        # Stop the worker thread when the application is closed
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        event.accept()

    def initUI(self):
        self.setWindowTitle('Spotify Mini Carthing')
        window_h = 400
        window_w = 570
        self.setGeometry(0, 0, window_w, window_h)  # Set window size and position
        self.setFixedSize(window_w, window_h)  # Make the window fixed size

        # *** Enable Translucent Background for Rounded Corners ***
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        # *** Apply Border Radius to Specific Corners of the Main Window ***
        self.setStyleSheet("""
            QWidget#SpotifyApp {
                background-color: #121212;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
        """)

        self.setObjectName("SpotifyApp")

        # Retrieve the primary screen's geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = screen_geometry.width() - window_w  # Position at the bottom right with 10px margin
        y = screen_geometry.height() - window_h # Adjust y-position as needed
        self.move(x, y)

        # *** New Top Bar for Window Controls ***
        self.top_bar = QWidget(self)
        self.top_bar.setFixedHeight(22)  # Height for window controls
        self.top_bar.setStyleSheet("background-color: transparent;")  # Background color

        self.top_bar_layout = QHBoxLayout(self.top_bar)
        self.top_bar_layout.setContentsMargins(10, 8, 10, 0)  # Left, Top, Right, Bottom
        self.top_bar_layout.setSpacing(10)

        # Spacer to push the close button to the right
        self.top_bar_layout.addStretch()

        # *** Close Button ***
        self.close_button = QPushButton(self.top_bar)
        self.close_button.setFixedSize(11, 11)  # Size similar to macOS close button
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #FF605C;  /* Red color */
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FF2B45;
            }
            QPushButton:pressed {
                background-color: #E12C2C;
            }
        """)
        self.close_button.setToolTip("Close")
        self.close_button.clicked.connect(self.close_application)
        self.top_bar_layout.addWidget(self.close_button)

        # *** Error Message Label ***
        self.error_label = QLabel('', self)
        self.error_label.setFont(QFont('Arial', 10))
        self.error_label.setStyleSheet("color: red; background-color: #222222; padding: 5px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)  # Hidden by default

        # *** Main Content Panel (Album Art and Track Info) ***
        self.content_panel = QWidget(self)
        self.content_layout = QHBoxLayout(self.content_panel)
        self.content_layout.setSpacing(10)

        # Album art
        self.album_art_label = QLabel(self.content_panel)
        self.album_art_label.setAlignment(Qt.AlignLeft)
        self.album_art_label.setFixedSize(190, 190)
        # self.album_art_label.setContentsMargins(10, 0, 0, 0)

        # Track info
        self.track_info_layout = QVBoxLayout()
        self.track_info_layout.setSpacing(6)
        self.track_info_layout.setContentsMargins(10, 20, 0, 0)

        self.album_name_label = QLabel('', self.content_panel)
        self.album_name_label.setFont(QFont('Arial Rounded MT Bold', 14))
        self.album_name_label.setStyleSheet("color: white;")
        self.album_name_label.setAlignment(Qt.AlignLeft)
        self.album_name_label.setWordWrap(True)
        self.album_name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.track_name_label = QLabel('', self.content_panel)
        self.track_name_label.setFont(QFont('Arial Rounded MT Bold', 28, QFont.Bold))
        self.track_name_label.setStyleSheet("color: white;")
        self.track_name_label.setAlignment(Qt.AlignLeft)
        self.track_name_label.setWordWrap(True)
        self.track_name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.artist_name_label = QLabel('', self.content_panel)
        self.artist_name_label.setFont(QFont('Arial Rounded MT Bold', 14))
        self.artist_name_label.setStyleSheet("color: white;")
        self.artist_name_label.setAlignment(Qt.AlignLeft)
        self.artist_name_label.setWordWrap(True)
        self.artist_name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.track_info_layout.addWidget(self.album_name_label)
        self.track_info_layout.addWidget(self.track_name_label)
        self.track_info_layout.addWidget(self.artist_name_label)
        self.track_info_layout.addStretch()

        self.content_layout.addWidget(self.album_art_label)
        self.content_layout.addLayout(self.track_info_layout)

        # *** Network manager for image loading ***
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.update_album_art)

        # *** Bottom Panel (Progress Bar and Controls) ***
        self.bottom_panel = QWidget(self)
        self.bottom_layout = QVBoxLayout(self.bottom_panel)
        self.bottom_layout.setContentsMargins(10, 10, 10, 10)
        self.bottom_layout.setSpacing(10)

        # Time labels
        self.time_labels_layout = QHBoxLayout()
        self.current_time_label = QLabel('00:00', self.bottom_panel)
        self.current_time_label.setFont(QFont('Arial Rounded MT Bold', 10))
        self.current_time_label.setStyleSheet("color: white;")
        self.end_time_label = QLabel('00:00', self.bottom_panel)
        self.end_time_label.setFont(QFont('Arial Rounded MT Bold', 10))
        self.end_time_label.setStyleSheet("color: white;")
        self.time_labels_layout.addWidget(self.current_time_label)
        self.time_labels_layout.addStretch()
        self.time_labels_layout.addWidget(self.end_time_label)

        # Progress bar (full width, slim)
        self.progress_bar = QProgressBar(self.bottom_panel)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                color: transparent;
                border: none;
                border-radius: 2px;
                background-color: #505050;
            }
            QProgressBar::chunk {
                background-color: white;
                border-radius: 2px;
            }
        """)
        self.progress_bar.setFixedHeight(4)  # Slim progress bar

        # Control buttons with FontAwesome icons
        self.controls_layout = QHBoxLayout()
        self.controls_layout.setSpacing(20)
        self.controls_layout.setContentsMargins(10, 10, 10, 10)

        self.shuffle_button = QPushButton(self.bottom_panel)
        self.shuffle_button.setIcon(qta.icon('fa.random', color='white'))  # Shuffle icon
        self.shuffle_button.setIconSize(QSize(30, 30))
        self.shuffle_button.setStyleSheet("background-color: transparent;")
        self.shuffle_button.clicked.connect(self.toggle_shuffle)

        self.previous_button = QPushButton(self.bottom_panel)
        self.previous_button.setIcon(qta.icon('fa.step-backward', color='white'))  # Backward icon
        self.previous_button.setIconSize(QSize(30, 30))
        self.previous_button.setStyleSheet("background-color: transparent;")
        self.previous_button.clicked.connect(self.previous_track)

        self.play_pause_button = QPushButton(self.bottom_panel)
        self.play_pause_button.setIcon(qta.icon('fa.play', color='white'))
        self.play_pause_button.setIconSize(QSize(30, 30))
        self.play_pause_button.setStyleSheet("background-color: transparent;")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        self.next_button = QPushButton(self.bottom_panel)
        self.next_button.setIcon(qta.icon('fa.step-forward', color='white'))  # Forward icon
        self.next_button.setIconSize(QSize(30, 30))
        self.next_button.setStyleSheet("background-color: transparent;")
        self.next_button.clicked.connect(self.next_track)

        self.like_button = QPushButton(self.bottom_panel)
        self.like_button.setIcon(qta.icon('fa.heart-o', color='white'))  # Unliked heart icon
        self.like_button.setIconSize(QSize(30, 30))
        self.like_button.setStyleSheet("background-color: transparent;")
        self.like_button.clicked.connect(self.like_unlike_track)

        # Add buttons to controls layout
        self.controls_layout.addWidget(self.shuffle_button)
        self.controls_layout.addWidget(self.previous_button)
        self.controls_layout.addWidget(self.play_pause_button)
        self.controls_layout.addWidget(self.next_button)
        self.controls_layout.addWidget(self.like_button)

        # Add elements to bottom layout
        self.bottom_layout.addLayout(self.time_labels_layout)
        self.bottom_layout.addWidget(self.progress_bar)
        self.bottom_layout.addLayout(self.controls_layout)

        # *** Combine All Sections into Main Vertical Layout ***
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)  # Adjusted margins to fit within rounded corners
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.error_label)  # Add the error label here
        self.main_layout.addWidget(self.content_panel)
        self.main_layout.addWidget(self.bottom_panel)

        self.setLayout(self.main_layout)

    def show_error_message(self, message):
        """
        Display an error message using the error label.
        """
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def hide_error_message(self):
        """
        Hide the error message.
        """
        self.error_label.setVisible(False)

    # Define functions for like and shuffle functionality
    def like_unlike_track(self):
        try:
            current_track = self.sp.current_user_playing_track()
            if current_track and current_track['item'] and not current_track['item']['is_local']:
                track_id = current_track['item']['id']

                # Check if the track is already liked
                is_liked = self.sp.current_user_saved_tracks_contains([track_id])[0]

                if is_liked:
                    # If liked, remove from liked tracks
                    self.sp.current_user_saved_tracks_delete([track_id])
                    self.like_button.setIcon(qta.icon('fa.heart-o', color='white'))  # Unliked icon
                else:
                    # If not liked, add to liked tracks
                    self.sp.current_user_saved_tracks_add([track_id])
                    self.like_button.setIcon(qta.icon('fa.heart', color='red'))  # Liked icon
        except Exception as e:
            # Show error message box instead of printing
            self.show_error_message(f"Error in like_unlike_track: {e}")

    def toggle_shuffle(self):
        try:
            current_playback = self.sp.current_playback()
            if current_playback:
                current_state = current_playback['shuffle_state']
                self.sp.shuffle(not current_state)
                # Update the shuffle button icon
                if not current_state:
                    self.shuffle_button.setIcon(qta.icon('fa.random', color='green'))  # Shuffle enabled
                else:
                    self.shuffle_button.setIcon(qta.icon('fa.random', color='white'))  # Shuffle disabled
            else:
                self.show_error_message("No active playback found.")
        except spotipy.exceptions.SpotifyException as e:
            self.show_error_message(f"Spotify API Error in toggle_shuffle: {e}")
        except Exception as e:
            self.show_error_message(f"Error in toggle_shuffle: {e}")

    def handle_track_data(self, current_track):
        # Reset connection error flag since data was fetched successfully
        if self.connection_error:
            # Optionally notify the user that the connection has been restored
            self.show_error_message("Connection Restored: Internet connection is back.")
            QTimer.singleShot(3000, self.hide_error_message)  # Hide after 3 seconds
        self.connection_error = False

        if current_track is not None and current_track['item'] is not None:
            track_id = current_track['item']['id']
            is_playing = current_track['is_playing']
            duration_ms = current_track['item']['duration_ms']
            progress_ms = current_track['progress_ms']
            album_url = current_track['item']['album']['images'][0]['url']
            album_name = current_track['item']['album']['name']
            # **Only fetch album art if it has changed**
            if album_url != self.current_album_url:
                self.current_album_url = album_url
                request = QNetworkRequest(QUrl(album_url))
                self.network_manager.get(request)
            # Update track info
            self.album_name_label.setText(album_name)
            self.track_name_label.setText(current_track['item']['name'])
            self.artist_name_label.setText(current_track['item']['artists'][0]['name'])
            self.current_time_label.setText(f"{progress_ms // 1000 // 60:02}:{progress_ms // 1000 % 60:02}")
            self.end_time_label.setText(f"{duration_ms // 1000 // 60:02}:{duration_ms // 1000 % 60:02}")

            # Update progress bar
            self.progress_bar.setMaximum(duration_ms)
            self.progress_bar.setValue(progress_ms)

            # Update play/pause button icon
            if is_playing:
                self.play_pause_button.setIcon(qta.icon('fa.pause', color='white'))  # Pause icon
            else:
                self.play_pause_button.setIcon(qta.icon('fa.play', color='white'))  # Play icon

            # Update like button icon
            is_liked = self.sp.current_user_saved_tracks_contains([track_id])[0]
            if is_liked:
                self.like_button.setIcon(qta.icon('fa.heart', color='red'))  # Liked icon
            else:
                self.like_button.setIcon(qta.icon('fa.heart-o', color='white'))  # Unliked icon

            # **Retrieve and update shuffle status**
            try:
                current_playback = self.sp.current_playback()
                if current_playback:
                    shuffle_state = current_playback['shuffle_state']
                    if shuffle_state:
                        self.shuffle_button.setIcon(qta.icon('fa.random', color='green'))  # Shuffle enabled
                    else:
                        self.shuffle_button.setIcon(qta.icon('fa.random', color='white'))  # Shuffle disabled
                else:
                    self.show_error_message("No active playback found.")
            except spotipy.exceptions.SpotifyException as e:
                self.show_error_message(f"Spotify API Error in handle_track_data when checking shuffle state: {e}")
            except Exception as e:
                self.show_error_message(f"Error in handle_track_data when checking shuffle state: {e}")

            # Load album art asynchronously using QNetworkAccessManager
            request = QNetworkRequest(QUrl(album_url))
            self.network_manager.get(request)
        else:
            if not self.connection_error:
                # Clear track info if no track is playing and no connection error
                self.album_name_label.setText('')
                self.track_name_label.setText('No track playing')
                self.artist_name_label.setText('')
                self.current_time_label.setText('00:00')
                self.end_time_label.setText('00:00')
                self.progress_bar.setValue(0)
                self.play_pause_button.setIcon(qta.icon('fa.play', color='white'))  # Reset to play icon

    def update_album_art(self, reply):
        if reply.error() == reply.NoError:
            image_data = reply.readAll()
            image = QImage()
            image.loadFromData(image_data)
            # Create a shadow effect for the album art
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setXOffset(10)
            shadow.setYOffset(5)
            shadow.setColor(QColor(0, 0, 0, 190))
            self.album_art_label.setGraphicsEffect(shadow)
            self.album_art_label.setPixmap(QPixmap(image).scaled(190, 190, Qt.KeepAspectRatio))

            # Now, sample color from the image
            width = image.width()
            height = image.height()
            center_color = QColor(image.pixel(width // 2, height // 2))

            # Adjust the color to be darker for the bottom panel
            darker_color = center_color.darker(300)  # Factor >100 makes it darker
            color_string_bottom = darker_color.name()  # Hex color code

            # Adjust the color to be lighter for the content panel (previously top panel)
            lighter_color = center_color.lighter(60)  # Factor >100 makes it lighter
            color_string_top = lighter_color.name()

            # Set the background colors of the panels
            self.content_panel.setStyleSheet(f" background-color: {color_string_top}; ")
            self.bottom_panel.setStyleSheet(f"background-color: {color_string_bottom}; border-top-left-radius: 0px; border-top-right-radius: 0px; border-bottom-left-radius: 15px; border-bottom-right-radius: 15px;")
            self.top_bar.setStyleSheet(f"background-color: {color_string_top}; border-top-left-radius: 15px; border-top-right-radius: 15px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;")  # Background color with rounded top corners

            # Convert the top panel's background color to a QColor object
            top_color = QColor(color_string_top)

            # Get RGB values
            r = top_color.red()
            g = top_color.green()
            b = top_color.blue()

            # Calculate perceived brightness (standard formula)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            # Decide if the background is light or dark
            if brightness < 80:
                background_is_dark = True
            else:
                background_is_dark = False
            # Base gray color
            base_gray = QColor('#2B2B2B')
            if background_is_dark:
                # Background is dark, lighten the gray color
                adjusted_gray = base_gray.lighter(300)  # Adjust the factor as needed
            else:
                # Background is light, darken the gray color
                adjusted_gray = base_gray.darker(200)   # Adjust the factor as needed

            # Get the hex code of the adjusted gray color
            text_color = adjusted_gray.name()
            self.album_name_label.setStyleSheet(f"color: {text_color};")
        else:
            # Instead of showing a QMessageBox, display the error in the error label
            self.show_error_message(f"Error loading image: {reply.errorString()}")

        reply.deleteLater()

    def handle_error(self, error_message):
        if not self.connection_error:
            # Show error message once when connection is lost
            self.show_error_message(f"Connection Error: {error_message}")
            self.connection_error = True  # Set the connection error flag
            # Update UI to show no internet connection
            self.current_album_url = None
            self.track_name_label.setText("No internet connection")
            self.album_name_label.setText('')
            self.artist_name_label.setText('')
            self.current_time_label.setText('--:--')
            self.end_time_label.setText('--:--')
            self.progress_bar.setValue(0)
            self.play_pause_button.setIcon(qta.icon('fa.play', color='white'))  # Reset to play icon
            self.album_art_label.clear()

    def toggle_play_pause(self):
        try:
            current_track = self.sp.current_user_playing_track()
            if current_track and current_track['is_playing']:
                self.sp.pause_playback()
            else:
                self.sp.start_playback()
        except spotipy.SpotifyException as e:
            self.show_error_message(f"Spotify API Error: {e}")
        except Exception as e:
            self.show_error_message(f"Error: {e}")

    def previous_track(self):
        try:
            self.sp.previous_track()
        except Exception as e:
            self.show_error_message(f"Error: {e}")

    def next_track(self):
        try:
            self.sp.next_track()
        except Exception as e:
            self.show_error_message(f"Error: {e}")

    # *** Close Application Function ***
    def close_application(self):
        self.close()

    # *** Optional: Implement Window Dragging ***
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_in_top_bar(event.pos()):
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = None

    def is_in_top_bar(self, pos):
        """
        Determine if the mouse position is within the top bar area.
        """
        return 0 <= pos.y() <= self.top_bar.height()


def main():
    app = QApplication(sys.argv)

    # Perform Spotify authentication before creating the app
    auth_manager = SpotifyOAuth(client_id=client_id,
                                client_secret=client_secret,
                                redirect_uri=redirect_uri,
                                scope=scope)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Test authentication
    try:
        user = sp.current_user()
        print(f"Logged in as {user['display_name']}")
    except spotipy.exceptions.SpotifyException as e:
        # Instead of showing QMessageBox here, you can use a temporary window or print to console
        QMessageBox.critical(None, "Authentication Error", f"Spotify authentication failed: {e}")
        sys.exit()

    spotify_app = SpotifyApp(sp)
    spotify_app.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
