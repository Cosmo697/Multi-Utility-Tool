
# Multi-Utility Tool

## Overview
The Multi-Utility Tool is a Python-based GUI application designed for easy handling of media files, including images, audio, text, and video. It allows users to perform common operations such as file conversion, resizing, extraction, and more through an intuitive drag-and-drop interface.

## Features
- **Image Processing**: Resize images, crop to square, add margins, and sharpen images.
- **Audio Processing**: Convert audio formats, adjust bitrate, and convert to mono.
- **Text Processing**: Merge text files or remove duplicate words.
- **Video Processing**: Extract every nth frame from video files.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Cosmo697/Multi-Utility-Tool.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Dependencies
The tool requires the following Python packages:
- Pillow
- ffmpeg-python
- tkinterdnd2
- tkinter

## Usage
1. Launch the app:
   ```bash
   python app.py
   ```

2. Drag and Drop media files into the relevant tabs (Audio, Image, Text, Video) to begin processing.
   - **Image Tab**: Resize images and apply optional enhancements like adding margins.
   - **Audio Tab**: Convert files to various audio formats (mp3, wav, flac, etc.) with bitrate options.
   - **Text Tab**: Merge multiple text files or remove duplicate words from a single file.
   - **Video Tab**: Extract frames from videos based on a selected interval.

## Structure
- **app.py**: Main application file that sets up the GUI and tabs.
- **tabs/**: Contains the individual tab implementations (audio, image, text, video).
- **utils/**: Contains helper functions for file handling and logging.

## License
This project is licensed under the MIT License.
