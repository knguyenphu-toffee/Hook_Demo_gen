#!/usr/bin/env python3
"""
Video Combiner Script
Combines hook and demo videos with audio overlay
Optimized for TikTok/Reels 9:16 format
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil
import textwrap

class VideoCombiner:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.hooks_folder = self.script_dir / "hooks"
        self.demo_folder = self.script_dir / "demo"
        self.audio_folder = self.script_dir / "audio"
        self.assets_folder = self.script_dir / "assets"
        self.font_path = self.assets_folder / "TikTokDisplay-Medium.ttf"
        self.output_path = self.script_dir / "combined_video_with_audio.mp4"
        
        # Supported file types
        self.video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        self.audio_extensions = ['.mp3', '.wav', '.aac', '.m4a', '.flac']
    
    def check_dependencies(self):
        """Check if FFmpeg is installed"""
        if not shutil.which('ffmpeg'):
            print("❌ FFmpeg is not installed!")
            print("Please install FFmpeg:")
            print("  Mac: brew install ffmpeg")
            print("  Linux: sudo apt-get install ffmpeg")
            print("  Windows: Download from ffmpeg.org")
            return False
        print("✅ FFmpeg found")
        return True
    
    def find_file(self, folder, extensions):
        """Find first file with matching extension in folder"""
        if not folder.exists():
            print(f"❌ Folder not found: {folder}")
            return None
        
        for ext in extensions:
            files = list(folder.glob(f"*{ext}"))
            if files:
                print(f"✅ Found: {files[0].name}")
                return files[0]
        
        print(f"❌ No files with extensions {extensions} found in {folder}")
        return None
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except:
            return 0
    
    def get_font_path(self):
        """Get a suitable font path for the current OS"""
        import platform
        system = platform.system()
        
        if system == "Darwin":  # macOS
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Avenir.ttc",
                "/Library/Fonts/Arial.ttf"
            ]
        elif system == "Windows":
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/Arial.ttf",
                "C:/Windows/Fonts/calibri.ttf"
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf"
            ]
        
        # Find first available font
        for font in font_paths:
            if Path(font).exists():
                return font
        
        # If no font found, let FFmpeg use its default
        return None
    
    def wrap_text_for_margins(self, text, video_width=1080, margin_percent=5):
        """Wrap text to fit within margins of the video"""
        # Calculate available width considering margins
        # 5% margin on each side = 10% total, leaving 90% for text
        available_width_percent = 100 - (margin_percent * 2)
        
        # With 5% margins and 75pt font, we can fit approximately 22-24 chars per line
        # This ensures text fits within the 90% available width
        chars_per_line = 23
        
        # Use textwrap to wrap the text
        wrapped = textwrap.fill(text, width=chars_per_line, break_long_words=False)
        return wrapped
    
    def combine_videos(self, hook_path, demo_path, audio_path):
        """Combine hook and demo videos with audio overlay"""
        print("\n🎬 Starting video combination process...")
        
        # Get overlay text from user
        print("\n📝 Text Overlay Setup:")
        overlay_text = input("Enter text to display during the hook (or press Enter to skip): ").strip()
        
        # Get video durations for verification
        hook_duration = self.get_video_duration(hook_path)
        demo_duration = self.get_video_duration(demo_path)
        
        print(f"\n📊 Video Information:")
        print(f"  Hook video: {hook_path.name} ({hook_duration:.1f}s)")
        print(f"  Demo video: {demo_path.name} ({demo_duration:.1f}s)")
        print(f"  Audio: {audio_path.name}")
        print(f"  Expected total duration: {hook_duration + demo_duration:.1f}s")
        print(f"  Output format: 9:16 (1080x1920) - TikTok/Reels format")
        if overlay_text:
            wrapped_preview = self.wrap_text_for_margins(overlay_text, margin_percent=5)
            print(f"  Overlay text (5s duration, with 5% margins):")
            for line in wrapped_preview.split('\n'):
                print(f"    {line}")
        
        # Method 1: Using concat filter (most reliable for different codecs)
        print("\n⚙️  Combining videos and adding audio...")
        print("  - Converting to 9:16 aspect ratio (1080x1920)")
        print("  - Hook: Maintaining 9:16 format (cropped if needed)")
        print("  - Demo: Fitted to 9:16 with black bars (no cropping)")
        print("  - Muting hook video audio")
        print("  - Preserving demo video's original audio")
        print("  - Lowering overlay audio to -15dB")
        if overlay_text:
            print("  - Adding text overlay to hook with 5% margins")
        
        # Build filter complex based on whether text overlay is needed
        if overlay_text:
            # Wrap text for margins (5% on each side)
            wrapped_text = self.wrap_text_for_margins(overlay_text, margin_percent=5)
            
            # Create a temporary text file for the overlay text to avoid escaping issues
            text_file = self.script_dir / "overlay_text.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(wrapped_text)
            
            # Determine font to use
            font_param = ''
            if self.font_path.exists():
                print(f"  - Using TikTok font from assets folder")
                font_param = f":fontfile='{str(self.font_path)}'"
            else:
                system_font = self.get_font_path()
                if system_font:
                    print(f"  - Using system font: {Path(system_font).name}")
                    font_param = f":fontfile='{system_font}'"
                else:
                    print("  - Using FFmpeg default font")
                    font_param = ''
            
            # Build the drawtext filter using textfile instead of text parameter
            # 75pt font size with center alignment
            drawtext_filter = (
                f"drawtext="
                f"textfile='{str(text_file)}'"
                f"{font_param}"
                f":fontsize=75"  # 75pt font size as requested
                f":fontcolor=white"
                f":borderw=4"  # Good border thickness for 75pt text
                f":bordercolor=black"
                f":x=(w-text_w)/2"  # Center horizontally
                f":y=(h-text_h)/2+100"  # Slightly below center (shifted down by 100 pixels)
                f":text_align=C"  # Center align text (C for center)
                f":enable='between(t,0,5)'"
            )
            
            filter_complex = (
                # Hook video: scale to 9:16 with cropping if needed, then add text
                f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                f"{drawtext_filter}[v0];"
                # Demo video: scale to fit within 9:16 without cropping, add padding
                "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[v1];"
                # Concatenate the two videos
                "[v0][v1]concat=n=2:v=1:a=0[outv];"
            )
        else:
            filter_complex = (
                # Hook video: scale to 9:16 with cropping if needed
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v0];"
                # Demo video: scale to fit within 9:16 without cropping, add padding
                "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[v1];"
                # Concatenate the two videos
                "[v0][v1]concat=n=2:v=1:a=0[outv];"
            )
        
        # Add audio processing to filter complex
        filter_complex += (
            # Audio processing - create silence for hook duration, then use demo audio
            f"aevalsrc=0:d={hook_duration}:s=44100:c=stereo[silence];"
            "[1:a]aformat=sample_rates=44100:channel_layouts=stereo[demo_audio];"
            "[silence][demo_audio]concat=n=2:v=0:a=1[original_audio];"
            # Lower the overlay audio to -15dB
            "[2:a]volume=-15dB[overlay_audio];"
            # Mix the original audio with the lowered overlay audio
            "[original_audio][overlay_audio]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
        
        cmd = [
            'ffmpeg',
            '-i', str(hook_path),
            '-i', str(demo_path),
            '-i', str(audio_path),
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-movflags', '+faststart',
            '-y',
            str(self.output_path)
        ]
        
        # Debug: Print the filter complex if there's text overlay
        if overlay_text:
            print("\n🔍 Debug - Using text file for overlay to avoid escaping issues")
            print(f"  Text file: {text_file}")
            print(f"  Filter: {drawtext_filter[:150]}...")
        
        try:
            # Run FFmpeg with more verbose error output for debugging
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            stderr_lines = []
            # Monitor progress
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                stderr_lines.append(line)
                # Look for time updates to show progress
                if 'time=' in line:
                    time_str = line.split('time=')[1].split()[0]
                    print(f"  Processing: {time_str}", end='\r')
            
            process.wait()
            
            # Clean up text file if it was created
            if overlay_text:
                if text_file.exists():
                    text_file.unlink()
                # Clean up line files if they exist
                for i in range(10):  # Clean up to 10 line files
                    line_file = self.script_dir / f"overlay_text_line_{i}.txt"
                    if line_file.exists():
                        line_file.unlink()
            
            if process.returncode == 0:
                # Verify output
                output_duration = self.get_video_duration(self.output_path)
                print(f"\n✅ Success! Output video created ({output_duration:.1f}s)")
                print(f"📍 Location: {self.output_path}")
                return True
            else:
                # Join all stderr lines for complete error message
                stderr = ''.join(stderr_lines)
                print(f"\n❌ FFmpeg error occurred")
                
                # Show more specific error information
                if 'No such filter' in stderr:
                    print("Error: Invalid filter configuration")
                elif 'fontfile' in stderr or 'textfile' in stderr:
                    print("Error: Font or text file issue - trying without custom font")
                    # Retry without custom font
                    if overlay_text:
                        return self.combine_videos_fallback(hook_path, demo_path, audio_path, overlay_text, hook_duration)
                
                # Show last few lines of error for debugging
                error_lines = stderr_lines[-10:]  # Last 10 lines
                print("\nError details (last 10 lines):")
                for line in error_lines:
                    if line.strip():
                        print(f"  {line.strip()}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            # Clean up text files on error
            if overlay_text and 'text_file' in locals() and text_file.exists():
                text_file.unlink()
            # Clean up line files
            for i in range(10):
                line_file = self.script_dir / f"overlay_text_line_{i}.txt"
                if line_file.exists():
                    line_file.unlink()
            return False
    
    def combine_videos_fallback(self, hook_path, demo_path, audio_path, overlay_text, hook_duration):
        """Fallback method without custom font"""
        print("\n🔄 Retrying with simplified text overlay...")
        
        # Wrap text for margins (5% on each side)
        wrapped_text = self.wrap_text_for_margins(overlay_text, margin_percent=5)
        
        # Create a temporary text file
        text_file = self.script_dir / "overlay_text.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(wrapped_text)
        
        # Build filter without fontfile parameter
        drawtext_filter = (
            f"drawtext="
            f"textfile='{str(text_file)}'"
            f":fontsize=75"  # 75pt font size
            f":fontcolor=white"
            f":borderw=4"
            f":bordercolor=black"
            f":x=(w-text_w)/2"  # Center horizontally
            f":y=(h-text_h)/2+100"  # Slightly below center (shifted down by 100 pixels)
            f":text_align=C"  # Center align text
            f":enable='between(t,0,5)'"
        )
        
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"{drawtext_filter}[v0];"
            "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[v1];"
            "[v0][v1]concat=n=2:v=1:a=0[outv];"
            f"aevalsrc=0:d={hook_duration}:s=44100:c=stereo[silence];"
            "[1:a]aformat=sample_rates=44100:channel_layouts=stereo[demo_audio];"
            "[silence][demo_audio]concat=n=2:v=0:a=1[original_audio];"
            "[2:a]volume=-15dB[overlay_audio];"
            "[original_audio][overlay_audio]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
        
        cmd = [
            'ffmpeg',
            '-i', str(hook_path),
            '-i', str(demo_path),
            '-i', str(audio_path),
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-movflags', '+faststart',
            '-y',
            str(self.output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up text file
            if text_file.exists():
                text_file.unlink()
            
            if result.returncode == 0:
                output_duration = self.get_video_duration(self.output_path)
                print(f"\n✅ Success! Output video created ({output_duration:.1f}s)")
                print(f"📍 Location: {self.output_path}")
                return True
            else:
                print(f"\n❌ Fallback also failed")
                print("Creating video without text overlay...")
                return self.combine_videos_no_text(hook_path, demo_path, audio_path, hook_duration)
        except Exception as e:
            print(f"\n❌ Fallback error: {str(e)}")
            # Clean up text file on error
            if text_file.exists():
                text_file.unlink()
            return False
    
    def combine_videos_no_text(self, hook_path, demo_path, audio_path, hook_duration):
        """Combine videos without any text overlay"""
        print("\n⚠️  Creating video without text overlay...")
        
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v0];"
            f"[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[v1];"
            f"[v0][v1]concat=n=2:v=1:a=0[outv];"
            f"aevalsrc=0:d={hook_duration}:s=44100:c=stereo[silence];"
            f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo[demo_audio];"
            f"[silence][demo_audio]concat=n=2:v=0:a=1[original_audio];"
            f"[2:a]volume=-15dB[overlay_audio];"
            f"[original_audio][overlay_audio]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
        
        cmd = [
            'ffmpeg',
            '-i', str(hook_path),
            '-i', str(demo_path),
            '-i', str(audio_path),
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-movflags', '+faststart',
            '-y',
            str(self.output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                output_duration = self.get_video_duration(self.output_path)
                print(f"\n✅ Success! Output video created ({output_duration:.1f}s)")
                print(f"📍 Location: {self.output_path}")
                print(f"⚠️  Note: Text overlay was omitted due to processing issues")
                return True
            else:
                print(f"\n❌ Video creation failed")
                return False
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return False
    
    def run(self):
        """Main execution"""
        print("=" * 50)
        print("VIDEO COMBINER SCRIPT")
        print("=" * 50)
        
        # Check FFmpeg
        if not self.check_dependencies():
            return False
        
        # Find files
        print("\n📁 Searching for files...")
        
        hook_video = self.find_file(self.hooks_folder, self.video_extensions)
        if not hook_video:
            print(f"Please add a video file to: {self.hooks_folder}")
            return False
        
        demo_video = self.find_file(self.demo_folder, self.video_extensions)
        if not demo_video:
            print(f"Please add a video file to: {self.demo_folder}")
            return False
        
        audio_file = self.find_file(self.audio_folder, self.audio_extensions)
        if not audio_file:
            print(f"Please add an audio file to: {self.audio_folder}")
            return False
        
        # Combine videos
        success = self.combine_videos(hook_video, demo_video, audio_file)
        
        if success:
            print("\n🎉 Video combination complete!")
            print(f"Your video is ready: {self.output_path.name}")
        else:
            print("\n❌ Video combination failed")
            print("Please check that your video files are valid MP4/MOV files")
        
        return success

def main():
    """Entry point"""
    combiner = VideoCombiner()
    success = combiner.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()