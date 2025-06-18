import os
import sys
import json
import time
import math
import random
import hashlib
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import ImageTk
from datetime import datetime

# Try importing optional dependencies with graceful fallback
try:
    from qrcode import QRCode, constants

    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("Warning: qrcode module not available. QR code features will be disabled.")

try:
    from opencv import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python module not available. QR code scanning will be disabled.")

try:
    import openai
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI module not available. AI features will be limited.")

try:
    import speech_recognition as sr

    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("Warning: speech_recognition not available. Voice input will be disabled.")


# ===============================================================================
# File Usage Analytics Class
# ===============================================================================

class FileUsageAnalytics:
    """Track file usage patterns"""

    def __init__(self):
        self.usage_data = {}
        self.load_data()

    def record_access(self, filepath):
        """Record an access to a file"""
        now = time.time()

        if filepath not in self.usage_data:
            self.usage_data[filepath] = {
                'accesses': 0,
                'first_access': now,
                'last_access': now,
                'access_times': []
            }

        self.usage_data[filepath]['accesses'] += 1
        self.usage_data[filepath]['last_access'] = now

        # Maintain a list of the last 10 access times
        access_times = self.usage_data[filepath].get('access_times', [])
        access_times.append(now)
        if len(access_times) > 10:
            access_times = access_times[-10:]
        self.usage_data[filepath]['access_times'] = access_times

        # Save data periodically
        if random.random() < 0.1:  # 10% chance on each access
            self.save_data()

    def get_most_accessed_files(self, count=10):
        """Get the most frequently accessed files"""
        sorted_files = sorted(self.usage_data.items(),
                              key=lambda x: x[1]['accesses'], reverse=True)
        return sorted_files[:count]

    def get_recently_accessed_files(self, count=10):
        """Get the most recently accessed files"""
        sorted_files = sorted(self.usage_data.items(),
                              key=lambda x: x[1]['last_access'], reverse=True)
        return sorted_files[:count]

    def get_file_stats(self, filepath):
        """Get usage statistics for a specific file"""
        if filepath not in self.usage_data:
            return None

        data = self.usage_data[filepath]

        # Calculate additional metrics
        days_since_first = (time.time() - data['first_access']) / (60 * 60 * 24)
        days_since_last = (time.time() - data['last_access']) / (60 * 60 * 24)

        # Calculate access frequency (accesses per day)
        frequency = data['accesses'] / max(1, days_since_first)

        return {
            'accesses': data['accesses'],
            'first_access': time.ctime(data['first_access']),
            'last_access': time.ctime(data['last_access']),
            'days_since_last_access': round(days_since_last, 1),
            'access_frequency': round(frequency, 2)
        }

    def load_data(self):
        """Load usage data from file"""
        try:
            if os.path.exists('file_usage_data.json'):
                with open('file_usage_data.json', 'r') as f:
                    self.usage_data = json.load(f)
        except Exception as e:
            print(f"Error loading usage data: {e}")

    def save_data(self):
        """Save usage data to file"""
        try:
            with open('file_usage_data.json', 'w') as f:
                json.dump(self.usage_data, f)
        except Exception as e:
            print(f"Error saving usage data: {e}")


# ===============================================================================
# Smart Tagging System Class
# ===============================================================================

class SmartTaggingSystem:
    """Intelligent file tagging system"""

    def __init__(self, openai_client=None):
        self.tags_data = {}
        self.openai_client = openai_client
        self.load_tags()

    def add_tag(self, filepath, tag):
        """Add a tag to a file"""
        if filepath not in self.tags_data:
            self.tags_data[filepath] = {'tags': [], 'auto_tags': []}

        tags = self.tags_data[filepath]['tags']
        if tag not in tags:
            tags.append(tag)
            self.save_tags()
            return True
        return False

    def remove_tag(self, filepath, tag):
        """Remove a tag from a file"""
        if filepath in self.tags_data and tag in self.tags_data[filepath]['tags']:
            self.tags_data[filepath]['tags'].remove(tag)
            self.save_tags()
            return True
        return False

    def get_file_tags(self, filepath):
        """Get all tags for a file"""
        if filepath not in self.tags_data:
            return [], []

        return (
            self.tags_data[filepath].get('tags', []),
            self.tags_data[filepath].get('auto_tags', [])
        )

    def find_files_by_tag(self, tag):
        """Find all files with a specific tag"""
        matching_files = []

        for filepath, data in self.tags_data.items():
            if tag in data.get('tags', []) or tag in data.get('auto_tags', []):
                matching_files.append(filepath)

        return matching_files

    # def auto_tag_file(self, filepath):
    #     """Use AI to automatically suggest tags for a file"""
    #     if not self.openai_client:
    #         return []
    #
    #     try:
    #         # Read file content or metadata
    #         filename = os.path.basename(filepath)
    #         ext = os.path.splitext(filepath)[1].lower()
    #
    #         # For small text files, include content
    #         content = ""
    #         if os.path.getsize(filepath) < 50000 and ext in ['.txt', '.md', '.py', '.js', '.html', '.css']:
    #             with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
    #                 content = f.read(5000)  # Read first 5KB
    #
    #         # Use OpenAI to generate tags
    #         response = self.openai_client.chat.completions.create(
    #             model="gpt-3.5-turbo",  # Use a smaller model to save costs
    #             messages=[
    #                 {"role": "system",
    #                  "content": "Generate 3-5 relevant tags for this file based on its name, extension, and content if provided. Return only a comma-separated list of tags, nothing else."},
    #                 {"role": "user", "content": f"Filename: {filename}\nExtension: {ext}\nContent snippet: {content}"}
    #             ],
    #             max_tokens=50,
    #             temperature=0.3
    #         )
    #
    #         tags = [tag.strip() for tag in response.choices[0].message.content.split(',')]
    #
    #         # Store auto-generated tags
    #         if filepath not in self.tags_data:
    #             self.tags_data[filepath] = {'tags': [], 'auto_tags': []}
    #
    #         self.tags_data[filepath]['auto_tags'] = tags
    #         self.save_tags()
    #
    #         return tags
    #
    #     except Exception as e:
    #         print(f"Error auto-tagging file: {e}")
    #         return []

    def get_all_tags(self):
        """Get a list of all used tags"""
        all_tags = set()

        for data in self.tags_data.values():
            all_tags.update(data.get('tags', []))

        return sorted(list(all_tags))

    def load_tags(self):
        """Load tags data from file"""
        try:
            if os.path.exists('file_tags.json'):
                with open('file_tags.json', 'r') as f:
                    self.tags_data = json.load(f)
        except Exception as e:
            print(f"Error loading tags data: {e}")

    def save_tags(self):
        """Save tags data to file"""
        try:
            with open('file_tags.json', 'w') as f:
                json.dump(self.tags_data, f)
        except Exception as e:
            print(f"Error saving tags data: {e}")


# ===============================================================================
# File Health Monitor Class
# ===============================================================================

