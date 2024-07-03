import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox, QSpinBox, QHBoxLayout
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Define your Spotify API credentials
SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''
SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'

# Set up authentication
scope = "playlist-modify-public"
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope=scope)

# Obtain the token
token_info = sp_oauth.get_access_token(as_dict=False)

if not token_info:
    print("Cannot get token for authentication")
    sys.exit()

sp = spotipy.Spotify(auth=token_info)

class SpotifyPlaylistApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('SpotList')
        
        # Set dark mode
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(QPalette.Window, Qt.black)
        p.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(p)
        
        # Set layout
        layout = QVBoxLayout()
        
        # Playlist name input
        self.playlistLabel = QLabel('Playlist Name:', self)
        self.playlistLabel.setStyleSheet('color: white;')
        layout.addWidget(self.playlistLabel)
        
        self.playlistInput = QLineEdit(self)
        self.playlistInput.setStyleSheet('background-color: #2C2C2C; color: white;')
        layout.addWidget(self.playlistInput)
        
        # Artist name and top songs input
        self.artistLabel = QLabel('Artist Name and Top Songs:', self)
        self.artistLabel.setStyleSheet('color: white;')
        layout.addWidget(self.artistLabel)
        
        artistLayout = QHBoxLayout()
        
        self.artistInput = QLineEdit(self)
        self.artistInput.setPlaceholderText('Artist Name')
        self.artistInput.setStyleSheet('background-color: #2C2C2C; color: white;')
        self.artistInput.returnPressed.connect(self.addArtist)  # Add this line
        artistLayout.addWidget(self.artistInput)
        
        self.topSongsInput = QSpinBox(self)
        self.topSongsInput.setRange(1, 10)
        self.topSongsInput.setValue(5)
        self.topSongsInput.setStyleSheet('background-color: #2C2C2C; color: white;')
        artistLayout.addWidget(self.topSongsInput)
        
        layout.addLayout(artistLayout)
        
        # Add artist button
        self.addArtistButton = QPushButton('Add Artist', self)
        self.addArtistButton.setStyleSheet('background-color: purple; color: white;')
        self.addArtistButton.clicked.connect(self.addArtist)
        layout.addWidget(self.addArtistButton)
        
        # Clear list button
        self.clearListButton = QPushButton('Clear List', self)
        self.clearListButton.setStyleSheet('background-color: purple; color: white;')
        self.clearListButton.clicked.connect(self.clearList)
        layout.addWidget(self.clearListButton)
        
        # Artist list
        self.artistList = QListWidget(self)
        self.artistList.setStyleSheet('background-color: #2C2C2C; color: white;')
        self.artistList.itemClicked.connect(self.removeArtist)
        layout.addWidget(self.artistList)
        
        # Submit button
        self.submitButton = QPushButton('Submit', self)
        self.submitButton.setStyleSheet('background-color: purple; color: white;')
        self.submitButton.clicked.connect(self.submitPlaylist)
        layout.addWidget(self.submitButton)
        
        self.setLayout(layout)
        
    def addArtist(self):
        artist_name = self.artistInput.text().strip()
        top_songs = self.topSongsInput.value()
        if artist_name:
            self.artistList.addItem(f'{artist_name} - Top {top_songs}')
            self.artistInput.clear()
            self.topSongsInput.setValue(5)
    
    def removeArtist(self, item):
        self.artistList.takeItem(self.artistList.row(item))
        
    def clearList(self):
        self.artistList.clear()
    
    def get_top_tracks(self, artist_name, top_songs):
        results = sp.search(q='artist:' + artist_name, type='artist')
        if not results['artists']['items']:
            print(f"Artist '{artist_name}' not found on Spotify. Skipping...")
            return []
        artist_id = results['artists']['items'][0]['id']
        top_tracks = sp.artist_top_tracks(artist_id)
        top_tracks_ids = [track['id'] for track in top_tracks['tracks'][:top_songs]]
        return top_tracks_ids
    
    def submitPlaylist(self):
        playlist_name = self.playlistInput.text().strip()
        if not playlist_name:
            QMessageBox.warning(self, 'Error', 'Please enter a playlist name.')
            return
        
        artists = []
        for index in range(self.artistList.count()):
            item = self.artistList.item(index).text()
            artist_name, top_songs = item.rsplit(' - Top ', 1)
            artists.append((artist_name, int(top_songs)))
        
        if not artists:
            QMessageBox.warning(self, 'Error', 'Please add at least one artist.')
            return
        
        try:
            self.create_playlist_with_artists_top_tracks(artists, playlist_name)
            QMessageBox.information(self, 'Success', f'Playlist "{playlist_name}" created successfully!')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to create playlist: {str(e)}')
    
    def create_playlist_with_artists_top_tracks(self, artists, playlist_name):
        user_id = sp.current_user()['id']
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
        playlist_id = playlist['id']
        track_ids = []
        for artist_name, top_songs in artists:
            track_ids.extend(self.get_top_tracks(artist_name, top_songs))
        sp.playlist_add_items(playlist_id, track_ids)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SpotifyPlaylistApp()
    window.show()
    sys.exit(app.exec_())
