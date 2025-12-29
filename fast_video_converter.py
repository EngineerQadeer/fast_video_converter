#!/usr/bin/env python3
"""
Fast Video Converter to 3GP (176x144)
Optimized for speed using modern codecs
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import shutil

# Configuration
TARGET_WIDTH = 176
TARGET_HEIGHT = 144
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', 
                   '.webm', '.m4v', '.mpeg', '.mpg', '.3gp', '.ts', '.vob'}

class VideoConverter:
    def __init__(self, folder_path, max_workers=4, keep_originals=False, dry_run=False):
        self.folder_path = Path(folder_path)
        self.max_workers = max_workers
        self.keep_originals = keep_originals
        self.dry_run = dry_run
        self.state_file = Path(__file__).parent / "conversion_state.json"
        self.state = self.load_state()
        
    def load_state(self):
        """Load conversion state for resume capability"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_state(self):
        """Save conversion state"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
    
    def check_ffmpeg(self):
        """Check if FFmpeg is available"""
        if not shutil.which('ffmpeg'):
            print("ERROR: FFmpeg not found in PATH")
            print("Please install FFmpeg: https://ffmpeg.org/download.html")
            sys.exit(1)
        
        if not shutil.which('ffprobe'):
            print("ERROR: FFprobe not found in PATH")
            sys.exit(1)
        
        # Get FFmpeg version
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            version_line = result.stdout.split('\n')[0]
            print(f"✓ Found {version_line}")
        except:
            print("✓ FFmpeg found (version check failed)")
    
    def get_video_resolution(self, file_path):
        """Get video resolution using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'json',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            if 'streams' in data and len(data['streams']) > 0:
                stream = data['streams'][0]
                return (stream.get('width'), stream.get('height'))
            
            return None
        except Exception as e:
            print(f"Warning: Could not get resolution for {file_path.name}: {e}")
            return None
    
    def scan_videos(self):
        """Scan folder for videos that need conversion"""
        print(f"\n📁 Scanning: {self.folder_path}")
        
        files_to_convert = []
        skipped = 0
        already_done = 0
        
        for file_path in self.folder_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
                continue
            
            if file_path.name.startswith('temp_'):
                continue
            
            # Check if already converted
            state_key = str(file_path).lower()
            if state_key in self.state and self.state[state_key] == 'converted':
                already_done += 1
                continue
            
            # Get resolution
            resolution = self.get_video_resolution(file_path)
            
            if resolution is None:
                print(f"⚠️  SKIP (no video stream): {file_path.name}")
                skipped += 1
                continue
            
            width, height = resolution
            
            # Skip if already 3GP with exact target resolution
            if file_path.suffix.lower() == '.3gp' and width == TARGET_WIDTH and height == TARGET_HEIGHT:
                print(f"⊘ SKIP (already 3GP 176x144): {file_path.name}")
                self.state[state_key] = 'skipped'
                skipped += 1
                continue
            
            # Convert if resolution is larger OR if it's the right size but not 3GP format
            if width > TARGET_WIDTH or height > TARGET_HEIGHT:
                files_to_convert.append((file_path, width, height))
                print(f"✓ QUEUE: {file_path.name} ({width}x{height})")
            elif width == TARGET_WIDTH and height == TARGET_HEIGHT and file_path.suffix.lower() != '.3gp':
                # Same resolution but different format - convert to 3GP
                files_to_convert.append((file_path, width, height))
                print(f"✓ QUEUE (format conversion): {file_path.name} ({width}x{height}) → 3GP")
            else:
                print(f"⊘ SKIP (already small): {file_path.name} ({width}x{height})")
                self.state[state_key] = 'skipped'
                skipped += 1
        
        if already_done > 0:
            print(f"\n✓ Already converted: {already_done}")
        
        if skipped > 0:
            print(f"⊘ Skipped: {skipped}")
        
        self.save_state()
        return files_to_convert
    
    def convert_video(self, file_info):
        """Convert a single video file"""
        file_path, orig_width, orig_height = file_info
        
        temp_output = file_path.parent / f"temp_{file_path.stem}.3gp"
        final_output = file_path.parent / f"{file_path.stem}.3gp"
        
        state_key = str(file_path).lower()
        
        try:
            # FFmpeg command optimized for SPEED
            # Using libx264 with ultrafast preset instead of h263
            # Using AAC audio instead of AMR-NB for much faster encoding
            cmd = [
                'ffmpeg',
                '-i', str(file_path),
                '-vf', f'scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2',
                '-c:v', 'libx264',           # H.264 codec (much faster than h263)
                '-preset', 'ultrafast',       # Fastest encoding preset
                '-crf', '28',                 # Quality (higher = smaller file, 28 is good for low-res)
                '-maxrate', '128k',           # Max bitrate
                '-bufsize', '256k',           # Buffer size
                '-c:a', 'aac',                # AAC audio (much faster than amr_nb)
                '-b:a', '32k',                # Audio bitrate
                '-ar', '22050',               # Audio sample rate (lower = faster)
                '-ac', '1',                   # Mono audio
                '-movflags', '+faststart',    # Optimize for streaming
                '-y',                         # Overwrite output
                str(temp_output)
            ]
            
            # Run conversion
            start_time = datetime.now()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',  # Ignore Unicode decode errors from FFmpeg stderr
                timeout=300  # 5 minute timeout per file
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed with exit code {result.returncode}")
            
            if not temp_output.exists():
                raise Exception("Output file not created")
            
            # Check file size
            temp_size = temp_output.stat().st_size
            if temp_size < 1024:
                raise Exception(f"Output file too small ({temp_size} bytes)")
            
            # Move temp to final
            if final_output.exists():
                final_output.unlink()
            
            temp_output.rename(final_output)
            
            # Calculate savings
            original_size = file_path.stat().st_size
            new_size = final_output.stat().st_size
            savings = ((original_size - new_size) / original_size) * 100
            
            # Remove original if requested
            if not self.keep_originals:
                file_path.unlink()
                status_msg = f"✓ {file_path.name} (saved {savings:.1f}%, {elapsed:.1f}s)"
            else:
                status_msg = f"✓ {file_path.name} (saved {savings:.1f}%, {elapsed:.1f}s, original kept)"
            
            self.state[state_key] = 'converted'
            self.save_state()
            
            return ('success', status_msg)
            
        except Exception as e:
            # Clean up temp file
            if temp_output.exists():
                temp_output.unlink()
            
            self.state[state_key] = 'failed'
            self.save_state()
            
            return ('error', f"✗ {file_path.name}: {str(e)}")
    
    def run(self):
        """Main conversion process"""
        self.check_ffmpeg()
        
        files_to_convert = self.scan_videos()
        
        if not files_to_convert:
            print("\n✓ Nothing to convert. All files processed or skipped.")
            return
        
        print(f"\n📊 Found {len(files_to_convert)} file(s) to convert")
        
        if self.dry_run:
            print("\n[DRY RUN] Files that would be converted:")
            for file_path, width, height in files_to_convert:
                print(f"  • {file_path.name} ({width}x{height}) → ({TARGET_WIDTH}x{TARGET_HEIGHT})")
            return
        
        print(f"\n🚀 Starting conversion with {self.max_workers} concurrent jobs...")
        print("=" * 60)
        
        start_time = datetime.now()
        success_count = 0
        error_count = 0
        
        # Process files concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.convert_video, file_info): file_info 
                      for file_info in files_to_convert}
            
            for i, future in enumerate(as_completed(futures), 1):
                status, message = future.result()
                
                if status == 'success':
                    print(f"[{i}/{len(files_to_convert)}] {message}")
                    success_count += 1
                else:
                    print(f"[{i}/{len(files_to_convert)}] {message}")
                    error_count += 1
        
        # Summary
        elapsed = datetime.now() - start_time
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"✓ Converted: {success_count}")
        if error_count > 0:
            print(f"✗ Failed: {error_count}")
        print(f"⏱️  Total Time: {elapsed}")
        print(f"⚡ Avg Time: {elapsed.total_seconds() / len(files_to_convert):.1f}s per file")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Fast Video Converter to 3GP (176x144)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fast_video_converter.py                    # GUI folder selection
  python fast_video_converter.py -f C:\\Videos       # Convert specific folder
  python fast_video_converter.py -f C:\\Videos -w 4  # Use 4 concurrent jobs
  python fast_video_converter.py --dry-run          # Preview without converting
  python fast_video_converter.py --keep-originals   # Keep original files
        """
    )
    
    parser.add_argument('-f', '--folder', 
                       help='Folder containing videos (GUI if not specified)')
    parser.add_argument('-w', '--workers', type=int, default=2,
                       help='Max concurrent conversions (default: 2)')
    parser.add_argument('-k', '--keep-originals', action='store_true',
                       help='Keep original files after conversion')
    parser.add_argument('-d', '--dry-run', action='store_true',
                       help='Preview files without converting')
    
    args = parser.parse_args()
    
    folder_path = args.folder
    
    # GUI folder selection if not provided
    if not folder_path:
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            folder_path = filedialog.askdirectory(title="Select folder containing videos")
            root.destroy()
            
            if not folder_path:
                print("No folder selected. Exiting.")
                sys.exit(0)
        except ImportError:
            print("ERROR: No folder specified and tkinter not available for GUI")
            print("Usage: python fast_video_converter.py -f <folder_path>")
            sys.exit(1)
    
    if not os.path.isdir(folder_path):
        print(f"ERROR: Folder not found: {folder_path}")
        sys.exit(1)
    
    # Run converter
    converter = VideoConverter(
        folder_path=folder_path,
        max_workers=args.workers,
        keep_originals=args.keep_originals,
        dry_run=args.dry_run
    )
    
    converter.run()


if __name__ == '__main__':
    main()