class FileHealthMonitor:
    """Monitor and check file health and integrity"""

    def __init__(self):
        self.file_hashes = {}
        self.load_hashes()

    def check_file_integrity(self, filepath):
        """Check if a file has been modified since last check"""
        if not os.path.exists(filepath):
            return {'exists': False}

        current_hash = self._get_file_hash(filepath)

        if filepath in self.file_hashes:
            stored_hash = self.file_hashes[filepath]['hash']
            if current_hash != stored_hash:
                return {
                    'exists': True,
                    'changed': True,
                    'last_verified': self.file_hashes[filepath].get('timestamp')
                }
            else:
                return {
                    'exists': True,
                    'changed': False,
                    'last_verified': self.file_hashes[filepath].get('timestamp')
                }

        # First time seeing this file
        self.file_hashes[filepath] = {
            'hash': current_hash,
            'timestamp': time.time()
        }
        self.save_hashes()

        return {'exists': True, 'changed': False, 'first_check': True}

    def check_for_problems(self, filepath):
        """Check for common problems with the file"""
        problems = []

        if not os.path.exists(filepath):
            return ["File doesn't exist"]

        # Check if the file is empty
        if os.path.getsize(filepath) == 0:
            problems.append("File is empty")

        # Check if file has unusual permissions
        try:
            mode = os.stat(filepath).st_mode
            if not (mode & 0o400):  # Check for read permission
                problems.append("File is not readable")
            if not (mode & 0o200):  # Check for write permission
                problems.append("File is not writable")
        except:
            problems.append("Can't check file permissions")

        # For text files, check for encoding issues
        _, ext = os.path.splitext(filepath)
        if ext.lower() in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md']:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    f.read(1024)  # Try to read a small part of the file
            except UnicodeDecodeError:
                problems.append("File has encoding issues (not UTF-8)")

        return problems

    def _get_file_hash(self, filepath):
        """Calculate a hash of the file's content"""
        try:
            hasher = hashlib.md5()
            with open(filepath, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return None

    def verify_all_files(self, directory):
        """Check integrity of all previously verified files in a directory"""
        results = {
            'changed': [],
            'missing': [],
            'ok': []
        }

        # Check only files we've previously hashed
        for filepath in list(self.file_hashes.keys()):
            if not filepath.startswith(directory):
                continue

            if not os.path.exists(filepath):
                results['missing'].append(filepath)
                continue

            current_hash = self._get_file_hash(filepath)
            stored_hash = self.file_hashes[filepath]['hash']

            if current_hash != stored_hash:
                results['changed'].append(filepath)
            else:
                results['ok'].append(filepath)

        return results

    def load_hashes(self):
        """Load saved file hashes"""
        try:
            if os.path.exists('file_hashes.json'):
                with open('file_hashes.json', 'r') as f:
                    self.file_hashes = json.load(f)
        except Exception as e:
            print(f"Error loading file hashes: {e}")

    def save_hashes(self):
        """Save file hashes"""
        try:
            with open('file_hashes.json', 'w') as f:
                json.dump(self.file_hashes, f)
        except Exception as e:
            print(f"Error saving file hashes: {e}")

    # ===============================================================================
    # Voice Assistant Class
    # ===============================================================================

    # class VoiceAssistant:
    """Voice assistant for file explorer"""


try:
    import pyttsx3
    import speech_recognition as sr

    PYTTSX3_AVAILABLE = True
    SR_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    SR_AVAILABLE = False


class VoiceAssistant:
    def __init__(self, explorer):
        self.explorer = explorer
        self.engine = None
        self.recognizer = None
        self.listening = False
        self.current_command = None
        self.init_voice_engine()
        self.init_speech_recognition()

    def init_voice_engine(self):
        if not PYTTSX3_AVAILABLE:
            return
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
        except Exception as e:
            print(f"Voice engine error: {e}")
            self.engine = None

    def init_speech_recognition(self):
        if not SR_AVAILABLE:
            return
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 4000
            self.recognizer.pause_threshold = 0.8
        except Exception as e:
            print(f"Speech recognition error: {e}")
            self.recognizer = None

    def start_voice_assistant(self):
        if not self.recognizer:
            messagebox.showerror("Error", "Speech recognition not available.")
            return
        self._show_listening_indicator()
        self.speak("Voice assistant started. Awaiting your command.")
        self.listening = True
        threading.Thread(target=self._listen_for_commands, daemon=True).start()

    def stop_voice_assistant(self):
        self.listening = False
        self.speak("Voice assistant stopped.")

    def _listen_for_commands(self):
        while self.listening:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                try:
                    text = self.recognizer.recognize_google(audio)
                    self.process_command(text.lower())
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError:
                    self.speak("Voice service unavailable.")
            except Exception as e:
                print(f"Voice command error: {e}")
                self.listening = False

    def speak(self, text):
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"Speech error: {e}")

    def _show_listening_indicator(self):
        try:
            indicator = tk.Toplevel(self.explorer.root)
            indicator.title("Listening")
            indicator.geometry("300x100")
            indicator.transient(self.explorer.root)
            ttk.Label(indicator, text="🎤 Listening...", font=("Arial", 14)).pack(pady=10)
            ttk.Button(indicator, text="Stop", command=self.stop_voice_assistant).pack(pady=10)

            def check_listening():
                if not self.listening:
                    indicator.destroy()
                else:
                    indicator.after(500, check_listening)

            check_listening()
        except Exception as e:
            print(f"UI error: {e}")

    def process_command(self, text):
        self.current_command = text
        if "open" in text or "go to" in text:
            self._handle_navigation(text)
        elif "back" in text:
            self.explorer.go_back()
        elif "up" in text:
            self.explorer.go_up()
        elif "create file" in text:
            name = text.split("file")[-1].strip()
            self.explorer.create_file(name=name)
        elif "create folder" in text:
            name = text.split("folder")[-1].strip()
            self.explorer.make_dir(name=name)
        elif "delete" in text:
            self.explorer.delete_file()
        elif "rename to" in text:
            name = text.split("to")[-1].strip()
            self.explorer.rename_file(new_name=name)
        elif "search" in text:
            keyword = text.split("search")[-1].strip()
            self.explorer.search_var.set(keyword)
            self.explorer.search_files()
        elif "stop" in text or "exit" in text:
            self.stop_voice_assistant()
        else:
            self.speak("Command not recognized.")
        self.current_command = None

    def _handle_navigation(self, text):
        if "downloads" in text:
            target = os.path.join(os.path.expanduser("~"), "Downloads")
        elif "documents" in text:
            target = os.path.join(os.path.expanduser("~"), "Documents")
        elif "desktop" in text:
            target = os.path.join(os.path.expanduser("~"), "Desktop")
        else:
            self.speak("Navigation path not recognized.")
            return
        if os.path.exists(target):
            self.explorer.current_directory = target
            self.explorer.load_files()
            self.speak("Opened " + os.path.basename(target))


# ===============================================================================
# QR Code Manager Class
# ===============================================================================

class QRCodeManager:
    """Class to handle QR code generation and scanning for file access"""

    def __init__(self, explorer):
        self.explorer = explorer

    def generate_qr_for_selected(self):
        """Generate QR code for selected file or folder"""
        if not QRCODE_AVAILABLE:
            messagebox.showerror("Error", "QR code functionality requires the 'qrcode' module.")
            return

        # Get selected file or folder
        selected = self.explorer.get_selected_items()
        if not selected:
            messagebox.showinfo("Info", "Please select a file or folder first.")
            return

        if len(selected) > 1:
            messagebox.showinfo("Info", "Please select only one file or folder.")
            return

        file_path = selected[0]

        # Create a dialog to choose QR code type
        dialog = tk.Toplevel(self.explorer.root)
        dialog.title("Generate QR Code")
        dialog.geometry("400x300")
        dialog.transient(self.explorer.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Generate QR Code for:", font=("Arial", 12)).pack(pady=10)
        ttk.Label(dialog, text=file_path, wraplength=380).pack(pady=5)

        ttk.Separator(dialog, orient="horizontal").pack(fill="x", padx=20, pady=10)

        qr_type = tk.StringVar(value="path")

        # QR code options
        ttk.Radiobutton(dialog, text="File Path (scannable by another file explorer)",
                        variable=qr_type, value="path").pack(anchor="w", padx=20, pady=5)

        if os.path.isfile(file_path) and os.path.getsize(file_path) < 2000:
            # Only offer content option for small text files
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(100)  # Read a sample
                    if all(c.isprintable() or c.isspace() for c in content):
                        ttk.Radiobutton(dialog, text="File Content (for small text files)",
                                        variable=qr_type, value="content").pack(anchor="w", padx=20, pady=5)
            except:
                pass

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def on_generate():
            qr_choice = qr_type.get()
            dialog.destroy()

            if qr_choice == "path":
                self.generate_file_path_qr(file_path)
            elif qr_choice == "content":
                self.generate_file_content_qr(file_path)

        ttk.Button(button_frame, text="Generate", command=on_generate).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=10)

    def generate_file_content_qr(self, file_path):
        """Generate QR code with file content (if it's a small text file)"""
        if not QRCODE_AVAILABLE:
            messagebox.showerror("Error", "QR code functionality requires the 'qrcode' module.")
            return

        try:
            # Check if file is small enough
            if os.path.getsize(file_path) > 2000:  # Arbitrary limit - QR codes can't hold much data
                messagebox.showinfo("Info", "File is too large for content QR code. Using path instead.")
                self.generate_file_path_qr(file_path)
                return

            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            # Generate QR code
            self.show_qr_code(content, f"File Content QR Code - {os.path.basename(file_path)}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not read file content: {e}")

    def generate_file_path_qr(self, file_path):
        """Generate QR code with the file path"""
        if not QRCODE_AVAILABLE:
            messagebox.showerror("Error", "QR code functionality requires the 'qrcode' module.")
            return

        # Generate absolute path
        abs_path = os.path.abspath(file_path)

        # Generate QR code
        self.show_qr_code(abs_path, f"File Path QR Code - {os.path.basename(file_path)}")

    def show_qr_code(self, data, title):
        """Show a QR code in a new window"""
        if not QRCODE_AVAILABLE:
            messagebox.showerror("Error", "QR code functionality requires the 'qrcode' module.")
            return

        # Create QR code
        qr = QRCode(
            version=1,
            error_correction=constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Create an image from the QR Code
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to PhotoImage
        qr_img = ImageTk.PhotoImage(img)

        # Create a window to display the QR code
        window = tk.Toplevel(self.explorer.root)
        window.title(title)
        window.transient(self.explorer.root)

        # Display the QR code
        label = ttk.Label(window, image=qr_img)
        label.image = qr_img  # Keep a reference
        label.pack(padx=20, pady=20)

        # Display the data
        ttk.Label(window, text="Scan with a QR code reader app", font=("Arial", 10)).pack(pady=5)
        data_display = tk.Text(window, height=5, width=50, wrap="word")
        data_display.insert("1.0", data)
        data_display.config(state="disabled")
        data_display.pack(padx=20, pady=10, fill="x")

        # Add save button
        button_frame = ttk.Frame(window)
        button_frame.pack(pady=10)

        def save_qr():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
                title="Save QR Code"
            )
            if file_path:
                img.save(file_path)
                messagebox.showinfo("Success", f"QR code saved to {file_path}")

        ttk.Button(button_frame, text="Save QR Code", command=save_qr).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Close", command=window.destroy).pack(side="left", padx=10)


