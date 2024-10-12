# Spotify Mini Carthing PythonEdition

A desktop application that mimics the Spotify CarThing device, displaying the currently playing song with album art, track info, and playback controls.

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features

- **Real-Time Track Display**: Shows the currently playing track on Spotify.
- **Album Art**: Displays the album art of the current track.
- **Track Information**: Shows track name, artist name, and album name.
- **Playback Controls**:
  - Play/Pause
  - Next Track
  - Previous Track
  - Shuffle Toggle
- **Like/Unlike Track**: Add or remove the current track from your Liked Songs.
- **Progress Bar**: Displays track progress with current time and total duration.
- **Dynamic UI**: Adapts the UI colors based on the album art.
- **Custom Window**: Rounded corners and draggable interface without standard window borders.

## Screenshots

*Note: Include screenshots of your application here.*

## Prerequisites

- **Spotify Premium Account**: Required to control playback and access user-specific data.
- **Spotify Developer Account**: To obtain API credentials.
- **Python 3.6 or higher**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/spotify-mini-carthing.git
cd spotify-mini-carthing
```

### 2. Set Up a Spotify Developer Application

1. Log in to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/login).
2. Click on **Create an App**.
3. Enter an app name and description.
4. Click on **Edit Settings** and add `http://localhost:8888/callback` to the **Redirect URIs**.
5. Save the settings.
6. Note down your **Client ID** and **Client Secret**.

### 3. Install Dependencies

It's recommended to use a virtual environment.

#### Using `venv`

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

#### Install Required Packages

```bash
pip install -r requirements.txt
```

*If `requirements.txt` is not provided, install packages individually:*

```bash
pip install PyQt5 spotipy qtawesome
```

## Usage

### 1. Configure the Application

Update the `client_id`, `client_secret`, and `redirect_uri` in the script with your Spotify API credentials.

```python
# Spotify authentication credentials
client_id = 'your_client_id_here'
client_secret = 'your_client_secret_here'
redirect_uri = 'http://localhost:8888/callback'
```

### 2. Run the Application

```bash
python spotify_mini_carthing.py
```

*Note: Replace `spotify_mini_carthing.py` with the actual filename if different.*

### 3. Authenticate with Spotify

Upon running the application for the first time, you'll be prompted to authenticate with Spotify:

1. A web browser window will open, asking you to log in to your Spotify account and authorize the application.
2. After authorization, you'll be redirected to the redirect URI (`http://localhost:8888/callback`) with an authentication code.
3. The application will capture this code and proceed to display the current track information.

## Configuration

### Spotify API Credentials

Ensure you have set your Spotify API credentials in the script:

- `client_id`
- `client_secret`
- `redirect_uri`

### Redirect URI

The `redirect_uri` must match exactly between your Spotify Developer Dashboard and the script.

### Scope

The application requests the following scopes:

- `user-read-currently-playing`
- `user-read-playback-state`
- `user-modify-playback-state`
- `user-library-read`
- `user-library-modify`

These scopes allow the application to read your currently playing track, control playback, and manage your library.

## Dependencies

- [Python 3.6+](https://www.python.org/downloads/)
- [PyQt5](https://pypi.org/project/PyQt5/): Python bindings for the Qt application framework.
- [Spotipy](https://spotipy.readthedocs.io/): A lightweight Python library for the Spotify Web API.
- [qtawesome](https://github.com/spyder-ide/qtawesome): Icon packs for PyQt.

### Installing Dependencies

```bash
pip install PyQt5 spotipy qtawesome
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Spotify**: For providing a robust API to interact with music data.
- **Qt and PyQt5**: For making GUI development accessible in Python.
- **QtAwesome**: For the icon packs used in the application.
- **Spotipy**: For simplifying interactions with the Spotify API.

## Troubleshooting

### Common Issues

#### Authentication Error

If you receive an authentication error:

- Ensure your `client_id`, `client_secret`, and `redirect_uri` are correctly set.
- The `redirect_uri` in your script must match exactly with the one set in your Spotify Developer Dashboard.
- Make sure you have a stable internet connection.

#### No Active Playback Found

If the application displays "No active playback found.":

- Ensure that Spotify is running and playing music on one of your devices.
- The application cannot control devices in **Private Session** mode.

### Logging

For debugging purposes, you can print additional information to the console by adding print statements or configuring logging in the script.

## Contribution

Contributions are welcome! Please open an issue or submit a pull request.

---

*This project is not affiliated with or endorsed by Spotify. It is an independent project created for educational purposes.*
