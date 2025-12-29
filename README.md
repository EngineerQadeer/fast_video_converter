# Fast Video Converter 🎥

A high-performance batch video converter designed to convert videos to 3GP format (176x144 resolution), optimized for older mobile devices or low-bandwidth applications.

## 🚀 Features

- **Fast Processing**: Uses multi-threading to convert multiple videos simultaneously.
- **Smart Resuming**: Keeps track of converted files to allow resuming interrupted sessions.
- **Speed Optimized**: Utilizes FFmpeg with `libx264` and `ultrafast` preset for maximum conversion speed.
- **Format Support**: Supports a wide range of input formats including MP4, AVI, MKV, MOV, WMV, FLV, WEBM, and more.
- **Intelligent Skipping**:
  - Skips files that are already in the target format and resolution.
  - Skips files with no video stream.
  - Skips "temp" files to avoid conflicts.
- **Detailed Reporting**: Shows progress, time taken, and size savings for each file.

## 📋 Prerequisites

Before running the converter, ensure you have the following installed:

1. **Python 3.x**: [Download Python](https://www.python.org/downloads/)
2. **FFmpeg**: [Download FFmpeg](https://ffmpeg.org/download.html)
   - Ensure `ffmpeg` and `ffprobe` are added to your system's PATH.

## 🛠️ Usage

### Quick Start (Windows)
Double-click `run_fast_converter.bat` to launch the application. A window will appear asking you to select the folder containing your videos.

### Command Line Interface (CLI)

You can also run the script directly from the terminal with various options:

```bash
# GUI folder selection (default)
python fast_video_converter.py

# Convert specific folder
python fast_video_converter.py -f "C:\Path\To\Videos"

# Use specific number of concurrent workers (default: 2)
python fast_video_converter.py -f "C:\Path\To\Videos" -w 4

# Preview which files would be converted without actually converting (Dry Run)
python fast_video_converter.py --dry-run

# Keep original files after conversion (default: delete originals)
python fast_video_converter.py --keep-originals
```

### Options

| Flag | Long Flag | Description |
|------|-----------|-------------|
| `-f` | `--folder` | Path to the folder containing videos to convert. |
| `-w` | `--workers` | Number of concurrent conversion jobs (Default: 2). |
| `-k` | `--keep-originals` | Keep original files after successful conversion. |
| `-d` | `--dry-run` | Preview files to be converted without performing actions. |

## ⚙️ Configuration

The script is hardcoded for specific settings optimized for 3GP 176x144 output:
- **Resolution**: 176x144
- **Video Codec**: H.264 (libx264)
- **Audio Codec**: AAC (Mono, 22050Hz)
- **Container**: 3GP

## 🌐 Connect with Me

- **GitHub**: [EngineerQadeer](https://github.com/EngineerQadeer)
- **Facebook**: [Engineer.Qadeer](https://www.facebook.com/Engineer.Qadeer)
- **YouTube**: [Engineer.Qadeer](https://www.youtube.com/@Engineer.Qadeer)
- **Instagram**: [Engineer.Qadeer](https://www.instagram.com/Engineer.Qadeer)

## 📄 License

This project is open-source and free to use.
