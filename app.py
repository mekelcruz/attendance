import sys
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QFrame,
    QMessageBox, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QDateEdit, QFileDialog, QCheckBox
)
from PyQt5.QtGui import QFont, QPixmap, QPalette, QBrush, QIcon
from PyQt5.QtCore import Qt, QTimer, QTime, QSize, QDateTime, QDate
import csv
from PyQt5.QtGui import QIcon

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    path = os.path.join(base_path, relative_path)
    
    # Verify the file exists
    if not os.path.exists(path):
        print(f"Warning: Resource not found at {path}")
        return None
    
    return path

def get_persistent_db_path():
    """Get a persistent database path that works across platforms"""
    if sys.platform == "win32":
        # On Windows, use AppData/Local
        base_path = os.getenv('LOCALAPPDATA')
        app_path = os.path.join(base_path, "AttendanceSystem")
    else:
        # On Linux/Mac, use home directory
        base_path = os.path.expanduser("~")
        app_path = os.path.join(base_path, ".attendance_system")
    
    # Create directory if it doesn't exist
    os.makedirs(app_path, exist_ok=True)
    
    return os.path.join(app_path, "attendance.db")

def load_pixmap(image_path):
    """Safely load a pixmap with error handling"""
    path = resource_path(image_path)
    if path is None:
        return QPixmap()
    
    pixmap = QPixmap(path)
    if pixmap.isNull():
        print(f"Warning: Could not load image from {path}")
    return pixmap

def load_icon(icon_path, size=None):
    """Safely load an icon with error handling"""
    path = resource_path(icon_path)
    if path is None:
        return QIcon()
    
    icon = QIcon(path)
    if icon.isNull():
        print(f"Warning: Could not load icon from {path}")
    
    if size:
        icon.actualSize(QSize(size, size))
    return icon

