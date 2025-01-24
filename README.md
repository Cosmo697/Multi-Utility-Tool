# README.md (Updated Version)

## Multi-Utility Application

### Overview
This project is a GUI-based multi-utility application built using Python and Tkinter. The application provides multiple tools for processing audio, image, text, and video files, all integrated into a single easy-to-use interface. The application is designed to run on Windows and provides drag-and-drop functionality for quick and convenient file handling.

### Features
- **Audio Tab**: Tools for audio processing (conversion, extraction, etc.).
- **Image Tab**: Tools for image editing (resize, crop, etc.).
- **Text Tab**: Tools for text file manipulation (merging, deduplication, etc.).
- **Video Tab**: Tools for video processing (frame extraction, format conversion, etc.).
- **Multi-threaded Processing**: The app uses threads for long-running tasks to keep the interface responsive.
- **Robust Logging**: Comprehensive logging for easier debugging and issue tracking.

### Installation

#### Prerequisites
- Python 3.7+
- Pip (Python package manager)

#### Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/multi-utility-application.git
   ```
2. Navigate into the project directory:
   ```bash
   cd multi-utility-application
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Requirements
The following dependencies are listed in `requirements.txt`:
- **Pillow**: Used for image manipulation.
- **ffmpeg-python**: For handling video and audio processing.
- **tkinterdnd2**: Provides drag-and-drop capabilities for the GUI.

### Running the Application
To run the application, use the following command:
```bash
python app.py
```

### File Structure
- **app.py**: Main entry point for the GUI application.
- **tabs.py**: Contains functions to set up individual tabs (Audio, Image, Text, Video) in the application.
- **helpers.py**: Provides utility functions that are used across the application. Includes thread-safe queue operations and item processing utilities.
- **utils/logging_config.py**: Sets up the logging configuration, which logs important information to both a file and the console for better tracking of events.
- **requirements.txt**: Lists the required Python packages for the project.

### Logging
Logging is configured through the `logging_config.py` file:
- **File Logging**: Logs are saved in `logs/app.log` for tracking important information and debugging.
- **Console Logging**: Logs are also output to the console to help during development.

### How to Contribute
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

### License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

### Contact
If you have any questions or suggestions, please feel free to reach out via email or open an issue in the repository.

