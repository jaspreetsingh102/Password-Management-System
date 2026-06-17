import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from cryptography.fernet import Fernet
import hashlib as Hash
import maskpass
from functools import partial
import email_sender
import json
import csv
import os
import threading
import time
import secrets
import string

# Helper Functions (Same as original)
To_Sha512 = lambda Login_Password: Hash.sha512(Login_Password.encode()).hexdigest()
To_Sha256 = lambda Login_Username: Hash.sha256(Login_Username.encode()).hexdigest()
To_Md5 = lambda x: Hash.md5(x.encode()).hexdigest()
To_Filename = lambda Hashed_Username: Hashed_Username + ".txt"
To_Filekey = lambda Hashed_Username: Hashed_Username + ".key"

def calculate_password_strength(password):
    """
    Calculate password strength and return a tuple:
    (strength_label, strength_score, strength_color)
    
    strength_score: 0-100
    strength_label: Weak, Medium, Strong, Very Strong
    strength_color: hex color code
    """
    if not password:
        return ("Enter Password", 0, "#6c757d")
    
    score = 0
    feedback = []
    
    # Length checks
    if len(password) >= 8:
        score += 20
    elif len(password) >= 6:
        score += 10
    
    if len(password) >= 12:
        score += 10
    
    if len(password) >= 16:
        score += 10
    
    # Character type checks
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    if has_upper:
        score += 15
    if has_lower:
        score += 15
    if has_digit:
        score += 10
    if has_special:
        score += 20
    
# Determine strength level
    if score >= 80:
        return ("🔵 Very Strong", score, "#00d9ff")
    elif score >= 60:
        return ("🟢 Strong", score, "#00f5d4")
    elif score >= 40:
        return ("🟡 Medium", score, "#ffc107")
    elif score >= 20:
        return ("🟠 Fair", score, "#ff6b35")
    else:
        return ("🔴 Weak", score, "#e63946")

def get_expiry_status(timestamp_str):
    """
    Calculate expiry status based on timestamp
    Returns: (status_text, status_color, days_old)
    
    Color scheme:
    - 🟢 Green: Fresh (< 30 days)
    - 🟡 Yellow: Warning (30-60 days)  
    - 🟠 Orange: Urgent (60-90 days)
    - 🔴 Red: Expired (> 90 days)
    """
    try:
        if not timestamp_str:
            return ("❓ Unknown", "#6c757d", 0)
        
        timestamp = int(timestamp_str)
        current_time = int(time.time())
        days_old = (current_time - timestamp) // (24 * 60 * 60)
        
        if days_old < 30:
            return (f"🟢 Fresh ({days_old}d)", "#00f5d4", days_old)
        elif days_old < 60:
            return (f"🟡 Warning ({days_old}d)", "#ffc107", days_old)
        elif days_old < 90:
            return (f"🟠 Urgent ({days_old}d)", "#ff6b35", days_old)
        else:
            return (f"🔴 Expired ({days_old}d)", "#e63946", days_old)
    except:
        return ("❓ Unknown", "#6c757d", 0)

class PassmanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Passman - Password Manager")
        self.root.state("zoomed")
        self.root.resizable(False, False)
        
        # Modern color palette
        self.colors = {
            'bg_dark': '#1a1a2e',
            'bg_medium': '#16213e',
            'bg_light': '#0f3460',
            'accent_blue': '#00d9ff',
            'accent_purple': '#9d4edd',
            'accent_green': '#00f5d4',
            'accent_orange': '#ff6b35',
            'accent_red': '#e63946',
            'text_white': '#ffffff',
            'text_gray': '#a0a0a0'
        }
        
        self.root.configure(bg=self.colors['bg_dark'])
        
        # Style configuration with modern colors
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Custom styles
        self.style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'), 
                           foreground=self.colors['accent_blue'], background=self.colors['bg_medium'])
        self.style.configure('Subtitle.TLabel', font=('Segoe UI', 12), 
                           foreground=self.colors['text_gray'], background=self.colors['bg_medium'])
        self.style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), 
                           foreground=self.colors['text_white'], background=self.colors['bg_medium'])
        self.style.configure('Menu.TLabel', font=('Segoe UI', 11), 
                           foreground=self.colors['text_white'], background=self.colors['bg_medium'])
        
        # Loading style removed (no progressbar used)
        
        # Container for frames with card-like background
        self.container = tk.Frame(self.root, bg=self.colors['bg_medium'], 
                                  relief='flat', borderwidth=0)
        self.container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Current state
        self.current_frame = None
        self.username = None
        self.user_email = None  # Store user's email for passkey verification
        # OTP login state
        self.pending_login_user = None
        self.generated_otp = None
        self.otp_timestamp = None
        # Security attempt tracking
        self.system_attempts = 3
        self.login_attempts = 0
        self.login_button = None
        self.filename = None
        self.filekey = None
        self.cipher = None
        
        # Password visibility tracking
        self.password_visible = {}
        
        # Loading animation components
        self.loading_frame = None
        self.loading_label = None
        self.loading_progress = None
        self.spinner_state = 0

        # Auto-detect if setup is needed to make it easier to run
        if not os.path.exists("System_Password.txt"):
            self.show_system_setup()
        else:
            self.show_system_menu()
    
    def clear_frame(self):
        """Clear all widgets from the container"""
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def create_modern_button(self, parent, text, command, bg='#00d9ff', fg='#1a1a2e', 
                            hover_color=None, width=25):
        """Create a modern styled button"""
        if hover_color is None:
            hover_color = bg
            
        btn = tk.Button(parent, text=text, font=('Segoe UI', 11, 'bold'),
                       bg=bg, fg=fg, relief='flat', bd=0,
                       padx=20, pady=12, cursor='hand2',width=20,
                       activebackground=hover_color, activeforeground=fg,
                       command=command)
        
        # Hover effects
        def on_enter(e):
            btn.config(bg=hover_color)
        def on_leave(e):
            btn.config(bg=bg)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    def create_modern_entry(self, parent, show=None, width=30):
        entry_frame = tk.Frame(parent, bg=self.colors['accent_blue'], bd=1)
        entry_frame.pack(pady=5)

        entry = tk.Entry(entry_frame,
                        font=('Segoe UI', 11),
                        bg=self.colors['bg_light'],
                        fg=self.colors['text_white'],
                        insertbackground=self.colors['accent_blue'],
                        relief='flat',
                        width=width,
                        show=show)

        entry.pack(padx=10, pady=8)

        # force focus on click
        entry.bind("<Button-1>", lambda e: entry.focus_set())

        return entry, entry_frame
    
    def create_card_frame(self, parent, bg=None):
        """Create a card-like frame"""
        if bg is None:
            bg = self.colors['bg_medium']
        card = tk.Frame(parent, bg=bg, relief='flat', bd=0)
        return card
    
    def show_loading(self, msg="Generating secure OTP..."):
        """Show centered loading animation"""
        # Destroy existing loading frame if any
        if self.loading_frame:
            self.loading_frame.destroy()
        
        # Create new loading frame (centered)
        self.loading_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        self.loading_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Loading label with spinner dots
        self.loading_label = tk.Label(self.loading_frame, text=msg, 
                                    font=('Segoe UI', 14, 'bold'),
                                    bg=self.colors['bg_medium'], fg=self.colors['accent_blue'])
        self.loading_label.pack(pady=10)
        
        # Start spinner animation
        self.animate_spinner()
    
    def hide_loading(self):
        """Hide loading animation and re-enable UI"""
        if self.loading_frame:
            self.loading_frame.destroy()
            self.loading_frame = None
        
        # No progressbar to clean up
        
        # Stop spinner
        if self._spinner_id:
            self.root.after_cancel(self._spinner_id)
            self._spinner_id = None
        self.spinner_state = 0
    
    def animate_spinner(self):
        """Animate loading dots: ..."""
        dots = [' ', '..', '...', '....']
        self.loading_label.config(text=f"Generating secure OTP{dots[self.spinner_state % 4]}")
        self.spinner_state += 1
        self._spinner_id = self.root.after(500, self.animate_spinner)
    
    def send_otp_threaded(self, to_email, on_success, on_error=None):
        """Threaded OTP sender with loading animation"""
        def thread_target():
            try:
                self.generated_otp = email_sender.generate_verification_code()
                self.otp_timestamp = int(time.time())
                success = email_sender.send_verification_code(
                    to_email=to_email, 
                    code=self.generated_otp
                )
                # Schedule UI callback on main thread
                self.root.after(0, lambda: self._otp_complete(success, on_success, on_error))
            except Exception as e:
                self.root.after(0, lambda: self._otp_error(str(e), on_error))
        
        # Show loading
        self.show_loading()
        
        # Start thread
        thread = threading.Thread(target=thread_target, daemon=True)
        thread.start()
    
    def _otp_complete(self, success, on_success, on_error):
        """OTP send complete callback"""
        self.hide_loading()
        if success:
            if callable(on_success):
                on_success()
        else:
            messagebox.showinfo("📧 Demo Mode", f"OTP: {self.generated_otp} (email not sent)")
            if callable(on_success):
                on_success()
    
    def _otp_error(self, error_msg, on_error):
        """OTP send error callback"""
        self.hide_loading()
        messagebox.showerror("❌ Network Error", f"Failed to send OTP: {error_msg}")
        if callable(on_error):
            on_error()

    
    # ==================== SYSTEM MENU ====================
    
    def show_system_setup(self):
        """Initial setup screen if no system password exists"""
        self.clear_frame()
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        tk.Label(header, text="🛡️", font=('Segoe UI', 50), 
                 bg=self.colors['bg_medium'], fg=self.colors['accent_green']).pack()
        tk.Label(self.container, text="Welcome to Passman", 
                 font=('Segoe UI', 24, 'bold'), bg=self.colors['bg_medium'], 
                 fg=self.colors['accent_blue']).pack()
        tk.Label(self.container, text="Please set a Master System Password to begin.", 
                 font=('Segoe UI', 12), bg=self.colors['bg_medium'], 
                 fg=self.colors['text_gray']).pack(pady=10)

        input_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        input_frame.pack(pady=20)
        
        pass_entry, _ = self.create_modern_entry(input_frame, show="*")
        
        def perform_setup():
            p = pass_entry.get()
            if len(p) < 4:
                messagebox.showerror("❌ Error", "Password must be at least 4 characters!")
                return
            with open("System_Password.txt", 'w') as f:
                f.write(To_Md5(p))
            messagebox.showinfo("✅ Success", "System Password Set! Please log in.")
            self.show_system_menu()

        self.create_modern_button(self.container, "🚀 Finish Setup", perform_setup, 
                                 bg='#00f5d4').pack(pady=20)

    def show_system_menu(self):
        """Show the System Menu"""
        self.clear_frame()
        
        # Decorative header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(0, 20))
        
        # Shield icon
        icon_label = tk.Label(header, text="🛡️", font=('Segoe UI', 50), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_blue'])
        icon_label.pack(pady=(20, 10))
        
        # Title
        title = tk.Label(self.container, text="PASSMAN", 
                        font=('Segoe UI', 28, 'bold'), 
                        bg=self.colors['bg_medium'], fg=self.colors['accent_blue'])
        title.pack(pady=(0, 5))
        
        subtitle = tk.Label(self.container, text="Secure Password Manager", 
                          font=('Segoe UI', 12), 
                          bg=self.colors['bg_medium'], fg=self.colors['text_gray'])
        subtitle.pack(pady=(0, 25))
        
        # Menu buttons container
        menu_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        menu_frame.pack(pady=10)
        
        # Modern styled buttons with icons
        btn_enter = self.create_modern_button(
            menu_frame, "🔐  Enter System Password",
            self.show_system_password_entry,
            bg='#00d9ff', hover_color='#00b8d9'
        )
        btn_enter.pack(pady=8, ipadx=40)
        
        btn_reset = self.create_modern_button(
            menu_frame, "🔄  Reset System Password",
            self.show_reset_password,
            bg='#9d4edd', hover_color='#7b2cbf'
        )
        btn_reset.pack(pady=8, ipadx=40)

        
        btn_passman = self.create_modern_button(
            menu_frame, "🛡️  About Passman",
            self.show_about_passman,
            bg='#ff6b35', hover_color='#e55a2b'
        )
        btn_passman.pack(pady=8, ipadx=40)
        
        btn_exit = self.create_modern_button(
            menu_frame, "🚪  Exit",
            self.exit_app,
            bg='#e63946', hover_color='#c1121f'
        )
        btn_exit.pack(pady=8, ipadx=40)
    
    def show_system_password_entry(self):
        """Show system password entry screen"""
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_system_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text="🔐", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_blue'])
        icon_label.pack(pady=(0, 10))
        
        title = tk.Label(self.container, text="System Password", 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 30))
        
        # Input frame
        input_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        input_frame.pack(pady=20)
        
        label = tk.Label(input_frame, text="Enter System Password:", 
                       font=('Segoe UI', 12), bg=self.colors['bg_medium'], 
                       fg=self.colors['text_white'])
        label.pack(pady=(0, 10))
        
        self.system_password_entry, entry_frame = self.create_modern_entry(input_frame, show="*")
        
        # self.system_attempts handled in verify_system_password
        
        # Button frame
        btn_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=30)
        
        submit_btn = self.create_modern_button(btn_frame, "✓  Verify", 
                                               self.verify_system_password,
                                               bg='#00f5d4', hover_color='#00c4a7')
        submit_btn.pack(side='left', padx=10)
        
        back_btn = self.create_modern_button(btn_frame, "←  Back", 
                                             self.show_system_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn.pack(side='left', padx=10)
        
        self.system_password_entry.bind('<Return>', lambda e: self.verify_system_password())
        self.root.after(200, lambda: self.system_password_entry.focus_set())
    
    def verify_system_password(self):
        """Verify the system password"""
        password = self.system_password_entry.get()
        
        try:
            with open("System_Password.txt", 'r') as f:
                existing_password = f.read().strip()
        except FileNotFoundError:
            existing_password = ""
        
        hashed_password = To_Md5(password)
        
        if hashed_password == existing_password:
            messagebox.showinfo("✅ Success", "System Password Verified Successfully!")
            self.show_user_menu()
        else:
            self.system_attempts -= 1
            if self.system_attempts > 0:
                messagebox.showerror("❌ Error", 
                    f"Incorrect Password!\nYou have {self.system_attempts} attempt(s) left.")
                self.system_password_entry.delete(0, 'end')
            else:
                messagebox.showerror("❌ Error", "No attempts left. Exiting...")
                self.exit_app()
    
    def show_reset_password(self):
        """Show reset password screen"""
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_system_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text="🔐", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_purple'])
        icon_label.pack(pady=(0, 10))
        
        title = tk.Label(self.container, text="Reset Password", 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 30))
        
        input_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Enter New Password:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(0, 5))
        new_pass_entry, _ = self.create_modern_entry(input_frame, show="*")
        
        tk.Label(input_frame, text="Confirm New Password:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        confirm_pass_entry, _ = self.create_modern_entry(input_frame, show="*")
        
        def save_new_password():
            new_pass = new_pass_entry.get()
            confirm_pass = confirm_pass_entry.get()
            
            if not new_pass or not confirm_pass:
                messagebox.showerror("❌ Error", "Please fill in all fields!")
                return
            
            if new_pass == confirm_pass:
                hashed_new = To_Md5(new_pass)
                with open("System_Password.txt", 'w') as f:
                    f.write(hashed_new)
                messagebox.showinfo("✅ Success", "System Password Reset Successfully!")
                self.show_system_menu()
            else:
                messagebox.showerror("❌ Error", "Passwords do not match!")
        
        btn_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=30)
        
        save_btn = self.create_modern_button(btn_frame, "💾  Save", 
                                            save_new_password,
                                            bg='#9d4edd', hover_color='#7b2cbf')
        save_btn.pack(side='left', padx=10)
        
        back_btn = self.create_modern_button(btn_frame, "←  Back", 
                                             self.show_system_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn.pack(side='left', padx=10)
    
    
    def show_about_passman(self):
        """Show about Passman information"""
        about_text = (
            "🛡️ Passman - Your Ultimate Digital Vault\n\n"
            "Passman is a comprehensive password management system designed to protect your digital identity from unauthorized access through multi-layered security protocols.\n\n"
            "🚀 Key Features:\n"
            "• AES-Powered Encryption: Uses Fernet symmetric encryption to ensure your site credentials are never stored in plain text.\n"
            "• Email-Based MFA: Secure verification using OTP (One-Time Passwords) sent via the integrated email module.\n"
            "• Robust Hashing: Implements SHA-512 for secure user authentication and SHA-256 for username protection.\n"
            "• Intelligence Tools: Includes real-time password strength analysis, age tracking, and a secure random password generator.\n"
            "• Data Portability: Easily export or import your vault using industry-standard CSV and JSON formats.\n\n"
            "Passman leverages Python's Cryptography, Hashlib, and smtplib libraries to provide a secure and organized environment for your sensitive data."
        )
        messagebox.showinfo("🛡️ About Passman", about_text)
    
    # ==================== USER MENU ====================
    
    def show_user_menu(self):
        """Show the User Menu"""
        self.clear_frame()
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(20, 10))
        
        icon_label = tk.Label(header, text="👤", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
        icon_label.pack(pady=(20, 10))
        
        title = tk.Label(self.container, text="User Menu", 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 30))
        
        menu_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        menu_frame.pack(pady=10)
        
        btn_create = self.create_modern_button(
            menu_frame, "✨  Create Account",
            lambda: self.show_user_credentials("Create"),
            bg='#00f5d4', hover_color='#00c4a7'
        )
        btn_create.pack(pady=8, ipadx=50)
        
        btn_login = self.create_modern_button(
            menu_frame, self.get_login_button_text(),
            lambda: self.show_user_credentials("Login") if self.login_attempts < 3 else None,
            bg=self.get_login_button_color()[0], hover_color=self.get_login_button_color()[1]
        )
        btn_login.pack(pady=8, ipadx=50)
        
        btn_update = self.create_modern_button(
            menu_frame, "✏️  Update Account",
            lambda: self.show_user_credentials("Update"),
            bg='#ff6b35', hover_color='#e55a2b'
        )
        btn_update.pack(pady=8, ipadx=50)
        
        btn_forgot = self.create_modern_button(
            menu_frame, "🔑  Forgot Password",
            self.show_forgot_password,
            bg='#9d4edd', hover_color='#7b2cbf'
        )
        btn_forgot.pack(pady=8, ipadx=50)
        
        btn_back = self.create_modern_button(
            menu_frame, "←  Back to System",
            self.show_system_menu,
            bg='#6c757d', hover_color='#5a6268'
        )
        btn_back.pack(pady=8, ipadx=50)
        
        btn_exit = self.create_modern_button(
            menu_frame, "🚪  Exit",
            self.exit_app,
            bg='#e63946', hover_color='#c1121f'
        )
        btn_exit.pack(pady=8, ipadx=50)

    def get_login_button_text(self):
        """Get dynamic text for login button based on attempts"""
        if self.login_attempts < 3:
            return f"🔓  Login ({self.login_attempts}/3)"
        else:
            return "🔒 Locked (3/3)"

    def get_login_button_color(self):
        """Get dynamic colors for login button based on attempts"""
        if self.login_attempts < 3:
            return ('#00d9ff', '#00b8d9')  # Normal blue
        else:
            return ('#6c757d', '#5a6268')  # Disabled gray
    
    def show_user_credentials(self, action):
        """Show username/password entry for user operations"""
        self.clear_frame()
        
        icons = {"Create": "✨", "Login": "🔓", "Update": "✏️"}
        colors = {"Create": "#00f5d4", "Login": "#00d9ff", "Update": "#ff6b35"}
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_user_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text=icons[action], font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=colors[action])
        icon_label.pack(pady=(0, 10))
        
        title_text = {"Create": "Create Account", 
                     "Login": "Login", 
                     "Update": "Verify & Update Account"}
        
        title = tk.Label(self.container, text=title_text[action], 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 30))
        
        input_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Username:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(0, 5))
        username_entry, _ = self.create_modern_entry(input_frame)
        
        # Add Gmail field for Create action
        if action == "Create":
            tk.Label(input_frame, text="Gmail:", font=('Segoe UI', 11),
                    bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(15, 5))
            gmail_entry, _ = self.create_modern_entry(input_frame)
        
        tk.Label(input_frame, text="Password:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(15, 5))
        password_entry, _ = self.create_modern_entry(input_frame, show="*")
        
        
        def submit_credentials():
            username = username_entry.get()
            password = password_entry.get()
            
            if action == "Create":
                gmail = gmail_entry.get()
                if not username or not gmail or not password:
                    messagebox.showerror("❌ Error", "Please fill in all fields!")
                    return
            else:
                if not username or not password:
                    messagebox.showerror("❌ Error", "Please fill in all fields!")
                    return
            
            hashed_username = To_Sha256(username)
            hashed_password = To_Sha512(password)
            
            if action == "Create":
                self.create_user(hashed_username, hashed_password, username, gmail)
            elif action == "Login":
                self.login_user(hashed_username, hashed_password, username)
            elif action == "Update":
                self.verify_and_show_update_popup(hashed_username, hashed_password, username)
        
        btn_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=30)
        
        submit_btn = self.create_modern_button(btn_frame, f"✓  {title_text[action]}", 
                                               submit_credentials,
                                               bg=colors[action], hover_color=colors[action])
        submit_btn.pack(side='left', padx=10)
        
        back_btn = self.create_modern_button(btn_frame, "←  Back", 
                                             self.show_user_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn.pack(side='left', padx=10)
    
    def create_user(self, hashed_username, hashed_password, username, gmail):
        """Create a new user account"""

        # Check if user already exists
        try:
            with open("Users.txt", 'r') as f:
                for line in f.readlines():
                    line = line.rstrip()

                    parts = line.split("|")

                    # Support old records with 2 fields
                    if len(parts) >= 2:
                        existing_user = parts[0]

                        if existing_user == hashed_username:
                            messagebox.showinfo("ℹ️ Info", "Username Found! Logging in...")
                            self.login_user(hashed_username, hashed_password, username)
                            return

        except FileNotFoundError:
            pass

        # Password confirmation window
        confirm_dialog = tk.Toplevel(self.root)
        confirm_dialog.title("Confirm Password")
        confirm_dialog.geometry("350x250")
        confirm_dialog.configure(bg=self.colors['bg_medium'])
        confirm_dialog.transient(self.root)

        tk.Label(confirm_dialog,
                text="🔐 Confirm Your Password",
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['bg_medium'],
                fg=self.colors['text_white']).pack(pady=20)

        confirm_entry = tk.Entry(confirm_dialog,
                                font=('Segoe UI', 11),
                                show="*",
                                bg=self.colors['bg_light'],
                                fg=self.colors['text_white'],
                                relief='flat')
        confirm_entry.pack(pady=10)

        def confirm():
            confirm_password = confirm_entry.get()

            # Hash password for verification
            hashed_confirm = To_Sha512(confirm_password)

            if hashed_confirm == hashed_password:
                # Save user data with gmail
                with open("Users.txt", 'a') as f:
                    f.write(hashed_username + "|" + username + "|" + gmail + "|" + hashed_password + "\n")

                # Create user vault file
                filename = To_Filename(hashed_username)
                open(filename, 'a').close()

                # Create encryption key
                filekey = To_Filekey(hashed_username)
                key = Fernet.generate_key()

                with open(filekey, 'wb') as f:
                    f.write(key)

                confirm_dialog.destroy()

                messagebox.showinfo("✅ Success", "Passman Account Created Successfully!")

                self.show_user_menu()

            else:
                messagebox.showerror("❌ Error", "Passwords do not match!")

        confirm_btn = tk.Button(confirm_dialog, text="✓ Confirm", command=confirm,
                               bg='#00f5d4', fg='#1a1a2e', relief='flat',
                               font=('Segoe UI', 11, 'bold'))
        confirm_btn.pack(pady=10)

        back_btn = tk.Button(confirm_dialog, text="← Back", command=confirm_dialog.destroy,
                             bg='#6c757d', fg='white', relief='flat',
                             font=('Segoe UI', 11, 'bold'))

        confirm_entry.bind('<Return>', lambda e: confirm())

    def login_user(self, hashed_username, hashed_password, username):
        '''Login user using Username OR Gmail - with OTP verification'''

        try:
            with open("Users.txt", 'r') as f:
                for line in f.readlines():
                    line = line.rstrip()

                    parts = line.split("|")
                    existing_user = parts[0]

                    # New format
                    if len(parts) >= 4:
                        stored_username = parts[1]
                        existing_email = parts[2]
                        existing_pass = parts[3]

                    # Old format
                    else:
                        existing_email = parts[1] if len(parts) > 1 else ""
                        existing_pass = parts[-1]
                        stored_username = existing_email.split("@")[0] if existing_email else username

                    # Check username OR email
                    if existing_user == hashed_username or existing_email == username:

                        if existing_pass == hashed_password:

                            # Password correct - store pending user data and send OTP
                            self.pending_login_user = {
                                'hashed_username': existing_user,
                                'username': stored_username,
                                'email': existing_email
                            }
                            self.generated_otp = email_sender.generate_verification_code()
                            self.otp_timestamp = int(time.time())
                            
                            # Send OTP threaded with loading animation
                            self.send_otp_threaded(
                                to_email=existing_email,
                                on_success=lambda: self.show_otp_login_verify()
                            )
                            return

                        else:
                            self.login_attempts += 1
                            if self.login_attempts >= 3:
                                alert_msg = f"🚨 SECURITY ALERT: 3 failed login attempts for '{username}'!"
                                try:
                                    email_sender.send_email(existing_email, "Passman Login Alert", alert_msg)
                                except:
                                    pass
                                self.login_attempts = 0
                                messagebox.showerror("❌ Error", "Incorrect Password! Account temporarily locked.")
                                self.show_user_menu()
                                return
                            else:
                                messagebox.showerror("❌ Error", f"Incorrect Password! Attempts left: {3-self.login_attempts}")
                            # Stay on login screen for attempts 1-2
                            return

            messagebox.showerror("❌ Error", "Username or Gmail Not Found!")
            self.show_user_menu()

        except FileNotFoundError:
            messagebox.showerror("❌ Error", "No users found!")
            self.show_user_menu()
    
    def show_otp_login_verify(self):
        '''Show OTP verification screen after password confirmation'''
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_user_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text="🔐", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
        icon_label.pack(pady=(0, 10))
        
        title = tk.Label(self.container, text="Verify OTP", 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 10))
        
        # OTP Info + Timer frame
        otp_info_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        otp_info_frame.pack(pady=(0, 15))
        
        info_label = tk.Label(otp_info_frame, text=f"📧 OTP sent to: {self.pending_login_user['email']}", 
                            font=('Segoe UI', 12),
                            bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
        info_label.pack()
        
        input_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="🔑 Enter 6-digit OTP:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(0, 10))
        otp_entry, _ = self.create_modern_entry(input_frame, width=20)
        
        def verify_otp():
            entered_otp = otp_entry.get()
            current_time = int(time.time())
            
            # Check expiry (5 minutes = 300 seconds)
            if current_time - self.otp_timestamp > 300:
                messagebox.showerror("❌ Error", "OTP expired! Please try logging in again.")
                self.show_user_menu()
                return
            
            if entered_otp == self.generated_otp:
                # OTP correct - complete login
                user_data = self.pending_login_user
                self.username = user_data['username']
                self.user_email = user_data['email']
                self.filename = To_Filename(user_data['hashed_username'])
                self.filekey = To_Filekey(user_data['hashed_username'])
                
                self.load_user_key()
                self.login_attempts = 0  # Reset login attempts on success
                messagebox.showinfo("✅ Success", "Login Successful!")
                self.show_passman_menu()
            else:
                messagebox.showerror("❌ Error", "Invalid OTP!")
                otp_entry.delete(0, 'end')
        
        btn_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=30)
        
        verify_btn = self.create_modern_button(btn_frame, "✓  Verify OTP", 
                                               verify_otp,
                                               bg='#00f5d4', hover_color='#00c4a7')
        verify_btn.pack(side='left', padx=10)
        
        resend_btn = self.create_modern_button(btn_frame, "🔄  Resend OTP", 
                                               self.login_user,  # Will re-trigger
                                               bg='#9d4edd', hover_color='#7b2cbf')
        resend_btn.pack(side='left', padx=10)
        
        back_btn2 = self.create_modern_button(btn_frame, "←  Back", 
                                              self.show_user_menu,
                                              bg='#6c757d', hover_color='#5a6268')
        back_btn2.pack(side='left', padx=10)
        
        otp_entry.bind('<Return>', lambda e: verify_otp())
        self.root.after(200, lambda: otp_entry.focus_set())

    def verify_otp_login(self, entered_otp):
        '''Verify OTP for login (alternative method if needed)'''
        current_time = int(time.time())
        if current_time - self.otp_timestamp > 300:
            return False, "OTP expired"
        if entered_otp == self.generated_otp:
            return True, "Valid"
        return False, "Invalid OTP"
    
    def load_user_key(self):
        """Load user encryption key"""
        with open(self.filekey, 'rb') as f:
            key = f.read()
        self.cipher = Fernet(key)
    
    def update_user(self, hashed_username, hashed_password):
        """Update user password"""
        try:
            with open("Users.txt", 'r') as f:
                for line in f.readlines():
                    line = line.rstrip()
                    
                    # Handle both old format (2 fields) and new format (3 fields)
                    parts = line.split("|")
                    if len(parts) >= 3:
                        existing_user = parts[0]
                        existing_email = parts[1]
                        existing_pass = parts[2]
                    elif len(parts) == 2:
                        existing_user = parts[0]
                        existing_pass = parts[1]
                        existing_email = ""
                    else:
                        continue
                    
                    if existing_user == hashed_username:
                        if existing_pass == hashed_password:
                            # Show new password dialog
                            update_dialog = tk.Toplevel(self.root)
                            update_dialog.title("Update Password")
                            update_dialog.geometry("350x250")
                            update_dialog.configure(bg=self.colors['bg_medium'])
                            update_dialog.transient(self.root)
                            
                            tk.Label(update_dialog, text="✏️ Enter New Password", 
                                    font=('Segoe UI', 14, 'bold'), bg=self.colors['bg_medium'], 
                                    fg=self.colors['text_white']).pack(pady=15)
                            
                            new_pass_entry = tk.Entry(update_dialog, show="*", font=('Segoe UI', 11),
                                                    bg=self.colors['bg_light'], fg=self.colors['text_white'])
                            new_pass_entry.pack(pady=5)
                            
                            confirm_entry = tk.Entry(update_dialog, show="*", font=('Segoe UI', 11),
                                                    bg=self.colors['bg_light'], fg=self.colors['text_white'])
                            confirm_entry.pack(pady=5)
                            
                            def save_update():
                                new_pass = new_pass_entry.get()
                                confirm_pass = confirm_entry.get()
                                
                                if not new_pass or not confirm_pass:
                                    messagebox.showerror("❌ Error", "Fill all fields!")
                                    return
                                
                                if new_pass == confirm_pass:
                                    hashed_new = To_Sha512(new_pass)
                                    with open("Users.txt", 'r') as f:
                                        lines = f.read()
                                    
                                    # Replace old password with new one
                                    if existing_email:
                                        old_line = existing_user + "|" + existing_email + "|" + existing_pass
                                        new_line = existing_user + "|" + existing_email + "|" + hashed_new
                                    else:
                                        old_line = existing_user + "|" + existing_pass
                                        new_line = existing_user + "|" + hashed_new
                                    
                                    lines = lines.replace(old_line, new_line)
                                    with open("Users.txt", 'w') as f:
                                        f.write(lines)
                                    update_dialog.destroy()
                                    messagebox.showinfo("✅ Success", "Password Updated Successfully!")
                                    self.show_user_menu()
                                else:
                                    messagebox.showerror("❌ Error", "Passwords do not match!")
                            
                            tk.Button(update_dialog, text="💾 Save", command=save_update,width=20,
                                    bg='#9d4edd', fg='white', relief='flat',
                                    font=('Segoe UI', 11, 'bold')).pack(pady=15)
                            return
                        else:
                            messagebox.showerror("❌ Error", "Incorrect Password!")
                            self.show_user_menu()
                            return
            
            messagebox.showerror("❌ Error", "Username Not Found!")
            self.show_user_menu()
            
        except FileNotFoundError:
            messagebox.showerror("❌ Error", "No users found!")
            self.show_user_menu()
    
    def verify_and_show_update_popup(self, hashed_username, hashed_password, username):
        """Verify old credentials and show update popup"""
        try:
            with open("Users.txt", 'r') as f:
                for line in f.readlines():
                    line = line.rstrip()
                    
                    parts = line.split("|")
                    existing_user = parts[0]
                    
                    # Handle both old and new format
                    if len(parts) >= 4:
                        stored_username = parts[1]
                        existing_email = parts[2]
                        existing_pass = parts[3]
                    elif len(parts) == 3:
                        stored_username = parts[1]
                        existing_email = ""
                        existing_pass = parts[2]
                    elif len(parts) == 2:
                        stored_username = parts[0]
                        existing_email = ""
                        existing_pass = parts[1]
                    else:
                        continue
                    
                    if existing_user == hashed_username:
                        if existing_pass == hashed_password:
                            # Credentials verified - show update popup with current data
                            self.show_update_account_popup(existing_user, stored_username, existing_email, existing_pass)
                            return
                        else:
                            messagebox.showerror("❌ Error", "Incorrect Password!")
                            self.show_user_credentials("Update")
                            return
            
            messagebox.showerror("❌ Error", "Username Not Found!")
            self.show_user_credentials("Update")
            
        except FileNotFoundError:
            messagebox.showerror("❌ Error", "No users found!")
            self.show_user_menu()
    
    def show_update_account_popup(self, old_hashed_username, current_username, current_email, current_password):
        """Show popup to update username, password, and email"""
        update_dialog = tk.Toplevel(self.root)
        update_dialog.title("✏️ Update Account")
        update_dialog.geometry("500x600")
        update_dialog.configure(bg=self.colors['bg_medium'])
        update_dialog.transient(self.root)
        
        # Header
        header = tk.Frame(update_dialog, bg=self.colors['bg_medium'])
        header.pack(pady=(20, 10))
        
        icon_label = tk.Label(header, text="✏️", font=('Segoe UI', 30), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_orange'])
        icon_label.pack(pady=(0, 5))
        
        title = tk.Label(update_dialog, text="Update Your Account", 
                        font=('Segoe UI', 16, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 10))
        
        # Input fields
        input_frame = tk.Frame(update_dialog, bg=self.colors['bg_medium'])
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="New Username:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(5, 5))
        new_username_entry = tk.Entry(input_frame, font=('Segoe UI', 11),
                                     bg=self.colors['bg_light'], fg=self.colors['text_white'],
                                     relief='flat')
        new_username_entry.pack(pady=5)
        new_username_entry.insert(0, current_username)
        
        tk.Label(input_frame, text="New Email:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        new_email_entry = tk.Entry(input_frame, font=('Segoe UI', 11),
                                  bg=self.colors['bg_light'], fg=self.colors['text_white'],
                                  relief='flat')
        new_email_entry.pack(pady=5)
        new_email_entry.insert(0, current_email)
        
        tk.Label(input_frame, text="New Password:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        new_password_entry = tk.Entry(input_frame, show="*", font=('Segoe UI', 11),
                                    bg=self.colors['bg_light'], fg=self.colors['text_white'],
                                    relief='flat')
        new_password_entry.pack(pady=5)
        
        tk.Label(input_frame, text="Confirm Password:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        confirm_password_entry = tk.Entry(input_frame, show="*", font=('Segoe UI', 11),
                                         bg=self.colors['bg_light'], fg=self.colors['text_white'],
                                         relief='flat')
        confirm_password_entry.pack(pady=5)
        
        def save_update():
            new_username = new_username_entry.get()
            new_email = new_email_entry.get()
            new_password = new_password_entry.get()
            confirm_password = confirm_password_entry.get()
            
            if not new_username or not new_email or not new_password:
                messagebox.showerror("❌ Error", "Please fill in all fields!")
                return
            
            if new_password != confirm_password:
                messagebox.showerror("❌ Error", "Passwords do not match!")
                return
            
            # Hash new values
            new_hashed_username = To_Sha256(new_username)
            new_hashed_password = To_Sha512(new_password)
            
            try:
                with open("Users.txt", 'r') as f:
                    lines = f.read()
                
                # Build old line based on format
                if current_email:
                    old_line = old_hashed_username + "|" + current_username + "|" + current_email + "|" + current_password
                else:
                    old_line = old_hashed_username + "|" + current_password
                
                # Build new line
                new_line = new_hashed_username + "|" + new_username + "|" + new_email + "|" + new_hashed_password
                
                lines = lines.replace(old_line, new_line)
                
                # Handle file renaming if username changed
                if new_hashed_username != old_hashed_username:
                    # Rename .txt file (vault)
                    old_txt_file = old_hashed_username + ".txt"
                    new_txt_file = new_hashed_username + ".txt"
                    try:
                        import os
                        if os.path.exists(old_txt_file):
                            os.rename(old_txt_file, new_txt_file)
                    except Exception as e:
                        print(f"Error renaming txt file: {e}")
                    
                    # Rename .key file
                    old_key_file = old_hashed_username + ".key"
                    new_key_file = new_hashed_username + ".key"
                    try:
                        if os.path.exists(old_key_file):
                            os.rename(old_key_file, new_key_file)
                    except Exception as e:
                        print(f"Error renaming key file: {e}")
                
                with open("Users.txt", 'w') as f:
                    f.write(lines)
                
                update_dialog.destroy()
                
                # Show confirmation popup with updated details
                self.show_updated_confirmation_popup(new_username, new_email)
                
            except Exception as e:
                messagebox.showerror("❌ Error", f"Failed to update: {str(e)}")
        
        # Buttons
        btn_frame = tk.Frame(update_dialog, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=20)
        
        save_btn = tk.Button(btn_frame, text="💾  Save Changes", command=save_update,
                           bg='#ff6b35', fg='white', relief='flat',
                           font=('Segoe UI', 11, 'bold'), width=18)
        save_btn.pack(side='left', padx=10)
        
        cancel_btn = tk.Button(btn_frame, text="✖  Cancel", command=update_dialog.destroy,
                             bg='#6c757d', fg='white', relief='flat',
                             font=('Segoe UI', 11, 'bold'), width=15)
        cancel_btn.pack(side='left', padx=10)
    
    def show_updated_confirmation_popup(self, updated_username, updated_email):
        """Show confirmation popup with updated details"""
        confirm_dialog = tk.Toplevel(self.root)
        confirm_dialog.title("✅ Account Updated")
        confirm_dialog.geometry("450x450")
        confirm_dialog.configure(bg=self.colors['bg_medium'])
        confirm_dialog.transient(self.root)
        
        # Header
        header = tk.Frame(confirm_dialog, bg=self.colors['bg_medium'])
        header.pack(pady=(20, 10))
        
        icon_label = tk.Label(header, text="✅", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
        icon_label.pack(pady=(0, 5))
        
        title = tk.Label(confirm_dialog, text="Account Updated Successfully!", 
                        font=('Segoe UI', 16, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
        title.pack(pady=(0, 10))
        
        # Details frame
        details_frame = tk.Frame(confirm_dialog, bg=self.colors['bg_medium'])
        details_frame.pack(pady=15)
        
        # Username
        username_label = tk.Label(details_frame, text="👤 Username:", 
                                 font=('Segoe UI', 11, 'bold'),
                                 bg=self.colors['bg_medium'], fg=self.colors['text_gray'])
        username_label.pack(pady=(10, 3))
        
        username_value = tk.Label(details_frame, text=updated_username, 
                                font=('Segoe UI', 12),
                                bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        username_value.pack(pady=(0, 10))
        
        # Email
        email_label = tk.Label(details_frame, text="📧 Email:", 
                             font=('Segoe UI', 11, 'bold'),
                             bg=self.colors['bg_medium'], fg=self.colors['text_gray'])
        email_label.pack(pady=(5, 3))
        
        email_value = tk.Label(details_frame, text=updated_email, 
                             font=('Segoe UI', 12),
                             bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        email_value.pack(pady=(0, 10))
        
        # Info text
        info_label = tk.Label(confirm_dialog, text="Your account details have been updated.", 
                            font=('Segoe UI', 10),
                            bg=self.colors['bg_medium'], fg=self.colors['text_gray'])
        info_label.pack(pady=(10, 15))
        
        # OK button
        ok_btn = tk.Button(confirm_dialog, text="✓  OK", command=lambda: [confirm_dialog.destroy(), self.show_user_menu()],
                         bg='#00f5d4', fg='#1a1a2e', relief='flat',
                         font=('Segoe UI', 12, 'bold'), width=15)
        ok_btn.pack(pady=10)
    
    # ==================== FORGOT PASSWORD ====================
    
    def show_forgot_password(self):
        """Show forgot password screen"""
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_user_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text="🔑", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_purple'])
        icon_label.pack(pady=(0, 10))
        
        title = tk.Label(self.container, text="Forgot Password", 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 30))
        
        # Info label
        info_label = tk.Label(self.container, text="Enter your username or email to reset password", 
                            font=('Segoe UI', 11),
                            bg=self.colors['bg_medium'], fg=self.colors['text_gray'])
        info_label.pack(pady=(0, 20))
        
        input_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Username or Email:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(0, 5))
        username_entry, _ = self.create_modern_entry(input_frame)
        
        # Store the found user info
        self.forgot_user_data = None
        
        def find_user():
            """Find user by username or email"""
            username_or_email = username_entry.get()
            
            if not username_or_email:
                messagebox.showerror("❌ Error", "Please enter username or email!")
                return
            
            try:
                with open("Users.txt", 'r') as f:
                    for line in f.readlines():
                        line = line.rstrip()
                        if not line:
                            continue
                        
                        parts = line.split("|")
                        if len(parts) >= 3:
                            hashed_username = parts[0]
                            stored_username = parts[1]
                            stored_email = parts[2]
                            stored_password = parts[3]
                        elif len(parts) == 2:
                            continue  # Skip old format
                        else:
                            continue
                        
                        # Check if username or email matches
                        if stored_username == username_or_email or stored_email == username_or_email:
                            # User found - store data and send verification
                            self.forgot_user_data = {
                                'hashed_username': hashed_username,
                                'username': stored_username,
                                'email': stored_email,
                                'old_password': stored_password
                            }
                            send_verification_to_email()
                            return
                
                messagebox.showerror("❌ Error", "User not found! Please check your username or email.")
                
            except FileNotFoundError:
                messagebox.showerror("❌ Error", "No users found!")
        
        # Verification code frame (initially hidden)
        verify_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        
        tk.Label(verify_frame, text="🔐 Verification code sent to your email", 
                font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['accent_green']).pack(pady=(0, 10))
        
        tk.Label(verify_frame, text="Enter 6-digit Code:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        code_entry, _ = self.create_modern_entry(verify_frame, width=20)
        
        # New password frame (initially hidden)
        new_pass_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        
        tk.Label(new_pass_frame, text="✅ Code Verified! Set New Password", 
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['bg_medium'], fg=self.colors['accent_green']).pack(pady=(0, 15))
        
        tk.Label(new_pass_frame, text="New Password:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        new_pass_entry, _ = self.create_modern_entry(new_pass_frame, show="*")
        
        tk.Label(new_pass_frame, text="Confirm Password:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        confirm_pass_entry, _ = self.create_modern_entry(new_pass_frame, show="*")
        
        # Store generated code
        generated_code = None
        
        def send_verification_to_email():
            """Send verification code to user's email"""
            nonlocal generated_code
            
            if not self.forgot_user_data:
                return
            
            user_email = self.forgot_user_data['email']
            
            if not user_email:
                messagebox.showerror("❌ Error", "No email found for this user!")
                return
            
            # Generate code
            generated_code = email_sender.generate_verification_code()
            
            # Send email
            success = email_sender.send_verification_code(to_email=user_email, code=generated_code)
            
            if success:
                messagebox.showinfo("✅ Email Sent", f"Verification code sent to {user_email}!")
            else:
                # Demo mode - show the code anyway
                messagebox.showinfo("📧 Demo Mode", 
                    f"Email not sent (check credentials).\n\nYour verification code is: {generated_code}")
            
            # Hide input frame, show verify frame
            input_frame.pack_forget()
            verify_frame.pack(pady=20)
            
            # Hide step 1 buttons, show step 2 buttons
            step1_buttons.pack_forget()
            step2_buttons.pack(pady=30)
        
        def verify_code():
            """Verify the code and show password reset form"""
            nonlocal generated_code
            
            entered_code = code_entry.get()
            
            if entered_code == generated_code:
                # Code correct - show password reset form
                verify_frame.pack_forget()
                new_pass_frame.pack(pady=20)
                
                # Hide step 2 buttons, show step 3 buttons
                step2_buttons.pack_forget()
                step3_buttons.pack(pady=30)
            else:
                messagebox.showerror("❌ Error", "Incorrect Code!")
                code_entry.delete(0, 'end')
        
        def reset_password():
            """Reset the password"""
            new_pass = new_pass_entry.get()
            confirm_pass = confirm_pass_entry.get()
            
            if not new_pass or not confirm_pass:
                messagebox.showerror("❌ Error", "Please fill in all fields!")
                return
            
            if new_pass != confirm_pass:
                messagebox.showerror("❌ Error", "Passwords do not match!")
                return
            
            if len(new_pass) < 4:
                messagebox.showerror("❌ Error", "Password must be at least 4 characters!")
                return
            
            # Hash new password
            new_hashed_password = To_Sha512(new_pass)
            
            try:
                with open("Users.txt", 'r') as f:
                    lines = f.read()
                
                # Build old line and new line
                old_line = (self.forgot_user_data['hashed_username'] + "|" + 
                           self.forgot_user_data['username'] + "|" + 
                           self.forgot_user_data['email'] + "|" + 
                           self.forgot_user_data['old_password'])
                
                new_line = (self.forgot_user_data['hashed_username'] + "|" + 
                           self.forgot_user_data['username'] + "|" + 
                           self.forgot_user_data['email'] + "|" + 
                           new_hashed_password)
                
                lines = lines.replace(old_line, new_line)
                
                with open("Users.txt", 'w') as f:
                    f.write(lines)
                
                messagebox.showinfo("✅ Success", "Password Reset Successfully!\n\nPlease login with your new password.")
                self.show_user_menu()
                
            except Exception as e:
                messagebox.showerror("❌ Error", f"Failed to reset password: {str(e)}")
        
        # ========== STEP 1 BUTTONS (Find Account) - Initially visible ==========
        step1_buttons = tk.Frame(self.container, bg=self.colors['bg_medium'])
        step1_buttons.pack(pady=30)
        
        submit_btn = self.create_modern_button(step1_buttons, "✓  Find Account", 
                                               find_user,
                                               bg='#9d4edd', hover_color='#7b2cbf')
        submit_btn.pack(side='left', padx=10)
        
        back_btn_step1 = self.create_modern_button(step1_buttons, "←  Back", 
                                             self.show_user_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn_step1.pack(side='left', padx=10)
        
        # ========== STEP 2 BUTTONS (Verify Code) - Initially hidden ==========
        step2_buttons = tk.Frame(self.container, bg=self.colors['bg_medium'])
        
        verify_btn = self.create_modern_button(step2_buttons, "✓  Verify Code", 
                                               verify_code,
                                               bg='#00f5d4', hover_color='#00c4a7')
        verify_btn.pack(side='left', padx=10)
        
        back_btn_step2 = self.create_modern_button(step2_buttons, "←  Back", 
                                             self.show_user_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn_step2.pack(side='left', padx=10)
        
        # ========== STEP 3 BUTTONS (Reset Password) - Initially hidden ==========
        step3_buttons = tk.Frame(self.container, bg=self.colors['bg_medium'])
        
        reset_btn = self.create_modern_button(step3_buttons, "💾  Reset Password", 
                                               reset_password,
                                               bg='#00f5d4', hover_color='#00c4a7')
        reset_btn.pack(side='left', padx=10)
        
        back_btn_step3 = self.create_modern_button(step3_buttons, "←  Back", 
                                             self.show_user_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn_step3.pack(side='left', padx=10)
    
    # ==================== PASSMAN MENU ====================
    
    def show_passman_menu(self):
        """Show the Passman Menu"""
        self.clear_frame()
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(20, 10))
        
        icon_label = tk.Label(header, text="🔐", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_blue'])
        icon_label.pack(pady=(20, 10))
        
        title = tk.Label(self.container, text="Passman Menu", 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 5))
        
        welcome = tk.Label(self.container, text=f"Welcome, {self.username}! 👋", 
                          font=('Segoe UI', 12),
                          bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
        welcome.pack(pady=(0, 25))
        
        menu_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        menu_frame.pack(pady=10)
        
        btn_save = self.create_modern_button(
            menu_frame, "💾  Save New Login",
            self.show_save_new,
            bg='#00f5d4', hover_color='#00c4a7'
        )
        btn_save.pack(pady=8, ipadx=50)
        
        btn_show = self.create_modern_button(
            menu_frame, "👁️  Show All Logins",
            self.show_all_details,
            bg='#00d9ff', hover_color='#00b8d9'
        )
        btn_show.pack(pady=8, ipadx=50)
        
        btn_update = self.create_modern_button(
            menu_frame, "✏️  Update Login Details",
            self.show_update_details,
            bg='#ff6b35', hover_color='#e55a2b'
        )
        btn_update.pack(pady=8, ipadx=50)
        
        # Import/Export buttons
        btn_export = self.create_modern_button(
            menu_frame, "📤  Export Logins",
            self.show_export_menu,
            bg='#9d4edd', hover_color='#7b2cbf'
        )
        btn_export.pack(pady=8, ipadx=50)
        
        btn_import = self.create_modern_button(
            menu_frame, "📥  Import Logins",
            self.show_import_menu,
            bg='#00d9ff', hover_color='#00b8d9'
        )
        btn_import.pack(pady=8, ipadx=50)
        
        btn_back = self.create_modern_button(
            menu_frame, "←  logout",
            self.show_user_menu,
            bg='#6c757d', hover_color='#5a6268'
        )
        btn_back.pack(pady=8, ipadx=50)
        
        btn_exit = self.create_modern_button(
            menu_frame, "🚪  Exit",
            self.exit_app,
            bg='#e63946', hover_color='#c1121f'
        )
        btn_exit.pack(pady=8, ipadx=50)
    
    def show_save_new(self):
        """Show save new details form"""
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_passman_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text="💾", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
        icon_label.pack(pady=(0, 10))
        
        title = tk.Label(self.container, text="Save New Details", 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 30))
        
        input_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Site Name:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(0, 5))
        sitename_entry, _ = self.create_modern_entry(input_frame)
        
        tk.Label(input_frame, text="Site Username:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        siteuser_entry, _ = self.create_modern_entry(input_frame)
        
        tk.Label(input_frame, text="Site Password:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        sitepass_entry, _ = self.create_modern_entry(input_frame, show="*")
        
        # ========== PASSWORD STRENGTH METER ==========
        strength_frame = tk.Frame(input_frame, bg=self.colors['bg_medium'])
        strength_frame.pack(pady=(10, 5), fill='x', expand=True)
        
        strength_label = tk.Label(strength_frame, text="🔐 Password Strength: ", 
                                font=('Segoe UI', 10),
                                bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        strength_label.pack(side='left')
        
        strength_indicator = tk.Label(strength_frame, text="Enter Password",
                                    font=('Segoe UI', 10, 'bold'),
                                    bg=self.colors['bg_medium'], fg="#6c757d")
        strength_indicator.pack(side='left', padx=(0, 10))
        
        def update_strength(*args):
            password = sitepass_entry.get()
            strength_text, score, color = calculate_password_strength(password)
            strength_indicator.config(text=strength_text, fg=color)
        
        sitepass_entry.bind('<KeyRelease>', update_strength)
        
        # ========== PASSWORD GENERATOR ==========
        def generate_secure_pass():
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(alphabet) for i in range(16))
            sitepass_entry.delete(0, tk.END)
            sitepass_entry.insert(0, password)
            update_strength()

        gen_btn = tk.Button(input_frame, text="⚡ Generate Strong Password", 
                           command=generate_secure_pass,
                           font=('Segoe UI', 9, 'bold'), bg=self.colors['bg_light'], 
                           fg=self.colors['accent_blue'], relief='flat', cursor='hand2')
        gen_btn.pack(pady=5)

        def save_details():
            sitename = sitename_entry.get()
            siteuser = siteuser_entry.get()
            sitepass = sitepass_entry.get()
            tag = self.tag_combo.get() or "Other"
            
            if not sitename or not siteuser or not sitepass:
                messagebox.showerror("❌ Error", "Please fill in all fields!")
                return
            
            encrypted_user = self.cipher.encrypt(siteuser.encode()).decode()
            encrypted_pass = self.cipher.encrypt(sitepass.encode()).decode()
            
            # Get current timestamp for expiry tracking
            timestamp = str(int(time.time()))
            
            # Format: sitename|tag|encrypted_user~encrypted_pass|timestamp
            with open(self.filename, 'a') as f:
                f.write(f"{sitename}|{tag}|{encrypted_user}~{encrypted_pass}|{timestamp}\n")
            
            messagebox.showinfo("✅ Success", f"Details saved with tag '{tag}'!")
            self.show_passman_menu()
        
        btn_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=30)
        
        save_btn = self.create_modern_button(btn_frame, "💾  Save", 
                                            save_details,
                                            bg='#00f5d4', hover_color='#00c4a7')
        save_btn.pack(side='left', padx=10)
        
        back_btn = self.create_modern_button(btn_frame, "←  Back", 
                                             self.show_passman_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn.pack(side='left', padx=10)
    
    def show_all_details(self):
        """Show all saved login details"""
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_passman_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        title = tk.Label(self.container, text="👁️ All Login Details", 
                        font=('Segoe UI', 18, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(30, 15))
        
        # Instruction label
        instruction = tk.Label(self.container, text="💡 Double-click on a row to view details", 
                              font=('Segoe UI', 10),
                              bg=self.colors['bg_medium'], fg=self.colors['text_gray'])
        instruction.pack(pady=(0, 10))
        
        # Search bar
        search_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        search_frame.pack(fill='x', padx=30, pady=5)
        
        tk.Label(search_frame, text="🔍 Search:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(side='left', padx=5)
        
        search_entry = tk.Entry(search_frame, font=('Segoe UI', 11),
                              bg=self.colors['bg_light'], fg=self.colors['text_white'],
                              relief='flat')
        search_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Create treeview with modern styling
        tree_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        tree_frame.pack(fill='both', expand=True, padx=30, pady=15)
        
        # Style the treeview
        style = ttk.Style()
        style.configure("Treeview", 
                       background="#0f3460",
                       foreground="white",
                       fieldbackground="#0f3460",
                       rowheight=30)
        style.configure("Treeview.Heading",
                       background="#00d9ff",
                       foreground="#1a1a2e",
                       font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#00d9ff')])

        tree = ttk.Treeview(tree_frame, columns=("Site", "Username", "Password", "Expiry"), show='headings')
        # Add row striping for better UX
        tree.tag_configure('oddrow', background=self.colors['bg_light'])

        tree.heading("Site", text="🌐 Site Name")
        tree.heading("Username", text="👤 Username")
        tree.heading("Password", text="🔑 Password")
        tree.heading("Expiry", text="⏳ Expiry")
        
        tree.column("Site", width=150)
        tree.column("Username", width=150)
        tree.column("Password", width=150)
        tree.column("Expiry", width=150)
        
        # Store all data for filtering (including encrypted values for decryption later)
        self.all_details = []
        
        try:
            with open(self.filename, 'r') as f:
                for line in f.readlines():
                    line = line.rstrip()
                    if '|' in line:
                        parts = line.split("|")
                        sitename = parts[0]
                        decode_line = ""
                        timestamp = ""
                        if len(parts) >= 4: 
                            decode_line = parts[2]
                            timestamp = parts[3]
                        elif len(parts) == 3: 
                            if '~' in parts[1]:
                                decode_line = parts[1]
                                timestamp = parts[2]
                            elif '~' in parts[2]:
                                decode_line = parts[2]
                        elif len(parts) == 2: 
                            decode_line = parts[1]
                        
                        if '~' in decode_line:
                            siteuser, sitepass = decode_line.split("~", 1)
                            # Strip timestamp if present
                            sitepass = sitepass.split('|')[0]
                            
                            expiry_status = "❓ Unknown"
                            if timestamp:
                                expiry_status, _, _ = get_expiry_status(timestamp)
                            
                            # Store encrypted values + expiry
                            self.all_details.append((sitename, siteuser, sitepass, expiry_status))
        except FileNotFoundError:
            pass
        
        # Insert all items initially (show masked)
        for item in self.all_details:
            tree.insert("", "end", values=(item[0], "🔒 Locked", "🔒 Locked", item[3]))
        
        # Search function
        def filter_tree(*args):
            search_text = search_entry.get().lower()
            for item in tree.get_children():
                tree.delete(item)
            for item in self.all_details:
                if search_text in item[0].lower():
                    tree.insert("", "end", values=(item[0], "🔒 Locked", "🔒 Locked", item[3]))

        search_entry.bind('<KeyRelease>', filter_tree)
        
        # Double-click handler to open detail popup
        def on_double_click(event):
            item = tree.selection()
            if not item:
                return
            
            # Get the selected item values
            selected_item = tree.item(item)
            site_name = selected_item['values'][0]
            
            # Find the corresponding encrypted data
            for detail in self.all_details:
                if detail[0] == site_name:
                    self.show_detail_popup(detail[0], detail[1], detail[2])
                    break
        
        # Bind double-click event
        tree.bind('<Double-1>', on_double_click)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        back_btn = self.create_modern_button(self.container, "←  Back", 
                                 self.show_passman_menu,
                                 bg='#6c757d', hover_color='#5a6268')
        back_btn.pack(pady=15)

    def show_detail_popup(self, sitename, encrypted_user, encrypted_pass):
        """Show a popup with email passkey - sends 6-digit code to user's email"""
        popup = tk.Toplevel(self.root)
        popup.title(f"🔐 {sitename}")
        popup.geometry("420x420")
        popup.configure(bg=self.colors['bg_medium'])
        popup.transient(self.root)
        
        # Header
        header = tk.Frame(popup, bg=self.colors['bg_medium'])
        header.pack(pady=(20, 10))
        
        icon_label = tk.Label(header, text="🔐", font=('Segoe UI', 30), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_blue'])
        icon_label.pack(pady=(0, 5))
        
        title = tk.Label(popup, text=sitename, 
                        font=('Segoe UI', 16, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 10))
        
        # Info label showing the email
        email_label = tk.Label(popup, text=f"📧 Code will be sent to: {self.user_email}", 
                            font=('Segoe UI', 10),
                            bg=self.colors['bg_medium'], fg=self.colors['text_gray'])
        email_label.pack(pady=(0, 15))
        
        # Email frame (initially shown)
        email_frame = tk.Frame(popup, bg=self.colors['bg_medium'])
        email_frame.pack(pady=10)
        
        # Store the generated code
        generated_code = None
        
        def send_verification_code():
            """Generate and send verification code to user's email"""
            nonlocal generated_code
            
            # Generate 6-digit code
            generated_code = email_sender.generate_verification_code()
            
            # Send email with the code using credentials from email_sender module
            success = email_sender.send_verification_code(
                to_email=self.user_email,
                code=generated_code
            )
            
            if success:
                messagebox.showinfo("✅ Email Sent", f"Verification code sent to {self.user_email}!")
                
                # Hide email frame, show code entry frame
                email_frame.pack_forget()
                code_frame.pack(pady=20)
                
            else:
                # For testing/demo purposes, show the code anyway
                messagebox.showinfo("📧 Demo Mode", 
                    f"Email not sent (check credentials in code).\n\nYour verification code is: {generated_code}\n\n(For production, configure email_sender.py with real credentials)")
                
                # Hide email frame, show code entry frame
                email_frame.pack_forget()
                code_frame.pack(pady=20)
        
        # Send button
        send_btn = tk.Button(email_frame, text="📧 Send Passkey Code", command=send_verification_code,
                            bg='#00d9ff', fg='#1a1a2e', relief='flat',
                            font=('Segoe UI', 11, 'bold'), width=22)
        send_btn.pack(pady=10)
        
        # Code entry frame (initially hidden)
        code_frame = tk.Frame(popup, bg=self.colors['bg_medium'])
        
        tk.Label(code_frame, text="🔑 Enter 6-digit Code:", 
                font=('Segoe UI', 12),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(0, 5))
        
        code_entry = tk.Entry(code_frame, font=('Segoe UI', 14, 'bold'),
                            bg=self.colors['bg_light'], fg=self.colors['text_white'],
                            relief='flat', width=15, justify='center')
        code_entry.pack(pady=10)
        
        # Result frame (initially hidden)
        result_frame = tk.Frame(popup, bg=self.colors['bg_medium'])
        
        def verify_code_and_show():
            """Verify the code and show decrypted details"""
            entered_code = code_entry.get()
            
            if entered_code == generated_code:
                # Code correct - decrypt and show details
                try:
                    decrypted_user = self.cipher.decrypt(encrypted_user.encode()).decode()
                    decrypted_pass = self.cipher.decrypt(encrypted_pass.encode()).decode()
                    
                    # Hide code frame, show result frame
                    code_frame.pack_forget()
                    result_frame.pack(fill='both', expand=True, padx=20)
                    
                    # Username field
                    user_label = tk.Label(result_frame, text="👤 Username:", 
                                        font=('Segoe UI', 11, 'bold'),
                                        bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
                    user_label.pack(pady=(10, 5))
                    
                    user_value_frame = tk.Frame(result_frame, bg=self.colors['bg_medium'])
                    user_value_frame.pack(pady=(0, 5))
                    
                    user_value = tk.Label(user_value_frame, text=decrypted_user, 
                                        font=('Segoe UI', 11),
                                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
                    user_value.pack(side='left', padx=(0, 10))
                    
                    # Copy Username Button
                    def copy_username():
                        self.root.clipboard_clear()
                        self.root.clipboard_append(decrypted_user)
                        # Auto-clear clipboard after 30 seconds
                        def clear_clipboard():
                            try:
                                if self.root.clipboard_get() == decrypted_user:
                                    self.root.clipboard_clear()
                                    copy_feedback.config(text="✅ Clipboard will clear in 30s", fg=self.colors['accent_orange'])
                            except:
                                pass
                        self.root.after(30000, clear_clipboard)
                        copy_feedback.config(text="✅ Copied! Auto-clear in 30s", fg=self.colors['accent_green'])
                        self.root.after(3000, lambda: copy_feedback.config(text="", fg=self.colors['bg_medium']))
                    
                    copy_user_btn = tk.Button(user_value_frame, text="📋 Copy", command=copy_username,
                                            bg=self.colors['bg_light'], fg=self.colors['text_white'],
                                            relief='flat', font=('Segoe UI', 9), cursor='hand2')
                    copy_user_btn.pack(side='left', padx=5)
                    
                    # Password field
                    pass_label = tk.Label(result_frame, text="🔑 Password:", 
                                        font=('Segoe UI', 11, 'bold'),
                                        bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
                    pass_label.pack(pady=(10, 5))
                    
                    pass_value_frame = tk.Frame(result_frame, bg=self.colors['bg_medium'])
                    pass_value_frame.pack(pady=(0, 5))
                    
                    pass_value = tk.Label(pass_value_frame, text=decrypted_pass, 
                                        font=('Segoe UI', 11),
                                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
                    pass_value.pack(side='left', padx=(0, 10))
                    
                    # Copy Password Button
                    def copy_password():
                        self.root.clipboard_clear()
                        self.root.clipboard_append(decrypted_pass)
                        # Auto-clear clipboard after 30 seconds
                        def clear_clipboard():
                            try:
                                if self.root.clipboard_get() == decrypted_pass:
                                    self.root.clipboard_clear()
                                    copy_feedback.config(text="✅ Clipboard cleared!", fg=self.colors['accent_green'])
                            except:
                                pass
                        self.root.after(30000, clear_clipboard)
                        copy_feedback.config(text="✅ Copied! Auto-clear in 30s", fg=self.colors['accent_green'])
                        self.root.after(3000, lambda: copy_feedback.config(text="", fg=self.colors['bg_medium']))
                    
                    copy_pass_btn = tk.Button(pass_value_frame, text="📋 Copy", command=copy_password,
                                            bg=self.colors['bg_light'], fg=self.colors['text_white'],
                                            relief='flat', font=('Segoe UI', 9), cursor='hand2')
                    copy_pass_btn.pack(side='left', padx=5)
                    
                    # Copy feedback label
                    copy_feedback = tk.Label(result_frame, text="", 
                                            font=('Segoe UI', 9),
                                            bg=self.colors['bg_medium'], fg=self.colors['bg_medium'])
                    copy_feedback.pack(pady=(5, 0))
                    
                    # Success indicator
                    success_label = tk.Label(result_frame, text="✅ Verified Successfully!", 
                                            font=('Segoe UI', 10),
                                            bg=self.colors['bg_medium'], fg=self.colors['accent_green'])
                    success_label.pack(pady=(10, 0))
                    
                except Exception as e:
                    messagebox.showerror("❌ Error", f"Decryption failed: {str(e)}")
                    popup.destroy()
            else:
                messagebox.showerror("❌ Error", "Incorrect Code!")
                code_entry.delete(0, 'end')
        
        # Verify button
        verify_btn = tk.Button(code_frame, text="✓ Verify Code", command=verify_code_and_show,
                            bg='#00f5d4', fg='#1a1a2e', relief='flat',
                            font=('Segoe UI', 11, 'bold'), width=18)
        verify_btn.pack(pady=10)
        
        code_entry.bind('<Return>', lambda e: verify_code_and_show())
        
        # Close button
        close_btn = tk.Button(popup, text="✖  Close", command=popup.destroy,
                            bg='#e63946', fg='white', relief='flat',
                            font=('Segoe UI', 10, 'bold'), width=15)
        close_btn.pack(pady=15)
    
    def show_update_details(self):
        """Show update details selection"""
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_passman_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text="✏️", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_orange'])
        icon_label.pack(pady=(0, 10))
        
        title = tk.Label(self.container, text="Update Login Details", 
                        font=('Segoe UI', 18, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 20))
        
        tk.Label(self.container, text="Select a site to update:", 
                font=('Segoe UI', 11), bg=self.colors['bg_medium'], 
                fg=self.colors['text_white']).pack(pady=10)
        
        # List of sites
        list_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        list_frame.pack(fill='both', expand=True, padx=50, pady=10)
        
        sites = []
        try:
            with open(self.filename, 'r') as f:
                for line in f.readlines():
                    line = line.rstrip()
                    if '|' in line:
                        parts = line.split("|")
                        sites.append(parts[0])
        except FileNotFoundError:
            pass
        
        if not sites:
            messagebox.showinfo("ℹ️ Info", "No sites found!")
            self.show_passman_menu()
            return
        
        # Create listbox
        listbox = tk.Listbox(list_frame, font=('Segoe UI', 11), height=10,
                           bg=self.colors['bg_light'], fg=self.colors['text_white'],
                           relief='flat', selectbackground=self.colors['accent_blue'])
        for site in sites:
            listbox.insert('end', f"🌐 {site}")
        listbox.pack(fill='both', expand=True)
        
        def select_site():
            selection = listbox.curselection()
            if not selection:
                messagebox.showerror("❌ Error", "Please select a site!")
                return
            
            selected_site = listbox.get(selection[0]).replace("🌐 ", "")
            self.update_site_details(selected_site)
        
        btn_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=15)
        
        select_btn = self.create_modern_button(btn_frame, "✓  Select", 
                                               select_site,
                                               bg='#ff6b35', hover_color='#e55a2b')
        select_btn.pack(side='left', padx=10)
        
        back_btn = self.create_modern_button(btn_frame, "←  Back", 
                                             self.show_passman_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn.pack(side='left', padx=10)
    
    def update_site_details(self, sitename):
        """Update details for a specific site"""
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_update_details)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text="✏️", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_orange'])
        icon_label.pack(pady=(0, 10))
        
        title = tk.Label(self.container, text=f"Update: {sitename}", 
                        font=('Segoe UI', 18, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 20))
        
        input_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="New Username:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(0, 5))
        new_user_entry, _ = self.create_modern_entry(input_frame)
        
        tk.Label(input_frame, text="New Password:", font=('Segoe UI', 11),
                bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(pady=(10, 5))
        new_pass_entry, _ = self.create_modern_entry(input_frame, show="*")
        
        # Read current values
        old_user = ""
        old_pass = ""
        try:
            with open(self.filename, 'r') as f:
                for line in f.readlines():
                    line = line.rstrip()
                    if '|' in line:
                        parts = line.split("|")
                        site = parts[0]
                        if site == sitename:
                            decode_line = ""
                            if len(parts) >= 4: decode_line = parts[2]
                            elif len(parts) == 3: decode_line = parts[1] if '~' in parts[1] else parts[2]
                            elif len(parts) == 2: decode_line = parts[1]
                            
                            if '~' in decode_line:
                                siteuser, sitepass = decode_line.split("~", 1)
                                sitepass = sitepass.split('|')[0]
                                old_user = self.cipher.decrypt(siteuser.encode()).decode()
                                old_pass = self.cipher.decrypt(sitepass.encode()).decode()
        except:
            pass
        
        # Pre-fill with current values
        new_user_entry.insert(0, old_user)
        new_pass_entry.insert(0, old_pass)
        
        def save_update():
            new_user = new_user_entry.get()
            new_pass = new_pass_entry.get()
            
            if not new_user or not new_pass:
                messagebox.showerror("❌ Error", "Please fill in all fields!")
                return
            
            encrypted_user = self.cipher.encrypt(new_user.encode()).decode()
            encrypted_pass = self.cipher.encrypt(new_pass.encode()).decode()
            
            try:
                with open(self.filename, 'r') as f:
                    lines = f.readlines()
                
                new_lines = []
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    parts = line.split('|')
                    if parts[0] == sitename:
                        # Preserve tag and timestamp if possible
                        tag = parts[1] if len(parts) >= 4 else "Other"
                        timestamp = parts[-1] if len(parts) >= 3 else str(int(time.time()))
                        new_lines.append(f"{sitename}|{tag}|{encrypted_user}~{encrypted_pass}|{timestamp}")
                    else:
                        new_lines.append(line)
                
                with open(self.filename, 'w') as f:
                    f.write('\n'.join(new_lines) + '\n')
                
                messagebox.showinfo("✅ Success", "Details Updated Successfully!")
                self.show_passman_menu()
            except Exception as e:
                messagebox.showerror("❌ Error", f"Failed to update: {str(e)}")
        
        btn_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=30)
        
        save_btn = self.create_modern_button(btn_frame, "💾  Save", 
                                            save_update,
                                            bg='#ff6b35', hover_color='#e55a2b')
        save_btn.pack(side='left', padx=10)
        
        back_btn = self.create_modern_button(btn_frame, "←  Back", 
                                             self.show_passman_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn.pack(side='left', padx=10)
    
    # ==================== EXPORT/IMPORT FUNCTIONS ====================
    
    def show_export_menu(self):
        """Show export options"""
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_passman_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text="📤", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_purple'])
        icon_label.pack(pady=(0, 10))
        
        title = tk.Label(self.container, text="Export Logins", 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 30))
        
        info_label = tk.Label(self.container, text="Choose export format:", 
                            font=('Segoe UI', 11),
                            bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        info_label.pack(pady=10)
        
        btn_frame = tk.Frame(self.container, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=20)
        
        # CSV Export
        def export_csv():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Export as CSV"
            )
            if not file_path:
                return
            
            try:
                # Get all data and decrypt
                data = []
                with open(self.filename, 'r') as f:
                    for line in f.readlines():
                        line = line.rstrip()
                        parts = line.split("|")
                        if len(parts) >= 2:
                            sitename = parts[0]
                            tag = "Other"
                            timestamp = ""
                            decode_line = ""
                            if len(parts) >= 4:
                                tag = parts[1]
                                decode_line = parts[2]
                                timestamp = parts[3]
                            elif len(parts) == 3:
                                if '~' in parts[1]: decode_line, timestamp = parts[1], parts[2]
                                else: tag, decode_line = parts[1], parts[2]
                            else:
                                decode_line = parts[1]
                                
                            if '~' in decode_line:
                                userpass = decode_line.split("~", 1)
                                userpass[1] = userpass[1].split('|')[0]
                                if len(userpass) == 2:
                                    decrypted_user = self.cipher.decrypt(userpass[0].encode()).decode()
                                    decrypted_pass = self.cipher.decrypt(userpass[1].encode()).decode()
                                    expiry_status = "Unknown"
                                    if timestamp:
                                        expiry_status, _, _ = get_expiry_status(timestamp)
                                    
                                    data.append({'site': sitename, 'tag': tag, 'username': decrypted_user, 
                                               'password': decrypted_pass, 'expiry': expiry_status})
                
                # Write to CSV
                with open(file_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['site', 'tag', 'username', 'password', 'expiry'])
                    writer.writeheader()
                    writer.writerows(data)
                
                messagebox.showinfo("✅ Success", f"Exported {len(data)} entries to CSV!")
                self.show_passman_menu()
                
            except Exception as e:
                messagebox.showerror("❌ Error", f"Export failed: {str(e)}")
        
        # JSON Export
        def export_json():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="Export as JSON"
            )
            if not file_path:
                return
            
            try:
                # Get all data and decrypt
                data = []
                with open(self.filename, 'r') as f:
                    for line in f.readlines():
                        line = line.rstrip()
                        parts = line.split("|")
                        if len(parts) >= 2:
                            sitename = parts[0]
                            tag = "Other"
                            timestamp = ""
                            decode_line = ""
                            if len(parts) >= 4:
                                tag = parts[1]
                                decode_line = parts[2]
                                timestamp = parts[3]
                            elif len(parts) == 3:
                                if '~' in parts[1]: decode_line, timestamp = parts[1], parts[2]
                                else: tag, decode_line = parts[1], parts[2]
                            else:
                                decode_line = parts[1]
                                
                            if '~' in decode_line:
                                userpass = decode_line.split("~", 1)
                                userpass[1] = userpass[1].split('|')[0]
                                if len(userpass) == 2:
                                    decrypted_user = self.cipher.decrypt(userpass[0].encode()).decode()
                                    decrypted_pass = self.cipher.decrypt(userpass[1].encode()).decode()
                                    
                                    data.append({'site': sitename, 'tag': tag, 'username': decrypted_user, 
                                               'password': decrypted_pass, 'timestamp': timestamp})
                
                # Write to JSON
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)
                
                messagebox.showinfo("✅ Success", f"Exported {len(data)} entries to JSON!")
                self.show_passman_menu()
                
            except Exception as e:
                messagebox.showerror("❌ Error", f"Export failed: {str(e)}")
        
        csv_btn = self.create_modern_button(btn_frame, "📄  Export as CSV", 
                                           export_csv,
                                           bg='#00f5d4', hover_color='#00c4a7')
        csv_btn.pack(side='left', padx=10)
        
        json_btn = self.create_modern_button(btn_frame, "📋  Export as JSON", 
                                             export_json,
                                             bg='#9d4edd', hover_color='#7b2cbf')
        json_btn.pack(side='left', padx=10)
        
        back_btn = self.create_modern_button(self.container, "←  Back", 
                                             self.show_passman_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn.pack(pady=20)
    
    def show_import_menu(self):
        """Show import options"""
        self.clear_frame()
        
        # Back button
        back_btn = tk.Button(self.container, text="← Back", width=20,
                           font=('Segoe UI', 10), bg=self.colors['bg_medium'], fg=self.colors['text_gray'],
                           relief='flat', bd=0, cursor='hand2',
                           command=self.show_passman_menu)
        back_btn.pack(anchor="nw", padx=10, pady=10)
        
        # Header
        header = tk.Frame(self.container, bg=self.colors['bg_medium'])
        header.pack(pady=(40, 20))
        
        icon_label = tk.Label(header, text="📥", font=('Segoe UI', 40), 
                            bg=self.colors['bg_medium'], fg=self.colors['accent_blue'])
        icon_label.pack(pady=(0, 10))
        
        title = tk.Label(self.container, text="Import Logins", 
                        font=('Segoe UI', 20, 'bold'),
                        bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        title.pack(pady=(0, 30))
        
        info_label = tk.Label(self.container, text="Select file to import (CSV or JSON):", 
                            font=('Segoe UI', 11),
                            bg=self.colors['bg_medium'], fg=self.colors['text_white'])
        info_label.pack(pady=10)
        
        def import_file():
            file_path = filedialog.askopenfilename(
                filetypes=[("All supported files", "*.csv *.json"), 
                          ("CSV files", "*.csv"),
                          ("JSON files", "*.json")],
                title="Import Logins"
            )
            if not file_path:
                return
            
            try:
                # Detect format
                if file_path.endswith('.csv'):
                    # Import from CSV
                    imported_count = 0
                    with open(file_path, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            site = row.get('site', row.get('Site', ''))
                            username = row.get('username', row.get('Username', row.get('user', '')))
                            password = row.get('password', row.get('Password', row.get('pass', '')))
                            
                            if site and username and password:
                                # Encrypt and save
                                encrypted_user = self.cipher.encrypt(username.encode()).decode()
                                encrypted_pass = self.cipher.encrypt(password.encode()).decode()
                                with open(self.filename, 'a') as f:
                                    f.write(site + "|" + encrypted_user + "~" + encrypted_pass + "\n")
                                imported_count += 1
                    
                    messagebox.showinfo("✅ Success", f"Imported {imported_count} entries from CSV!")
                
                elif file_path.endswith('.json'):
                    # Import from JSON
                    imported_count = 0
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        for item in data:
                            site = item.get('site', item.get('Site', ''))
                            username = item.get('username', item.get('Username', item.get('user', '')))
                            password = item.get('password', item.get('Password', item.get('pass', '')))
                            
                            if site and username and password:
                                # Encrypt and save
                                encrypted_user = self.cipher.encrypt(username.encode()).decode()
                                encrypted_pass = self.cipher.encrypt(password.encode()).decode()
                                with open(self.filename, 'a') as f:
                                    f.write(site + "|" + encrypted_user + "~" + encrypted_pass + "\n")
                                imported_count += 1
                    
                    messagebox.showinfo("✅ Success", f"Imported {imported_count} entries from JSON!")
                
                self.show_passman_menu()
                
            except Exception as e:
                messagebox.showerror("❌ Error", f"Import failed: {str(e)}")
        
        import_btn = self.create_modern_button(self.container, "📂  Select File", 
                                               import_file,
                                               bg='#00d9ff', hover_color='#00b8d9')
        import_btn.pack(pady=20)
        
        back_btn = self.create_modern_button(self.container, "←  Back", 
                                             self.show_passman_menu,
                                             bg='#6c757d', hover_color='#5a6268')
        back_btn.pack(pady=20)
    
    def exit_app(self):
        """Exit the application"""
        if messagebox.askyesno("🚪 Exit", "Are you sure you want to exit?"):
            self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = PassmanGUI(root)
    root.mainloop()