class AdminWindow(QWidget):
    def __init__(self, db_conn):
        super().__init__()
        self.conn = db_conn
        self.cursor = self.conn.cursor()
        self.setWindowIcon(load_icon("Batangas_State_Logo.png"))
        self.setWindowTitle("Admin Dashboard - Attendance Logs")
        self.setGeometry(100, 100, 1000, 600)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Add refresh controls at the top
        refresh_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedWidth(100)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        refresh_layout.addWidget(self.refresh_btn)
        
        # Auto-refresh toggle
        self.auto_refresh_check = QCheckBox("Auto-refresh (10 sec)")
        self.auto_refresh_check.stateChanged.connect(self.toggle_auto_refresh)
        refresh_layout.addWidget(self.auto_refresh_check)
        
        refresh_layout.addStretch()
        self.layout.addLayout(refresh_layout)

        self.title = QLabel("Attendance Logs")
        self.title.setFont(QFont("Arial", 18, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title)

        # Table setup
        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        # Filter controls layout
        filter_layout = QHBoxLayout()

        # Daily filter
        filter_layout.addWidget(QLabel("Daily Filter:"))
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setDisplayFormat("yyyy-MM-dd")
        self.date_filter.dateChanged.connect(self.load_daily_attendance)
        filter_layout.addWidget(self.date_filter)

        # Monthly filter
        filter_layout.addWidget(QLabel("Monthly Filter:"))
        
        self.month_combo = QComboBox()
        self.month_combo.addItems(["January", "February", "March", "April", "May", "June", 
                                 "July", "August", "September", "October", "November", "December"])
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
        filter_layout.addWidget(self.month_combo)
        
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(QDate.currentDate().year())
        filter_layout.addWidget(self.year_spin)
        
        self.monthly_export_btn = QPushButton("Export Monthly Data")
        self.monthly_export_btn.setFixedWidth(200)
        self.monthly_export_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.monthly_export_btn.clicked.connect(self.export_monthly_data)
        filter_layout.addWidget(self.monthly_export_btn)

        self.layout.addLayout(filter_layout)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Buttons
        self.import_students_btn = QPushButton("Import Students CSV")
        self.download_attendance_btn = QPushButton("Export Daily CSV")
        self.download_template_btn = QPushButton("Download Template")

        # Style and size
        self.import_students_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.import_students_btn.setFixedWidth(200)

        for btn in [self.download_attendance_btn, self.download_template_btn]:
            btn.setFixedWidth(200)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    padding: 10px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)

        # Connect buttons to functions
        self.import_students_btn.clicked.connect(self.import_students)
        self.download_attendance_btn.clicked.connect(self.download_csv)
        self.download_template_btn.clicked.connect(self.download_template)

        # Add to layout
        buttons_layout.addWidget(self.import_students_btn)
        buttons_layout.addWidget(self.download_attendance_btn)
        buttons_layout.addWidget(self.download_template_btn)
        self.layout.addLayout(buttons_layout)

        # Setup auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.auto_refresh_interval = 10000  # 10 seconds

        # Load initial data
        self.load_daily_attendance()

    def refresh_data(self):
        """Refresh the current view (daily or monthly)"""
        if self.date_filter.isEnabled():  # If daily view is active
            self.load_daily_attendance()
        else:  # Monthly view is active
            month = self.month_combo.currentIndex() + 1
            year = self.year_spin.value()
            self.load_monthly_attendance(month, year)

    def toggle_auto_refresh(self, state):
        """Toggle auto-refresh timer based on checkbox state"""
        if state == Qt.Checked:
            self.refresh_timer.start(self.auto_refresh_interval)
        else:
            self.refresh_timer.stop()

    def load_daily_attendance(self):
        """Load attendance data for the selected date"""
        selected_date = self.date_filter.date().toString("yyyy-MM-dd")
        try:
            query = """
                SELECT 
                    t.sr_code,
                    n.full_name,
                    n.College,
                    n.PROGRAM,
                    strftime('%I:%M:%S %p', t.time_in) AS time_in_12hr
                FROM 
                    time_tbl t
                JOIN 
                    name_tbl n ON t.sr_code = n.sr_code
                WHERE 
                    date(t.date_in) = ?
                ORDER BY 
                    t.time_in DESC;
            """
            
            self.cursor.execute(query, (selected_date,))
            self.records = self.cursor.fetchall()

            self.table.setRowCount(len(self.records))
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels([
                "SR Code", "Full Name", "College", "Program", "Time-In (AM/PM)"  # Updated header
            ])

            for row_idx, row_data in enumerate(self.records):
                for col_idx, col_data in enumerate(row_data):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load daily data:\n{e}")

    def load_monthly_attendance(self, month, year):
        """Load attendance data for a specific month and year"""
        try:
            query = """
                SELECT 
                    date(date_in) AS date,
                    t.sr_code,
                    n.full_name,
                    n.College,
                    n.PROGRAM,
                    strftime('%I:%M:%S %p', time_in) AS time_in_12hr
                FROM 
                    time_tbl t
                JOIN 
                    name_tbl n ON t.sr_code = n.sr_code
                WHERE 
                    strftime('%m', date_in) = ? AND
                    strftime('%Y', date_in) = ?
                ORDER BY 
                    t.date_in DESC;
            """
            month_str = f"{month:02d}"
            year_str = str(year)
            
            self.cursor.execute(query, (month_str, year_str))
            self.records = self.cursor.fetchall()

            self.table.setRowCount(len(self.records))
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels([
                "Date", "SR Code", "Full Name", "College", "Program", "Time-In (AM/PM)"  # Updated header
            ])

            for row_idx, row_data in enumerate(self.records):
                for col_idx, col_data in enumerate(row_data):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load monthly data:\n{e}")

    def export_monthly_data(self):
        """Export data for the selected month and year"""
        month = self.month_combo.currentIndex() + 1  # Months are 1-12
        year = self.year_spin.value()
        
        # First load the data to verify there's something to export
        self.load_monthly_attendance(month, year)
        
        if not hasattr(self, "records") or not self.records:
            QMessageBox.warning(self, "No Data", f"No attendance data found for {self.month_combo.currentText()} {year}")
            return
            
        # Suggest a filename with the month and year
        default_filename = f"Attendance_{self.month_combo.currentText()}_{year}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Monthly Attendance CSV", 
            default_filename, 
            "CSV Files (*.csv)"
        )
        
        if not path:
            return

        try:
            with open(path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "SR Code", "Full Name", "College", "Program", "Time-In"])
                writer.writerows(self.records)

            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Monthly attendance data for {self.month_combo.currentText()} {year} has been saved successfully."
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save monthly CSV:\n{e}")

    def import_students(self):
        """Import students from CSV file"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Students CSV", 
            "", 
            "CSV Files (*.csv)"
        )
        
        if not path:
            return

        try:
            with open(path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row
                
                # Prepare batch insert
                data = []
                for row in reader:
                    if len(row) >= 5:  # Ensure we have all required columns
                        data.append((row[0], row[1], row[2], row[3], row[4]))
                
                # Insert in batch
                self.cursor.executemany(
                    "INSERT OR REPLACE INTO name_tbl (sr_code, full_name, College, PROGRAM, CAMPUS) VALUES (?, ?, ?, ?, ?)",
                    data
                )
                self.conn.commit()
                
                QMessageBox.information(
                    self, 
                    "Import Successful", 
                    f"Successfully imported {len(data)} student records."
                )
                
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Import Error", f"Failed to import students:\n{e}")

    def download_csv(self):
        """Export daily attendance data to CSV"""
        selected_date = self.date_filter.date().toString("yyyy-MM-dd")
        
        # First load the data to verify there's something to export
        self.load_daily_attendance()
        
        if not hasattr(self, "records") or not self.records:
            QMessageBox.warning(self, "No Data", f"No attendance data found for {selected_date}")
            return
            
        # Suggest a filename with the date
        default_filename = f"Attendance_{selected_date}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Daily Attendance CSV", 
            default_filename, 
            "CSV Files (*.csv)"
        )
        
        if not path:
            return

        try:
            with open(path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["SR Code", "Full Name", "College", "Program", "Time-In"])
                writer.writerows(self.records)

            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Daily attendance data for {selected_date} has been saved successfully."
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save daily CSV:\n{e}")

    def download_template(self):
        """Download a template CSV for student imports"""
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Template CSV", 
            "Student_Import_Template.csv", 
            "CSV Files (*.csv)"
        )
        
        if not path:
            return

        try:
            with open(path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["SR Code", "Full Name", "College", "Program", "Campus"])
                writer.writerow(["21-07343", "Cruz, Mykel Aris B", "CICS", "BSIT", "Alangilan"])

            QMessageBox.information(
                self, 
                "Template Downloaded", 
                "Student import template has been saved successfully."
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save template:\n{e}")

class LoginPage(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.background_pixmap = load_pixmap("ATTENDANCE.png")
        self.setWindowTitle("Admin Login")
        self.setAutoFillBackground(True)
        self.init_ui()
        self.setWindowIcon(load_icon("Batangas_State_Logo.png"))
    def resizeEvent(self, event):
        if not self.background_pixmap.isNull():
            scaled = self.background_pixmap.scaled(
                self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
            )
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(scaled))
            self.setPalette(palette)
        super().resizeEvent(event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Admin Login")
        title.setFont(QFont("Times New Roman", 24, QFont.Bold))
        title.setStyleSheet("color: black;")
        title.setAlignment(Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(300)
        self.username_input.setFont(QFont("Times New Roman", 14))
        self.username_input.setStyleSheet("padding: 10px;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(300)
        self.password_input.setFont(QFont("Times New Roman", 14))
        self.password_input.setStyleSheet("padding: 10px;")

        login_btn = QPushButton("Login")
        login_btn.setFont(QFont("Times New Roman", 14, QFont.Bold))
        login_btn.setFixedWidth(150)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #d90012;
                color: white;
                padding: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #a8000f;
            }
        """)
        login_btn.clicked.connect(self.validate_login)

        self.username_input.returnPressed.connect(self.validate_login)
        self.password_input.returnPressed.connect(self.validate_login)

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addSpacing(20)
        layout.addWidget(login_btn, alignment=Qt.AlignCenter)

    def validate_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if username == "admin" and password == "library123":
            self.open_admin_window()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

    def open_admin_window(self):
        self.admin_window = AdminWindow(self.conn)
        self.admin_window.show()
        self.close()

class AttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.background_pixmap = QPixmap()
        self.setWindowTitle("Attendance System")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint |
                          Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.showMaximized()
        self.setAutoFillBackground(True)
        self.setWindowIcon(load_icon("Batangas_State_Logo.png"))
        self.connect_db()
        self.set_background_image("ATTENDANCE.png")
        self.init_ui()
        self.setup_timer()

    def set_background_image(self, image_path):
        self.background_pixmap = load_pixmap(image_path)
        if self.background_pixmap.isNull():
            print(f"Warning: Could not load background image from '{image_path}'")
            # Set a default background color if image fails to load
            palette = self.palette()
            palette.setColor(QPalette.Window, Qt.white)
            self.setPalette(palette)

    def resizeEvent(self, event):
        if not self.background_pixmap.isNull():
            scaled = self.background_pixmap.scaled(
                self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
            )
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(scaled))
            self.setPalette(palette)
        super().resizeEvent(event)

    def connect_db(self):
        try:
            # Get persistent database path
            db_path = get_persistent_db_path()
            
            # Create database if it doesn't exist
            if not os.path.exists(db_path):
                self.create_database(db_path)
                
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not connect to database:\n{e}")
            sys.exit()

    def create_database(self, db_path):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create name_tbl
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS name_tbl (
            sr_code TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            College TEXT,
            PROGRAM TEXT,
            CAMPUS TEXT
        )
        """)
        
        # Create time_tbl
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_tbl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sr_code TEXT NOT NULL,
            time_in TEXT NOT NULL,
            date_in TEXT NOT NULL,
            FOREIGN KEY (sr_code) REFERENCES name_tbl(sr_code)
        )
        """)
        
        # Create admin_tbl
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_tbl (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
        """)
        
        # Insert default admin if not exists
        cursor.execute("""
        INSERT OR IGNORE INTO admin_tbl (username, password)
        VALUES ('admin', 'library123')
        """)
        
        conn.commit()
        conn.close()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        # Get current Philippine time (UTC+8)
        utc_time = QDateTime.currentDateTimeUtc()
        ph_time = utc_time.addSecs(8 * 3600)  # Add 8 hours for Philippine Time
        self.time_label.setText(ph_time.toString("h:mm:ss AP"))

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #d90012;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(10)

        # Logo
        logo_label = QLabel()
        logo_pixmap = load_pixmap("Batangas_State_Logo.png")
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # University text
        uni_name = QLabel("BATANGAS STATE UNIVERSITY")
        uni_name.setFont(QFont("Times New Roman", 24, QFont.Bold))
        uni_name.setStyleSheet("color: white;")
        uni_name.setAlignment(Qt.AlignLeft)

        uni_subtitle = QLabel("THE NATIONAL ENGINEERING UNIVERSITY")
        uni_subtitle.setFont(QFont("Times New Roman", 14))
        uni_subtitle.setStyleSheet("color: white;")
        uni_subtitle.setAlignment(Qt.AlignHCenter)

        uni_text_layout = QVBoxLayout()
        uni_text_layout.setContentsMargins(0, 25, 0, 0)
        uni_text_layout.setSpacing(0)
        uni_text_layout.addWidget(uni_name)
        uni_text_layout.addWidget(uni_subtitle)

        uni_text_widget = QWidget()
        uni_text_widget.setLayout(uni_text_layout)

        logo_and_text_layout = QHBoxLayout()
        logo_and_text_layout.setSpacing(10)
        logo_and_text_layout.addWidget(logo_label)
        logo_and_text_layout.addWidget(uni_text_widget)

        logo_and_text_widget = QWidget()
        logo_and_text_widget.setLayout(logo_and_text_layout)

        header_layout.addWidget(logo_and_text_widget, alignment=Qt.AlignLeft | Qt.AlignTop)
        header_layout.addStretch()
        main_layout.addWidget(header)

        # Center content
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(40)
        main_layout.addLayout(center_layout, stretch=1)

        # SR Code input
        sr_frame = QFrame()
        sr_frame.setStyleSheet("background-color: transparent; border: none;")
        sr_frame.setFixedSize(500, 250)

        sr_layout = QVBoxLayout(sr_frame)
        sr_layout.setAlignment(Qt.AlignCenter)
        sr_layout.setSpacing(20)

        sr_title = QLabel("SR-CODE:")
        sr_title.setFont(QFont("Times New Roman", 24, QFont.Bold))
        sr_title.setStyleSheet("color: black;")
        sr_title.setAlignment(Qt.AlignCenter)
        sr_layout.addWidget(sr_title)

        self.sr_input = QLineEdit()
        self.sr_input.setPlaceholderText("Enter your SR CODE")
        self.sr_input.setStyleSheet("""
            padding: 15px;
            border: none;
            border-bottom: 3px solid #000000;
            font-size: 30px;
            font-family: Times New Roman;
            background-color: transparent;
        """)
        self.sr_input.setFixedWidth(500)
        self.sr_input.setAlignment(Qt.AlignHCenter)
        self.sr_input.returnPressed.connect(self.mark_attendance)
        sr_layout.addWidget(self.sr_input)

        self.status_label = QLabel("Attendance Check")
        self.status_label.setFont(QFont("Times New Roman", 10))
        self.status_label.setStyleSheet("color: black; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignHCenter)
        sr_layout.addWidget(self.status_label)

        center_layout.addWidget(sr_frame)

        # Bottom bar
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(20, 20, 20, 20)

        self.time_label = QLabel()
        self.time_label.setFont(QFont("Times New Roman", 20, QFont.Bold))
        self.time_label.setStyleSheet("""
            background-color: #d90012;
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
        """)
        self.time_label.setAlignment(Qt.AlignCenter)

        self.admin_btn = QPushButton()
        settings_icon = load_icon("settings.png", 50)
        if not settings_icon.isNull():
            self.admin_btn.setIcon(settings_icon)
        self.admin_btn.setIconSize(QSize(50, 50))
        self.admin_btn.setFixedSize(70, 70)
        self.admin_btn.setStyleSheet("""
            QPushButton {
                background-color: #d90012;
                border-radius: 35px;
            }
            QPushButton:hover {
                background-color: #a8000f;
            }
        """)
        self.admin_btn.setToolTip("Admin Settings")
        self.admin_btn.clicked.connect(self.open_admin)

        bottom_layout.addWidget(self.time_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.admin_btn)

        main_layout.addLayout(bottom_layout)

    def open_admin(self):
        self.login_page = LoginPage(self.conn)
        self.login_page.setGeometry(self.geometry())
        self.login_page.show()

    def mark_attendance(self):
        sr_code = self.sr_input.text().strip()
        if not sr_code:
            QMessageBox.warning(self, "Input Error", "Please enter your SR CODE.")
            return

        try:
            # Get current Philippine time (UTC+8)
            utc_now = datetime.now(timezone.utc)
            ph_time = utc_now + timedelta(hours=8)  # Convert to Philippine Time
            time_str = ph_time.strftime('%Y-%m-%d %H:%M:%S')
            date_str = ph_time.strftime('%Y-%m-%d')

            self.cursor.execute('SELECT full_name FROM name_tbl WHERE sr_code = ?', (sr_code,))
            result = self.cursor.fetchone()

            if not result:
                QMessageBox.warning(self, "Not Found", "SR CODE not found in the records.")
                return

            full_name = result[0]

            try:
                # Insert with explicit Philippine time
                self.cursor.execute('INSERT INTO time_tbl (sr_code, time_in, date_in) VALUES (?, ?, ?)', 
                                   (sr_code, time_str, date_str))
                self.conn.commit()

                self.status_label.setText(
                    f"<b>{full_name.upper()} ({sr_code})</b>"
                )
                self.sr_input.clear()
                self.sr_input.setFocus()

                # Clear the status_label after 5 seconds (5000 milliseconds)
                QTimer.singleShot(2000, lambda: self.status_label.setText(""))

            except Exception as insert_error:
                self.conn.rollback()
                QMessageBox.critical(self, "Insert Error", f"Could not mark attendance:\n{insert_error}")

        except Exception as query_error:
            self.conn.rollback()
            QMessageBox.critical(self, "Database Error", f"Error while checking SR CODE:\n{query_error}")

    def closeEvent(self, event):
        if hasattr(self, 'conn'):
            self.cursor.close()
            self.conn.close()
        event.accept()

if __name__ == "__main__":
    # Verify all required resources exist (except database which we'll handle specially)
    required_resources = [
        "ATTENDANCE.png",
        "Batangas_State_Logo.png",
        "settings.png"
    ]
    
    missing_resources = [res for res in required_resources if not os.path.exists(resource_path(res))]
    if missing_resources:
        print(f"Warning: Missing resources - {', '.join(missing_resources)}")
    
    app = QApplication(sys.argv)
    window = AttendanceApp()
    window.show()
    sys.exit(app.exec_())