# ===============================================================================
# Main File Explorer Class
# ===============================================================================

class AdvancedFileExplorer:
    """Main application class for the Advanced File Explorer"""

    def __init__(self, root):
        from tkinter import ttk

        # Inside your GUI class or method

        self.root = root
        self.root.title("File Expo. 😎")

        self.explorer = self
        self.engine = None
        self.recognizer = None
        self.listening = False
        self.current_command = None
        self.init_voice_engine()
        self.init_speech_recognition()
        # Set window size (80% of screen)
        width = int(self.root.winfo_screenwidth() * 0.8)
        height = int(self.root.winfo_screenheight() * 0.8)
        self.root.geometry(f"{width}x{height}")

        # Apply modern theme
        self.apply_theme()

        # Initialize components
        self.init_components()

        # Create the layout
        self.create_layout()

        # Initialize the file system navigation
        self.history = []
        self.history_position = -1
        self.current_directory = os.getcwd()
        self.navigate_to_directory(self.current_directory)

        # Bind keyboard shortcuts
        self.bind_shortcuts()

        # Initialize feature modules
        self.usage_tracker = FileUsageAnalytics()
        self.health_checker = FileHealthMonitor()
        self.tag_system = SmartTaggingSystem()
        self.voice = VoiceAssistant(self)

    def apply_theme(self):
        """Apply a modern dark theme to the application"""
        style = ttk.Style(self.root)

        # Try to use a built-in theme
        try:
            style.theme_use('clam')
        except tk.TclError:
            try:
                style.theme_use('alt')
            except tk.TclError:
                pass  # Use whatever's available

        # Configure default theme colors
        bg_color = "#ffffff"
        fg_color = "#000000"
        accent_color = "#cccccc"
        secondary_bg = "#f0f0f0"

        # Configure ttk widget styles
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', background=secondary_bg, foreground=fg_color)
        style.configure('TEntry', fieldbackground=secondary_bg, foreground=fg_color)
        style.configure('TNotebook', background=bg_color)
        style.map('TButton', background=[('active', accent_color), ('disabled', '#555555')],
                  foreground=[('active', 'white'), ('disabled', '#999999')])

        # Configure Tkinter widgets
        self.root.configure(bg=bg_color)

        # Make sure ttk widgets use the theme
        style.configure('Treeview', background=secondary_bg, foreground=fg_color, fieldbackground=secondary_bg)
        style.map('Treeview', background=[('selected', accent_color)], foreground=[('selected', 'white')])

    def change_theme(self, theme_name):
        """Change theme colors based on the selected theme"""
        style = ttk.Style(self.root)

        if theme_name == "Dark and Earthy":
            bg_color = "#46211A"
            fg_color = "#693D3D"
            accent_color = "#BA5536"
            secondary_bg = "#A43820"

        elif theme_name == "Cool Blues":
            bg_color = "#003B46"
            fg_color = "#07575B"
            accent_color = "#66A5AD"
            secondary_bg = "#C4DFE6"

        elif theme_name == "Blue-Greens":
            # Default theme
            bg_color = "#4e6b65"
            fg_color = "#E0E0E0"
            accent_color = "#384744"
            secondary_bg = "#4e6b65"

        elif theme_name == "Vibrant Twist":
            # Default theme
            bg_color = "#375E97"
            fg_color = "#FB6542"
            accent_color = "#FFBB00"
            secondary_bg = "#3F681C"

        elif theme_name == "Mountains":
            # Default theme
            bg_color = "#324851"
            fg_color = "#86AC41"
            accent_color = "#7DA3A1"
            secondary_bg = "#34675C"

        elif theme_name == "Autumn in Vermont":
            bg_color = "#8D230F"
            fg_color = "#1E434C"
            accent_color = "#9B4F0F"
            secondary_bg = "#C99E10"

        # Apply the new theme colors
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', background=secondary_bg, foreground=fg_color)
        style.configure('TEntry', fieldbackground=secondary_bg, foreground=fg_color)
        style.configure('TNotebook', background=bg_color)
        style.map('TButton', background=[('active', accent_color), ('disabled', '#555555')],
                  foreground=[('active', 'white'), ('disabled', '#999999')])

        self.root.configure(bg=bg_color)

        # Ensure ttk widgets use the updated theme
        style.configure('Treeview', background=secondary_bg, foreground=fg_color, fieldbackground=secondary_bg)
        style.map('Treeview', background=[('selected', accent_color)], foreground=[('selected', 'white')])

    def open_theme_popup(self):
        """Open a popup window to select a theme"""
        popup = tk.Toplevel(self.root)
        popup.title("Choose Theme")
        popup.geometry("300x200")
        popup.configure(bg="#dddddd")

        # Add theme buttons
        btn1 = tk.Button(popup, text="Dark and Earthy",
                         command=lambda: [self.change_theme("Dark and Earthy"), popup.destroy()])
        btn2 = tk.Button(popup, text="Cool Blues", command=lambda: [self.change_theme("Cool Blues"), popup.destroy()])
        btn3 = tk.Button(popup, text="Blue-Greens", command=lambda: [self.change_theme("Blue-Greens"), popup.destroy()])
        btn4 = tk.Button(popup, text="Vibrant Twist",
                         command=lambda: [self.change_theme("Vibrant Twist"), popup.destroy()])
        btn5 = tk.Button(popup, text="Mountains", command=lambda: [self.change_theme("Mountains"), popup.destroy()])
        btn6 = tk.Button(popup, text="Autumn in Vermont",
                         command=lambda: [self.change_theme("Autumn in Vermont"), popup.destroy()])
        btn1.grid(row=0, column=0, padx=10, pady=10)
        btn2.grid(row=0, column=1, padx=10, pady=10)
        btn3.grid(row=1, column=0, padx=10, pady=10)
        btn4.grid(row=1, column=1, padx=10, pady=10)
        btn5.grid(row=2, column=0, padx=10, pady=10)
        btn6.grid(row=2, column=1, padx=10, pady=10)

    # Other methods like init_components, create_layout, etc. go here

    def init_components(self):
        """Initialize the application components"""
        # Initialize search engine
        # self.search_engine = AISearchEngine()

        # Initialize analytics
        self.analytics = FileUsageAnalytics()

        # Initialize tagging system
        self.tagging = SmartTaggingSystem()

        # Initialize health monitor
        self.health_monitor = FileHealthMonitor()

        # Initialize QR code manager
        self.qr_manager = QRCodeManager(self)

        # Initialize voice assistant
        self.voice_assistant = VoiceAssistant(self)

        # Initialize clipboard
        self.clipboard = None

    def create_layout(self):
        """Create the main application layout"""
        # Create menu bar
        self.create_menu_bar()

        # Main content frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left sidebar for bookmarks and tags
        sidebar_width = 200
        self.sidebar_frame = ttk.Frame(main_frame, width=sidebar_width)
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 10))

        # Make sure the sidebar stays at the desired width
        self.sidebar_frame.pack_propagate(False)

        # Create sidebar content
        self.create_sidebar()

        # Right main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side="right", fill="both", expand=True)

        # Path and search bar
        path_frame = ttk.Frame(content_frame)
        path_frame.pack(fill="x", pady=(0, 10))

        # Back, forward, up buttons
        nav_frame = ttk.Frame(path_frame)
        nav_frame.pack(side="left", padx=(0, 10))

        self.back_button = ttk.Button(nav_frame, text="←", width=3,
                                      command=self.go_back)
        self.back_button.pack(side="left", padx=(0, 2))

        self.forward_button = ttk.Button(nav_frame, text="→", width=3,
                                         command=self.go_forward)
        self.forward_button.pack(side="left", padx=(0, 2))

        self.up_button = ttk.Button(nav_frame, text="↑", width=3,
                                    command=self.go_up)
        self.up_button.pack(side="left")

        # Path entry
        ttk.Label(path_frame, text="Path:").pack(side="left", padx=(0, 5))
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.path_entry.bind("<Return>", self.navigate_path)

        # Main and preview areas with adjustable separator
        self.paned_window = ttk.PanedWindow(content_frame, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True)

        # Files frame on the left
        self.files_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.files_frame, weight=3)

        # Files treeview
        self.create_files_view()

        # Statusbar
        self.status_var = tk.StringVar()
        statusbar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        statusbar.pack(side="bottom", fill="x")

        # Update status bar
        self.status_var.set("Ready")

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New File", command=self.create_file)
        file_menu.add_command(label="New Folder", command=self.make_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Cut", command=self.cut_file)
        edit_menu.add_command(label="Copy", command=self.copy_file)
        edit_menu.add_command(label="Paste", command=self.paste_file)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Delete", command=self.delete_file)
        edit_menu.add_command(label="Rename", command=self.rename_file)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Refresh", command=self.refresh)
        view_menu.add_separator()
        view_menu.add_command(label="Sort by Name", command=lambda: self.sort_files("name"))
        view_menu.add_command(label="Sort by Type", command=lambda: self.sort_files("type"))
        view_menu.add_command(label="Sort by Size", command=lambda: self.sort_files("size"))
        view_menu.add_command(label="Sort by Date", command=lambda: self.sort_files("date"))
        menubar.add_cascade(label="View", menu=view_menu)

        # Tools menu
        enu = tk.Menu(menubar, tearoff=0)  # Creates a submenu

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="AI File Summary", command=self.summarize_selected_file)
        tools_menu.add_command(label="Generate QR Code", command=self.qr_manager.generate_qr_for_selected)
        tools_menu.add_separator()
        tools_menu.add_command(label="Check File Health", command=self.check_file_health)
        tools_menu.add_separator()
        tools_menu.add_command(label="Voice Commands", command=self.voice_assistant.start_voice_assistant)
        tools_menu.add_command(label="Change Theme", command=self.open_theme_popup)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def create_sidebar(self):
        """Create the sidebar with bookmarks and tags"""
        # Favorites/Bookmarks section
        ttk.Label(self.sidebar_frame, text="FAVORITES", font=("Arial", 9, "bold")).pack(anchor="w", padx=10,
                                                                                        pady=(10, 5))

        self.bookmarks_frame = ttk.Frame(self.sidebar_frame)
        self.bookmarks_frame.pack(fill="x", padx=5, pady=5)

        # Add default bookmarks
        self.bookmarks = [
            {"name": "Home", "path": os.path.expanduser("~")},
            {"name": "Documents", "path": os.path.join(os.path.expanduser("~"), "Documents")},
            {"name": "Downloads", "path": os.path.join(os.path.expanduser("~"), "Downloads")},
            {"name": "Desktop", "path": os.path.join(os.path.expanduser("C:/Users/Parvati/OneDrive"), "Desktop")},
        ]

        self.update_bookmarks_ui()

        # Add bookmark button
        ttk.Button(self.sidebar_frame, text="+ Add Bookmark",
                   command=self.add_bookmark).pack(fill="x", padx=5, pady=(0, 10))

        # Separator
        ttk.Separator(self.sidebar_frame, orient="horizontal").pack(fill="x", padx=5, pady=5)

        # Tags section
        ttk.Label(self.sidebar_frame, text="TAGS", font=("Arial", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.tags_frame = ttk.Frame(self.sidebar_frame)
        self.tags_frame.pack(fill="x", padx=5, pady=5)

        # Update tags UI
        self.update_tags_ui()

        # Add tag button
        ttk.Button(self.sidebar_frame, text="+ Add Tag",
                   command=self.add_tag_to_selected).pack(fill="x", padx=5, pady=(0, 10))

        # Separator
        ttk.Separator(self.sidebar_frame, orient="horizontal").pack(fill="x", padx=5, pady=5)

        # Recent files section
        ttk.Label(self.sidebar_frame, text="RECENT FILES", font=("Arial", 9, "bold")).pack(anchor="w", padx=10,
                                                                                           pady=(10, 5))

        self.recent_frame = ttk.Frame(self.sidebar_frame)
        self.recent_frame.pack(fill="x", padx=5, pady=5)

        # Update recent files UI
        self.update_recent_files_ui()

    def update_bookmarks_ui(self):
        """Update the bookmarks section in the sidebar"""
        # Clear existing bookmarks
        for widget in self.bookmarks_frame.winfo_children():
            widget.destroy()

        # Add bookmark items
        for bookmark in self.bookmarks:
            bookmark_frame = ttk.Frame(self.bookmarks_frame)
            bookmark_frame.pack(fill="x", pady=1)

            ttk.Button(bookmark_frame, text=bookmark["name"],
                       command=lambda p=bookmark["path"]: self.navigate_to_directory(p),
                       style="Toolbutton").pack(side="left", fill="x", expand=True)

    def update_tags_ui(self):
        """Update the tags section in the sidebar"""
        # Clear existing tags
        # for widget in self.tags_frame.winfo_children():
        #    widget.destroy()

        # Get all tags
        all_tags = self.tagging.get_all_tags()

        # Add tag items
        for tag in all_tags:
            tag_frame = ttk.Frame(self.tags_frame)
            tag_frame.pack(fill="x", pady=1)

            ttk.Button(tag_frame, text=tag,
                       command=lambda t=tag: self.find_files_by_tag(t),
                       style="Toolbutton").pack(side="left", fill="x", expand=True)

    def update_recent_files_ui(self):
        """Update the recent files section in the sidebar"""
        # Clear existing recent files
        for widget in self.recent_frame.winfo_children():
            widget.destroy()

        # Get recent files
        recent_files = self.analytics.get_recently_accessed_files(count=5)

        # Add recent file items
        for file_path, _ in recent_files:
            if os.path.exists(file_path):
                file_frame = ttk.Frame(self.recent_frame)
                file_frame.pack(fill="x", pady=1)

                filename = os.path.basename(file_path)

                # Truncate long filenames
                if len(filename) > 20:
                    display_name = filename[:17] + "..."
                else:
                    display_name = filename

                ttk.Button(file_frame, text=display_name,
                           command=lambda p=file_path: self.open_file_from_path(p),
                           style="Toolbutton").pack(side="left", fill="x", expand=True)

    def create_files_view(self):
        """Create the files treeview"""
        # Create a frame for the treeview and scrollbars
        tree_frame = ttk.Frame(self.files_frame)
        tree_frame.pack(fill="both", expand=True)

        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Create the treeview
        self.files_tree = ttk.Treeview(
            tree_frame,
            columns=("name", "type", "size", "date"),
            selectmode="extended",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Configure scrollbars
        v_scrollbar.config(command=self.files_tree.yview)
        h_scrollbar.config(command=self.files_tree.xview)

        # Configure columns
        self.files_tree.heading("name", text="Name")
        self.files_tree.heading("type", text="Type")
        self.files_tree.heading("size", text="Size")
        self.files_tree.heading("date", text="Modified")

        # Set column widths
        self.files_tree.column("name", width=200, minwidth=100)
        self.files_tree.column("type", width=100, minwidth=50)
        self.files_tree.column("size", width=80, minwidth=50)
        self.files_tree.column("date", width=120, minwidth=80)

        # Hide the first column (which would show the id)
        self.files_tree["show"] = "headings"

        # Pack the treeview and scrollbars
        self.files_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")

        # Bind events
        self.files_tree.bind("<Double-1>", self.open_file)
        self.files_tree.bind("<Return>", self.open_file)
        self.files_tree.bind("<Delete>", self.delete_file)
        self.files_tree.bind("<F2>", self.rename_file)
        self.files_tree.bind("<<TreeviewSelect>>", self.on_file_select)

        # Create a right-click context menu
        self.context_menu = tk.Menu(self.files_tree, tearoff=0)

        # Bind right-click event
        if sys.platform == "darwin":  # macOS
            self.files_tree.bind("<Button-2>", self.show_context_menu)
        else:
            self.files_tree.bind("<Button-3>", self.show_context_menu)

    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        # File operations
        self.root.bind("<Control-n>", lambda e: self.create_file())
        self.root.bind("<Control-Shift-N>", lambda e: self.make_dir())

        # Edit operations
        self.root.bind("<Control-x>", lambda e: self.cut_file())
        self.root.bind("<Control-c>", lambda e: self.copy_file())
        self.root.bind("<Control-v>", lambda e: self.paste_file())
        self.root.bind("<Control-a>", lambda e: self.select_all())

        # Navigation
        self.root.bind("<Alt-Left>", lambda e: self.go_back())
        self.root.bind("<Alt-Right>", lambda e: self.go_forward())
        self.root.bind("<Alt-Up>", lambda e: self.go_up())
        self.root.bind("<F5>", lambda e: self.refresh())

        # Search
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set())

        # Tools
        self.root.bind("<Control-q>", lambda e: self.qr_manager.generate_qr_for_selected())
        self.root.bind("<Control-Shift-Q>", lambda e: self.qr_manager.scan_qr_code())

        # Voice commands
        self.root.bind("<F1>", lambda e: self.start_voice_assistant())

    def navigate_to_directory(self, path):
        """Navigate to the specified directory"""
        try:
            if os.path.isdir(path):
                os.chdir(path)
                self.current_directory = path
                self.path_var.set(path)
                self.load_files()
                self.add_to_history(path)
                self.status_var.set(f"Navigated to {path}")
                return True
            else:
                messagebox.showerror("Error", f"'{path}' is not a directory.")
                return False
        except Exception as e:
            messagebox.showerror("Error", f"Cannot access directory: {e}")
            return False

    def load_files(self):
        """Load files in the current directory into the treeview"""
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        try:
            # Get list of files and directories
            items = os.listdir(self.current_directory)

            # Sort items (directories first, then files)
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(self.current_directory, x)), x.lower()))

            for item in items:
                path = os.path.join(self.current_directory, item)

                # Skip hidden items
                if item.startswith('.'):
                    continue

                try:
                    # Get item info
                    stats = os.stat(path)
                    size = stats.st_size
                    modified = stats.st_mtime

                    # Format date
                    date_str = self.format_date(modified)

                    # Determine type
                    if os.path.isdir(path):
                        type_str = "Folder"
                        size_str = ""
                    else:
                        # Get file extension
                        _, ext = os.path.splitext(item)
                        type_str = ext[1:].upper() if ext else "File"
                        size_str = self.format_size(size)

                    # Add to treeview
                    self.files_tree.insert(
                        "", "end",
                        values=(item, type_str, size_str, date_str),
                        tags=("folder" if os.path.isdir(path) else "file")
                    )

                except:
                    # Skip items that can't be accessed
                    continue

            # Update status bar
            self.status_var.set(f"{len(self.files_tree.get_children())} items")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading files: {e}")

    def on_file_select(self, event):
        """Handle file selection event"""
        # Get selected item
        selected = self.get_selected_items()
        # Single item selected, show preview
        file_path = selected[0]

        # Record access in analytics
        self.analytics.record_access(file_path)

    def format_size(self, size_bytes):  # this is copied from gpt
        """Format file size in human-readable format"""
        # Handle None or invalid input
        if not isinstance(size_bytes, (int, float)) or size_bytes < 0:
            return "0 B"

        # Define units and their thresholds
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

        # For very small values, return bytes without decimal places
        if size_bytes < 1024:
            return f"{size_bytes} B"

        # Find the appropriate unit
        unit_index = min(int(math.log(size_bytes, 1024)), len(units) - 1)

        # Convert to the chosen unit
        value = size_bytes / (1024 ** unit_index)

        # Format with 1 decimal place for KB and above, none for bytes
        if unit_index > 0:
            return f"{value:.1f} {units[unit_index]}"
        else:
            return f"{value:.0f} {units[unit_index]}"

    def format_date(self, timestamp):
        """Format a timestamp as a date string"""
        # Convert timestamp to datetime
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()

        # If date is today, just show time
        if dt.date() == now.date():
            return dt.strftime("Today %H:%M")

        # If date is within the last week, show day of week
        delta = now.date() - dt.date()
        if delta.days < 7:
            return dt.strftime("%a %H:%M")

        # Otherwise show full date
        return dt.strftime("%Y-%m-%d %H:%M")

    def get_selected_items(self):
        """Get paths of selected items"""
        selected = []

        for item_id in self.files_tree.selection():
            # Get item values
            values = self.files_tree.item(item_id, "values")
            if values:
                item_name = values[0]
                item_path = os.path.join(self.current_directory, item_name)
                selected.append(item_path)

        return selected

    def add_to_history(self, path):
        """Add a path to navigation history"""
        # If we're not at the end of history, truncate it
        if self.history_position < len(self.history) - 1:
            self.history = self.history[:self.history_position + 1]

        # Add path to history if it's different from current
        if not self.history or self.history[-1] != path:
            self.history.append(path)
            self.history_position = len(self.history) - 1

        # Update navigation buttons
        self.update_nav_buttons()

    def update_nav_buttons(self):
        """Update the state of navigation buttons"""
        # Back button enabled if we have history to go back to
        self.back_button.state(['!disabled'] if self.history_position > 0 else ['disabled'])

        # Forward button enabled if we have history to go forward to
        self.forward_button.state(['!disabled'] if self.history_position < len(self.history) - 1 else ['disabled'])

        # Up button enabled if we're not at the root directory
        parent_dir = os.path.dirname(self.current_directory)
        self.up_button.state(['!disabled'] if parent_dir != self.current_directory else ['disabled'])

    def go_back(self):
        """Navigate back in history"""
        if self.history_position > 0:
            self.history_position -= 1
            path = self.history[self.history_position]

            # Navigate without adding to history
            if os.path.exists(path):
                os.chdir(path)
                self.current_directory = path
                self.path_var.set(path)
                self.load_files()

                # Update navigation buttons
                self.update_nav_buttons()
            else:
                # Handle deleted directory
                messagebox.showwarning("Warning", f"The directory {path} no longer exists.")
                self.history.pop(self.history_position)
                self.go_back()

    def go_forward(self):
        """Navigate forward in history"""
        if self.history_position < len(self.history) - 1:
            self.history_position += 1
            path = self.history[self.history_position]

            # Navigate without adding to history
            if os.path.exists(path):
                os.chdir(path)
                self.current_directory = path
                self.path_var.set(path)
                self.load_files()

                # Update navigation buttons
                self.update_nav_buttons()
            else:
                # Handle deleted directory
                messagebox.showwarning("Warning", f"The directory {path} no longer exists.")
                self.history.pop(self.history_position)
                self.go_forward()

    def go_up(self):
        """Navigate to parent directory"""
        parent_dir = os.path.dirname(self.current_directory)

        # Check if already at root
        if parent_dir != self.current_directory:
            self.navigate_to_directory(parent_dir)

    def navigate_path(self, event=None):
        """Navigate to the path entered in the path entry"""
        path = self.path_var.get()

        # Expand ~ to user's home directory
        if path.startswith('~'):
            path = os.path.expanduser(path)

        # Navigate to the path
        self.navigate_to_directory(path)

    def open_file(self, event=None):
        """Open selected file or directory"""
        selected = self.get_selected_items()

        if not selected:
            return

        # Get the first selected item
        path = selected[0]

        self.open_file_from_path(path)

    def open_file_from_path(self, path):
        """Open a file or directory from its path"""
        if os.path.isdir(path):
            # Navigate to directory
            self.navigate_to_directory(path)
        else:
            # Open file with default application
            try:
                # Record access in analytics
                self.analytics.record_access(path)

                if sys.platform == 'win32':
                    os.startfile(path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', path], check=True)
                else:  # Linux and others
                    subprocess.run(['xdg-open', path], check=True)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")

    def create_file(self, event=None, name=None):
        """Create a new file in the current directory"""
        if not name:
            name = simpledialog.askstring("New File", "Enter file name:")

        if not name:
            return

        try:
            path = os.path.join(self.current_directory, name)

            # Check if file already exists
            if os.path.exists(path):
                messagebox.showerror("Error", f"File '{name}' already exists.")
                return

            # Create empty file
            with open(path, 'w') as f:
                pass

            # Refresh view
            self.refresh()

            # Select the new file
            self.select_item(name)

            # Record access in analytics
            self.analytics.record_access(path)

        except Exception as e:
            messagebox.showerror("Error", f"Could not create file: {e}")

    def make_dir(self, event=None, name=None):
        """Create a new directory in the current directory"""
        if not name:
            name = simpledialog.askstring("New Folder", "Enter folder name:")

        if not name:
            return

        try:
            path = os.path.join(self.current_directory, name)

            # Check if directory already exists
            if os.path.exists(path):
                messagebox.showerror("Error", f"Folder '{name}' already exists.")
                return

            # Create directory
            os.mkdir(path)

            # Refresh view
            self.refresh()

            # Select the new directory
            self.select_item(name)

        except Exception as e:
            messagebox.showerror("Error", f"Could not create folder: {e}")

    def refresh(self, event=None):
        """Refresh the file view"""
        self.load_files()

    def select_item(self, name):
        """Select an item by name in the file view"""
        for item_id in self.files_tree.get_children():
            values = self.files_tree.item(item_id, "values")
            if values and values[0] == name:
                self.files_tree.selection_set(item_id)
                self.files_tree.see(item_id)
                self.files_tree.focus(item_id)
                return

    def show_context_menu(self, event):
        """Show context menu for selected items"""
        # Create a new context menu each time
        self.context_menu = tk.Menu(self.files_tree, tearoff=0)

        # Get selected items
        selected = self.get_selected_items()

        if not selected:
            return

        # Add menu items
        self.context_menu.add_command(label="Open", command=self.open_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cut", command=self.cut_file)
        self.context_menu.add_command(label="Copy", command=self.copy_file)
        self.context_menu.add_command(label="Paste", command=self.paste_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.delete_file)
        self.context_menu.add_command(label="Rename", command=self.rename_file)

        # Add advanced options
        self.context_menu.add_separator()

        if len(selected) == 1:
            # Single item selected
            path = selected[0]

            # Get tags
            if os.path.exists(path):
                self.context_menu.add_command(label="Add Tag", command=self.add_tag_to_selected)

                # Add file-specific options
                if os.path.isfile(path):
                    self.context_menu.add_command(label="AI Summary", command=self.summarize_selected_file)

                # All items can have QR codes
                self.context_menu.add_command(label="Generate QR Code",
                                              command=self.qr_manager.generate_qr_for_selected)

        # Show the context menu
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def delete_file(self, event=None):
        """Delete selected files/folders"""
        selected = self.get_selected_items()

        if not selected:
            return

        # Confirm deletion
        if len(selected) == 1:
            name = os.path.basename(selected[0])
            confirm = messagebox.askyesno("Confirm Delete", f"Delete '{name}'?")
        else:
            confirm = messagebox.askyesno("Confirm Delete", f"Delete {len(selected)} items?")

        if not confirm:
            return

        # Delete selected items
        for path in selected:
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete '{os.path.basename(path)}': {e}")

        # Refresh view
        self.refresh()

    def rename_file(self, event=None, new_name=None):
        """Rename selected file/folder"""
        selected = self.get_selected_items()

        if not selected or len(selected) != 1:
            return

        path = selected[0]
        old_name = os.path.basename(path)

        if not new_name:
            new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=old_name)

        if not new_name or new_name == old_name:
            return

        try:
            new_path = os.path.join(os.path.dirname(path), new_name)

            # Check if destination already exists
            if os.path.exists(new_path):
                messagebox.showerror("Error", f"'{new_name}' already exists.")
                return

            # Rename file/folder
            os.rename(path, new_path)

            # Refresh view
            self.refresh()

            # Select the renamed item
            self.select_item(new_name)

        except Exception as e:
            messagebox.showerror("Error", f"Could not rename file: {e}")

    def copy_file(self, event=None):
        """Copy selected files/folders to clipboard"""
        selected = self.get_selected_items()

        if not selected:
            return

        # Store selected items in the clipboard
        self.clipboard = {"action": "copy", "items": selected}
        self.status_var.set(f"{len(selected)} items copied to clipboard")

    def cut_file(self, event=None):
        """Cut selected files/folders to clipboard"""
        selected = self.get_selected_items()

        if not selected:
            return

        # Store selected items in the clipboard
        self.clipboard = {"action": "cut", "items": selected}
        self.status_var.set(f"{len(selected)} items cut to clipboard")

    def paste_file(self, event=None):
        """Paste files/folders from clipboard"""
        if not hasattr(self, "clipboard") or not self.clipboard:
            return

        action = self.clipboard["action"]
        items = self.clipboard["items"]

        if not items:
            return

        for src_path in items:
            try:
                # Get destination path
                filename = os.path.basename(src_path)
                dest_path = os.path.join(self.current_directory, filename)

                # Check if destination already exists
                if os.path.exists(dest_path):
                    # Ask for confirmation
                    confirm = messagebox.askyesno(
                        "Confirm Overwrite",
                        f"'{filename}' already exists. Overwrite?"
                    )

                    if not confirm:
                        continue

                    # Remove existing destination
                    if os.path.isdir(dest_path):
                        import shutil
                        shutil.rmtree(dest_path)
                    else:
                        os.remove(dest_path)

                # Copy/move the file/folder
                if os.path.isdir(src_path):
                    import shutil
                    if action == "copy":
                        shutil.copytree(src_path, dest_path)
                    else:  # cut
                        shutil.move(src_path, dest_path)
                else:
                    import shutil
                    if action == "copy":
                        shutil.copy2(src_path, dest_path)
                    else:  # cut
                        shutil.move(src_path, dest_path)

            except Exception as e:
                messagebox.showerror("Error", f"Could not paste '{os.path.basename(src_path)}': {e}")

        # Clear clipboard if items were cut (moved)
        if action == "cut":
            self.clipboard = None

        # Refresh view
        self.refresh()

    def select_all(self, event=None):
        """Select all items in the file view"""
        for item in self.files_tree.get_children():
            self.files_tree.selection_add(item)

    def add_bookmark(self):
        """Add current directory to bookmarks"""
        # Check if already in bookmarks
        for bookmark in self.bookmarks:
            if bookmark["path"] == self.current_directory:
                messagebox.showinfo("Info", "This directory is already bookmarked.")
                return

        # Ask for a name
        name = simpledialog.askstring("Bookmark", "Enter bookmark name:",
                                      initialvalue=os.path.basename(self.current_directory))

        if name:
            # Add to bookmarks
            self.bookmarks.append({"name": name, "path": self.current_directory})

            # Update UI
            self.update_bookmarks_ui()

            # Show confirmation
            self.status_var.set(f"Added bookmark: {name}")

    def add_tag_to_selected(self):
        """Add a tag to selected files"""
        selected = self.get_selected_items()

        if not selected:
            messagebox.showinfo("Info", "Please select a file or folder first.")
            return

        # Ask for the tag name
        tag = simpledialog.askstring("Add Tag", "Enter tag name:")

        if not tag:
            return

        # Add the tag to each selected item
        for path in selected:
            self.tagging.add_tag(path, tag)

        # Update tags UI
        self.update_tags_ui()

        # Show confirmation
        if len(selected) == 1:
            self.status_var.set(f"Added tag '{tag}' to {os.path.basename(selected[0])}")
        else:
            self.status_var.set(f"Added tag '{tag}' to {len(selected)} items")

    def find_files_by_tag(self, tag):
        """Find files with the specified tag"""
        # Show a loading indicator
        self.status_var.set(f"Finding files with tag '{tag}'...")
        self.root.update_idletasks()

        # Find files with the tag
        files = self.tagging.find_files_by_tag(tag)

        if not files:
            self.status_var.set(f"No files found with tag '{tag}'")
            messagebox.showinfo("Tag Search", f"No files with tag '{tag}' were found.")
            return

        # Create a dialog to show results
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Files with Tag: {tag}")
        dialog.geometry("600x400")
        dialog.transient(self.root)

        # Create a frame for the results
        ttk.Label(dialog, text=f"Files with tag '{tag}':",
                  font=("Arial", 12)).pack(pady=(10, 5), padx=10, anchor="w")

        # Create a treeview for results
        results_frame = ttk.Frame(dialog)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side="right", fill="y")

        # Create the treeview
        results_tree = ttk.Treeview(
            results_frame,
            columns=("path", "type"),
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )

        # Configure scrollbar
        scrollbar.config(command=results_tree.yview)

        # Configure columns
        results_tree.heading("#0", text="Name")
        results_tree.heading("path", text="Path")
        results_tree.heading("type", text="Type")

        # Set column widths
        results_tree.column("#0", width=150, minwidth=100)
        results_tree.column("path", width=350, minwidth=100)
        results_tree.column("type", width=80, minwidth=50)

        # Add results to treeview
        for path in files:
            try:
                if os.path.exists(path):
                    name = os.path.basename(path)
                    dir_path = os.path.dirname(path)

                    # Determine type
                    if os.path.isdir(path):
                        type_str = "Folder"
                    else:
                        # Get file extension
                        _, ext = os.path.splitext(name)
                        type_str = ext[1:].upper() if ext else "File"

                    # Add to treeview
                    results_tree.insert(
                        "", "end", text=name,
                        values=(dir_path, type_str),
                        tags=("folder" if os.path.isdir(path) else "file")
                    )
            except:
                # Skip items that can't be accessed
                continue

        # Pack the treeview
        results_tree.pack(side="left", fill="both", expand=True)

        # Handle double-click on result
        def on_result_double_click(event):
            selection = results_tree.selection()
            if selection:
                item = selection[0]
                name = results_tree.item(item, "text")
                path_value = results_tree.item(item, "values")[0]

                # Combine to get full path
                full_path = os.path.join(path_value, name)

                # Open the file/folder
                dialog.destroy()
                self.open_file_from_path(full_path)

        results_tree.bind("<Double-1>", on_result_double_click)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Open",
                   command=lambda: on_result_double_click(None)).pack(side="left", padx=5)

        ttk.Button(button_frame, text="Close",
                   command=dialog.destroy).pack(side="right", padx=5)

        # Update status bar
        self.status_var.set(f"Found {len(files)} files with tag '{tag}'")

    def summarize_selected_file(self):
        """Generate an AI summary of the selected file"""
        if not self.search_engine.openai_client:
            messagebox.showerror("Error", "OpenAI API is not configured. Please check your API key.")
            return

        selected = self.get_selected_items()

        if not selected or len(selected) != 1:
            messagebox.showinfo("Info", "Please select a single file to summarize.")
            return

        file_path = selected[0]

        if os.path.isdir(file_path):
            messagebox.showinfo("Info", "Please select a file, not a directory.")
            return

        # Show a loading dialog
        loading_dialog = tk.Toplevel(self.root)
        loading_dialog.title("Generating Summary")
        loading_dialog.geometry("300x100")
        loading_dialog.transient(self.root)
        loading_dialog.grab_set()

        ttk.Label(loading_dialog, text="Generating file summary...",
                  font=("Arial", 10)).pack(pady=(20, 10))

        status_var = tk.StringVar(value="Please wait...")
        ttk.Label(loading_dialog, textvariable=status_var).pack(pady=5)

        # Update the dialog immediately
        loading_dialog.update_idletasks()

        # Generate the summary
        def do_generate_summary():
            try:
                summary = self.search_engine.ai_summarize_file(file_path)
                loading_dialog.destroy()

                # Show the summary
                summary_dialog = tk.Toplevel(self.root)
                summary_dialog.title(f"Summary: {os.path.basename(file_path)}")
                summary_dialog.geometry("600x400")
                summary_dialog.transient(self.root)

                ttk.Label(summary_dialog, text=f"Summary of {os.path.basename(file_path)}",
                          font=("Arial", 12, "bold")).pack(pady=(10, 5), padx=10, anchor="w")

                # Create a text widget for the summary
                text_frame = ttk.Frame(summary_dialog)
                text_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

                text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 10))
                scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)

                scrollbar.pack(side="right", fill="y")
                text_widget.pack(side="left", fill="both", expand=True)

                # Insert the summary
                text_widget.insert("1.0", summary)
                text_widget.config(state="disabled")

                # Add buttons
                button_frame = ttk.Frame(summary_dialog)
                button_frame.pack(fill="x", padx=10, pady=10)

                def save_summary():
                    save_path = filedialog.asksaveasfilename(
                        defaultextension=".txt",
                        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                        title="Save Summary"
                    )
                    if save_path:
                        with open(save_path, 'w', encoding='utf-8') as f:
                            f.write(summary)
                        messagebox.showinfo("Success", f"Summary saved to {save_path}")

                ttk.Button(button_frame, text="Save Summary",
                           command=save_summary).pack(side="left", padx=5)

                ttk.Button(button_frame, text="Close",
                           command=summary_dialog.destroy).pack(side="right", padx=5)

            except Exception as e:
                loading_dialog.destroy()
                messagebox.showerror("Error", f"Could not generate summary: {e}")

        # Run in a separate thread
        threading.Thread(target=do_generate_summary, daemon=True).start()

    # ------------------------------------BY GPT CAN'T UNDERSTAND THE USE
    def find_similar_files(self):
        """Find files similar to the selected file"""
        selected = self.get_selected_items()

        if not selected or len(selected) != 1:
            messagebox.showinfo("Info", "Please select a single file to find similar files.")
            return

        file_path = selected[0]

        if os.path.isdir(file_path):
            messagebox.showinfo("Info", "Please select a file, not a directory.")
            return

        # Show a loading indicator
        self.status_var.set(f"Finding files similar to {os.path.basename(file_path)}...")
        self.root.update_idletasks()

        # Find similar files
        similar_files = self.search_engine.search_similar_files(file_path)

        if not similar_files:
            self.status_var.set("No similar files found")
            messagebox.showinfo("Similar Files", "No similar files were found.")
            return

        # Create a dialog to show results
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Files Similar to: {os.path.basename(file_path)}")
        dialog.geometry("600x400")
        dialog.transient(self.root)

        # Create a frame for the results
        ttk.Label(dialog, text=f"Files similar to {os.path.basename(file_path)}:",
                  font=("Arial", 12)).pack(pady=(10, 5), padx=10, anchor="w")

        # Create a treeview for results
        results_frame = ttk.Frame(dialog)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side="right", fill="y")

        # Create the treeview
        results_tree = ttk.Treeview(
            results_frame,
            columns=("path", "type"),
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )

        # Configure scrollbar
        scrollbar.config(command=results_tree.yview)

        # Configure columns
        results_tree.heading("#0", text="Name")
        results_tree.heading("path", text="Path")
        results_tree.heading("type", text="Type")

        # Set column widths
        results_tree.column("#0", width=150, minwidth=100)
        results_tree.column("path", width=350, minwidth=100)
        results_tree.column("type", width=80, minwidth=50)

        # Add results to treeview
        for path in similar_files:
            try:
                if os.path.exists(path) and path != file_path:
                    name = os.path.basename(path)
                    dir_path = os.path.dirname(path)

                    # Determine type
                    if os.path.isdir(path):
                        type_str = "Folder"
                    else:
                        # Get file extension
                        _, ext = os.path.splitext(name)
                        type_str = ext[1:].upper() if ext else "File"

                    # Add to treeview
                    results_tree.insert(
                        "", "end", text=name,
                        values=(dir_path, type_str),
                        tags=("folder" if os.path.isdir(path) else "file")
                    )
            except:
                # Skip items that can't be accessed
                continue

        # Pack the treeview
        results_tree.pack(side="left", fill="both", expand=True)

        # ----------------------------------------

        # Handle double-click on result
        def on_result_double_click(event):
            selection = results_tree.selection()
            if selection:
                item = selection[0]
                name = results_tree.item(item, "text")
                path_value = results_tree.item(item, "values")[0]

                # Combine to get full path
                full_path = os.path.join(path_value, name)

                # Open the file/folder
                dialog.destroy()
                self.open_file_from_path(full_path)

        results_tree.bind("<Double-1>", on_result_double_click)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Open",
                   command=lambda: on_result_double_click(None)).pack(side="left", padx=5)

        ttk.Button(button_frame, text="Close",
                   command=dialog.destroy).pack(side="right", padx=5)

        # Update status bar
        self.status_var.set(f"Found {len(results_tree.get_children())} similar files")

    def check_file_health(self):
        """Check health of selected files"""
        selected = self.get_selected_items()

        if not selected:
            messagebox.showinfo("Info", "Please select at least one file to check.")
            return

        # Create a dialog to show results
        dialog = tk.Toplevel(self.root)
        dialog.title("File Health Check")
        dialog.geometry("700x500")
        dialog.transient(self.root)

        # Create a frame for the results
        ttk.Label(dialog, text="File Health Report",
                  font=("Arial", 12, "bold")).pack(pady=(10, 5), padx=10, anchor="w")

        # Create a treeview for results
        results_frame = ttk.Frame(dialog)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side="right", fill="y")

        # Create the treeview
        results_tree = ttk.Treeview(
            results_frame,
            columns=("path", "status", "issues"),
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )

        # Configure scrollbar
        scrollbar.config(command=results_tree.yview)

        # Configure columns
        results_tree.heading("#0", text="Name")
        results_tree.heading("path", text="Path")
        results_tree.heading("status", text="Status")
        results_tree.heading("issues", text="Issues")

        # Set column widths
        results_tree.column("#0", width=150, minwidth=100)
        results_tree.column("path", width=250, minwidth=100)
        results_tree.column("status", width=80, minwidth=50)
        results_tree.column("issues", width=200, minwidth=100)

        # Add results to treeview
        for path in selected:
            try:
                if os.path.exists(path):
                    name = os.path.basename(path)
                    dir_path = os.path.dirname(path)

                    # Check file health
                    integrity = self.health_monitor.check_file_integrity(path)
                    problems = self.health_monitor.check_for_problems(path)

                    # Determine status
                    if problems:
                        status = "Issues Found"
                        issues = ", ".join(problems)
                    elif integrity.get('changed', False):
                        status = "Changed"
                        issues = "File has been modified since last check"
                    else:
                        status = "Healthy"
                        issues = ""

                    # Add to treeview with appropriate tag
                    tag = "healthy" if status == "Healthy" else "issues"
                    results_tree.insert(
                        "", "end", text=name,
                        values=(dir_path, status, issues),
                        tags=(tag,)
                    )
            except Exception as e:
                # Add error item
                results_tree.insert(
                    "", "end", text=os.path.basename(path),
                    values=(os.path.dirname(path), "Error", str(e)),
                    tags=("error",)
                )

        # Configure tags
        results_tree.tag_configure("healthy", foreground="green")
        results_tree.tag_configure("issues", foreground="orange")
        results_tree.tag_configure("error", foreground="red")

        # Pack the treeview
        results_tree.pack(side="left", fill="both", expand=True)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Close",
                   command=dialog.destroy).pack(side="right", padx=5)

        # Update status bar
        self.status_var.set(f"Checked health of {len(selected)} files")

    def start_voice_assistant(self):
        """Start the voice assistant"""
        # Initialize the voice assistant if it hasn't been already
        if not self.recognizer:
            messagebox.showerror("Error", "Speech recognition not available.")
            return
        self._show_listening_indicator()
        self.speak("Voice assistant started. Awaiting your command.")
        self.listening = True
        threading.Thread(target=self._listen_for_commands, daemon=True).start()

    def stop_voice_assistant(self):
        self.listening = False
        self.speak("Voice assistant stopped.")

    def _listen_for_commands(self):
        while self.listening:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = self.recognizer.listen(source, phrase_time_limit=5)
                try:
                    text = self.recognizer.recognize_google(audio)
                    self.process_command(text.lower())
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError:
                    self.speak("Voice service unavailable.")
            except Exception as e:
                print(f"Voice command error: {e}")
                self.listening = False

    def process_command(self, text):
        self.current_command = text
        if "open" in text or "go to" in text:
            self._handle_navigation(text)
        elif "back" in text:
            self.explorer.go_back()
        elif "up" in text:
            self.explorer.go_up()
        elif "create file" in text:
            name = text.split("file")[-1].strip()
            self.explorer.create_file(name=name)
        elif "create folder" in text:
            name = text.split("folder")[-1].strip()
            self.explorer.make_dir(name=name)
        elif "delete" in text:
            self.explorer.delete_file()
        elif "rename to" in text:
            name = text.split("to")[-1].strip()
            self.explorer.rename_file(new_name=name)
        elif "search" in text:
            keyword = text.split("search")[-1].strip()
            self.explorer.search_var.set(keyword)
            self.explorer.search_files()
        elif "stop" in text or "exit" in text:
            self.stop_voice_assistant()
        else:
            self.speak("Command not recognized.")
        self.current_command = None

    def init_voice_engine(self):
        if not PYTTSX3_AVAILABLE:
            return
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
        except Exception as e:
            print(f"Voice engine error: {e}")
            self.engine = None

    def init_speech_recognition(self):
        if not SR_AVAILABLE:
            return
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 4000
            self.recognizer.pause_threshold = 0.8
        except Exception as e:
            print(f"Speech recognition error: {e}")
            self.recognizer = None

    def _handle_navigation(self, text):
        if "downloads" in text:
            target = os.path.join(os.path.expanduser("~"), "Downloads")
        elif "documents" in text:
            target = os.path.join(os.path.expanduser("~"), "Documents")
        elif "desktop" in text:
            target = os.path.join(os.path.expanduser("~"), "Desktop")
        elif "parvati" in text:
            target = os.path.join(os.path.expanduser("C:/Users/Parvati/OneDrive/Desktop/PARVATI"), "PARVATI")
        else:
            self.speak("Navigation path not recognized.")
            return
        if os.path.exists(target):
            self.explorer.current_directory = target
            self.explorer.load_files()
            self.speak("Opened " + os.path.basename(target))

    def speak(self, text):
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"Speech error: {e}")

    def _show_listening_indicator(self):
        try:
            indicator = tk.Toplevel(self.explorer.root)
            indicator.title("Listening")
            indicator.geometry("300x100")
            indicator.transient(self.explorer.root)
            ttk.Label(indicator, text="🎤 Listening...", font=("Arial", 14)).pack(pady=10)
            ttk.Button(indicator, text="Stop", command=self.stop_voice_assistant).pack(pady=10)

            def check_listening():
                if not self.listening:
                    indicator.destroy()
                else:
                    indicator.after(500, check_listening)

            check_listening()
        except Exception as e:
            print(f"UI error: {e}")

    def sort_files(self, sort_by):
        """Sort files in the treeview"""
        items = [(self.files_tree.item(item, "values"), item) for item in self.files_tree.get_children()]

        if sort_by == "name":
            # Sort by name (case-insensitive)
            items.sort(key=lambda x: x[0][0].lower())
        elif sort_by == "type":
            # Sort by type, then name
            items.sort(key=lambda x: (x[0][1], x[0][0].lower()))
        elif sort_by == "size":
            # Sort by size (empty string for folders first)
            def get_size_for_sort(item):
                size_str = item[0][2]
                if not size_str:  # Folders come first
                    return -1

                # Extract numeric part
                try:
                    size = float(''.join(c for c in size_str.split()[0] if c.isdigit() or c == '.'))

                    # Adjust based on unit
                    if "KB" in size_str:
                        size *= 1024
                    elif "MB" in size_str:
                        size *= 1024 * 1024
                    elif "GB" in size_str:
                        size *= 1024 * 1024 * 1024

                    return size
                except:
                    return 0

            items.sort(key=get_size_for_sort)

        elif sort_by == "date":
            # Sort by date
            def parse_date(date_str):
                if "Today" in date_str:
                    return 10  # Very recent
                elif any(day in date_str for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
                    return 9  # This week
                else:
                    # Try to extract year, month, day
                    parts = date_str.split()
                    if len(parts) >= 1 and "-" in parts[0]:
                        date_parts = parts[0].split("-")
                        if len(date_parts) == 3:
                            try:
                                # Format: YYYY-MM-DD
                                year, month, day = map(int, date_parts)
                                return year * 10000 + month * 100 + day
                            except:
                                pass
                return 0

            items.sort(key=lambda x: parse_date(x[0][3]), reverse=True)

        # Rearrange items in the treeview
        for index, (_, item_id) in enumerate(items):
            self.files_tree.move(item_id, "", index)

    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Keyboard Shortcuts")
        dialog.geometry("400x500")
        dialog.transient(self.root)

        # Create a frame for the content
        content_frame = ttk.Frame(dialog, padding=10)
        content_frame.pack(fill="both", expand=True)

        # Heading
        ttk.Label(content_frame, text="Keyboard Shortcuts",
                  font=("Arial", 14, "bold")).pack(pady=(0, 10))

        # Create a text widget for the shortcuts
        text = tk.Text(content_frame, wrap="word", height=20, width=50)
        text.pack(fill="both", expand=True)

        # Add shortcuts
        shortcuts = """
File Operations:
Ctrl+N        Create new file
Ctrl+Shift+N  Create new folder
Delete        Delete selected item(s)
F2            Rename selected item

Navigation:
Alt+Left      Go back
Alt+Right     Go forward
Alt+Up        Go up (parent directory)
F5            Refresh

Editing:
Ctrl+X        Cut
Ctrl+C        Copy
Ctrl+V        Paste
Ctrl+A        Select all

Search:
Ctrl+F        Focus search box

Tools:
Ctrl+Q        Generate QR code
Ctrl+Shift+Q  Scan QR code
F1            Voice commands
        """

        text.insert("1.0", shortcuts)
        text.config(state="disabled")

        # Close button
        ttk.Button(content_frame, text="Close",
                   command=dialog.destroy).pack(pady=10)

    def show_about(self):
        """Show about dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("About Advanced File Explorer")
        dialog.geometry("400x300")
        dialog.transient(self.root)

        # Create a frame for the content
        content_frame = ttk.Frame(dialog, padding=20)
        content_frame.pack(fill="both", expand=True)

        # Heading
        ttk.Label(content_frame, text="Advanced File Explorer",
                  font=("Arial", 16, "bold")).pack(pady=(0, 5))

        ttk.Label(content_frame, text="Version 2.0").pack(pady=(0, 20))

        # Description
        description = """  An AI-enhanced file explorer with advanced features:
                                    • Voice command support
                                    • QR code generation and scanning
                                    • Tagging system
                                    • File health monitoring
                                    • Usage analytics """

        ttk.Label(content_frame, text=description, justify="left").pack(pady=10)

        # Close button
        ttk.Button(content_frame, text="Close",
                   command=dialog.destroy).pack(pady=10)

    def quit_app(self):
        """Quit the application"""
        self.root.quit()
        self.root.destroy()


# ===============================================================================
# Check Dependencies and Initialize Application
# ===============================================================================

def check_dependencies():
    """Check if all required packages are installed"""
    missing = []

    try:
        import openai
        print("OpenAI module available")
    except ImportError:
        missing.append("openai")

    try:
        import qrcode
        print("QR code module available")
    except ImportError:
        missing.append("qrcode")

    try:
        import cv2
        print("OpenCV module available")
    except ImportError:
        missing.append("opencv-python")

    try:
        import pyttsx3
        print("pyttsx3 module available")
    except ImportError:
        missing.append("pyttsx3")

    try:
        import speech_recognition
        print("SpeechRecognition module available")
    except ImportError:
        missing.append("SpeechRecognition")

    # Recommend installing missing packages
    if missing:
        print("\nMissing packages: " + ", ".join(missing))
        print("Run the following command to install them:")
        print(f"pip install {' '.join(missing)}")
    else:
        print("\nAll required packages are installed.")

    return missing


def main():
    """Main entry point for the application"""
    # Check dependencies
    missing = check_dependencies()

    # Create the main window
    root = tk.Tk()
    root.title("Advanced File Explorer")

    # Create and run the application
    app = AdvancedFileExplorer(root)

    # Warning about missing packages
    if missing:
        messagebox.showwarning(
            "Missing Dependencies",
            f"Some features may be limited due to missing packages:\n\n{', '.join(missing)}\n\n"
            f"You can install them using pip."
        )

    # Run the main loop
    root.mainloop()


if __name__ == "__main__":
    main()