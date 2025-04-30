import sys
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFrame, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QTime


class AttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attendance System")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint |
                            Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.showMaximized()
        self.init_ui()
        self.connect_db()
        self.setup_timer()

    def connect_db(self):
        try:
            self.conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="1234",
                host="localhost",
                port="5432"
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not connect to database:\n{e}")
            sys.exit()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        current_time = QTime.currentTime()
        self.time_label.setText(current_time.toString("h:mm:ss AP"))

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setStyleSheet("background-color: white;")

        header = QFrame()
        header.setStyleSheet("background-color: #d90012;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(20)

        logo_label = QLabel()
        logo_pixmap = QPixmap("Batangas_State_Logo.png").scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        uni_name = QLabel("BATANGAS STATE UNIVERSITY")
        uni_name.setFont(QFont("Times New Roman", 24, QFont.Bold))
        uni_name.setStyleSheet("color: white;")
        uni_name.setAlignment(Qt.AlignLeft)

        uni_subtitle = QLabel("THE NATIONAL ENGINEERING UNIVERSITY")
        uni_subtitle.setFont(QFont("Times New Roman", 14))
        uni_subtitle.setStyleSheet("color: white;")
        uni_subtitle.setAlignment(Qt.AlignLeft)

        uni_text_layout = QVBoxLayout()
        uni_text_layout.setContentsMargins(0, 0, 0, 0)
        uni_text_layout.setSpacing(5)
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

        self.time_label = QLabel()
        self.time_label.setFont(QFont("Times New Roman", 18, QFont.Bold))
        self.time_label.setStyleSheet("color: white;")
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        header_layout.addWidget(self.time_label, alignment=Qt.AlignTop)

        main_layout.addWidget(header)

        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(40)
        main_layout.addLayout(center_layout, stretch=1)

        sr_frame = QFrame()
        sr_frame.setStyleSheet("background-color: rgba(255, 255, 255, 0.9); border-radius: 10px; border: 2px solid #0056b3;")
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
            padding: 12px;
            border-radius: 5px;
            border: 2px solid #0056b3;
            font-size: 18px;
            font-family: Times New Roman;
        """)
        self.sr_input.setFixedWidth(350)
        self.sr_input.setAlignment(Qt.AlignCenter)
        sr_layout.addWidget(self.sr_input)

        mark_button = QPushButton("Mark Attendance")
        mark_button.setFont(QFont("Times New Roman", 14))
        mark_button.setStyleSheet("""
            QPushButton {
                background-color: #d90012;
                color: white;
                padding: 10px 25px;
                border-radius: 5px;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8f000c;
            }
        """)
        mark_button.clicked.connect(self.mark_attendance)
        sr_layout.addWidget(mark_button, alignment=Qt.AlignCenter)

        self.status_label = QLabel("[Note: Attendance]")
        self.status_label.setFont(QFont("Times New Roman", 14))
        self.status_label.setStyleSheet("color: black; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignCenter)
        sr_layout.addWidget(self.status_label)

        center_layout.addWidget(sr_frame)
        main_layout.addStretch(1)

    def mark_attendance(self):
        sr_code = self.sr_input.text().strip()
        if not sr_code:
            QMessageBox.warning(self, "Input Error", "Please enter your SR CODE.")
            return

        try:
            self.cursor.execute('SELECT full_name FROM name_tbl WHERE sr_code = %s', (sr_code,))
            result = self.cursor.fetchone()

            if not result:
                QMessageBox.warning(self, "Not Found", "SR CODE not found in the records.")
                return

            full_name = result[0]

            try:
                self.cursor.execute('INSERT INTO time_tbl ("sr_code") VALUES (%s)', (sr_code,))
                self.conn.commit()
                self.status_label.setText(f"Attendance marked for: {full_name.upper()} ({sr_code})")
                self.sr_input.clear()

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
    app = QApplication(sys.argv)
    window = AttendanceApp()
    window.show()
    sys.exit(app.exec_())