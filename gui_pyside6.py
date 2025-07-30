"""
现代化的PySide6用户界面模块
支持文件拖放、更合理的UI结构和现代化设计
"""
import sys
import os
from pathlib import Path
from typing import List, Optional
import threading

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox, QSlider,
    QProgressBar, QTextEdit, QGroupBox, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QFrame, QSpacerItem, QSizePolicy, QTabWidget, QScrollArea,
    QAbstractItemView, QSpinBox, QRadioButton
)
from PySide6.QtCore import (
    Qt, QThread, QObject, Signal, QTimer, QMimeData, QUrl, QSize
)
from PySide6.QtGui import (
    QFont, QPalette, QColor, QIcon, QPixmap, QDragEnterEvent, 
    QDropEvent, QPainter, QLinearGradient, QIntValidator
)

from image_processor import ImageProcessor, ResizeMode
from file_manager import FileManager


class DragDropTableWidget(QTableWidget):
    """支持拖放的表格控件"""
    files_dropped = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("""
                QTableWidget {
                    border: 2px dashed #007ACC;
                    background-color: #f0f8ff;
                }
            """)
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self.setStyleSheet("")
        
    def dropEvent(self, event):
        """拖拽放下事件"""
        self.setStyleSheet("")
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.isfile(file_path):
                        # 检查是否为图片文件
                        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')):
                            files.append(file_path)
                    elif os.path.isdir(file_path):
                        # 如果是文件夹，递归获取所有图片文件
                        for root, dirs, filenames in os.walk(file_path):
                            for filename in filenames:
                                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')):
                                    files.append(os.path.join(root, filename))
            
            if files:
                self.files_dropped.emit(files)
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()


class DragDropWidget(QWidget):
    """支持拖放的自定义Widget"""
    
    files_dropped = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        """设置拖放区域UI"""
        self.setMinimumHeight(120)
        self.setStyleSheet("""
            DragDropWidget {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f8f9fa;
                color: #666;
            }
            DragDropWidget:hover {
                border-color: #007acc;
                background-color: #e3f2fd;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # 图标标签
        icon_label = QLabel("📁")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 32px; border: none;")
        
        # 提示文字
        text_label = QLabel("拖放图片文件到此处\n或点击下方按钮选择文件")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 14px; color: #666; border: none;")
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("""
                DragDropWidget {
                    border: 2px solid #007acc;
                    border-radius: 10px;
                    background-color: #e3f2fd;
                    color: #007acc;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self.setStyleSheet("""
            DragDropWidget {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f8f9fa;
                color: #666;
            }
            DragDropWidget:hover {
                border-color: #007acc;
                background-color: #e3f2fd;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        """拖放事件"""
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
                elif os.path.isdir(file_path):
                    # 如果是文件夹，获取其中的图片文件
                    for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
                        files.extend(Path(file_path).glob(f'*{ext}'))
                        files.extend(Path(file_path).glob(f'*{ext.upper()}'))
        
        if files:
            self.files_dropped.emit([str(f) for f in files])
        
        # 恢复样式
        self.dragLeaveEvent(event)
        event.accept()


class ProcessingThread(QThread):
    """图片处理线程"""
    
    progress_updated = Signal(float, str, bool)
    processing_finished = Signal(dict)
    
    def __init__(self, processor, files, output_dir, target_size, mode, quality):
        super().__init__()
        self.processor = processor
        self.files = files
        self.output_dir = output_dir
        self.target_size = target_size
        self.mode = mode
        self.quality = quality
    
    def run(self):
        """运行处理任务"""
        result = self.processor.batch_process(
            self.files,
            self.output_dir,
            self.target_size,
            self.mode,
            self.quality,
            self.progress_updated.emit
        )
        self.processing_finished.emit(result)


class ModernImageResizerGUI(QMainWindow):
    """现代化的图片尺寸调整器GUI"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("批量图片尺寸调整工具 - PySide6版")
        self.setMinimumSize(1000, 700)
        
        # 初始化组件
        self.image_processor = ImageProcessor()
        self.file_manager = FileManager()
        self.selected_files = []
        self.output_directory = ""
        self.processing_thread = None
        
        self.setup_ui()
        self.setup_styles()
        self.setup_connections()
    
    def setup_styles(self):
        """设置应用程序样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #333;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
            QPushButton#primaryButton {
                background-color: #28a745;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton#primaryButton:hover {
                background-color: #218838;
            }
            QPushButton#dangerButton {
                background-color: #dc3545;
            }
            QPushButton#dangerButton:hover {
                background-color: #c82333;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #007acc;
            }
            QSlider::groove:horizontal {
                border: 1px solid #ddd;
                height: 8px;
                background: #f0f0f0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #007acc;
                border: 1px solid #005a9e;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #005a9e;
            }
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #333;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #ddd;
                font-weight: bold;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 6px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
    
    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([600, 400])
        
        # 底部进度条区域
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 10, 0, 0)
        progress_layout.setSpacing(5)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 6px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 4px;
            }
        """)
        
        progress_layout.addWidget(self.progress_bar)
        main_layout.addWidget(progress_container)
    
    def create_left_panel(self):
        """创建左侧面板 - 文件列表"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.StyledPanel)
        widget.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # 文件操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.select_files_btn = QPushButton("选择文件")
        self.select_files_btn.setMinimumHeight(45)
        self.select_files_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
                background-color: #4a90e2;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2968a3;
            }
        """)
        
        self.select_folder_btn = QPushButton("选择文件夹")
        self.select_folder_btn.setMinimumHeight(45)
        self.select_folder_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
                background-color: #5cb85c;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #449d44;
            }
            QPushButton:pressed {
                background-color: #398439;
            }
        """)
        
        self.clear_files_btn = QPushButton("清空列表")
        self.clear_files_btn.setMinimumHeight(45)
        self.clear_files_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
                background-color: #d9534f;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
            QPushButton:pressed {
                background-color: #ac2925;
            }
        """)
        
        button_layout.addWidget(self.select_files_btn)
        button_layout.addWidget(self.select_folder_btn)
        button_layout.addWidget(self.clear_files_btn)
        
        layout.addLayout(button_layout)
        
        # 文件列表
        self.file_table = DragDropTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["文件名", "原始尺寸", "目标尺寸", "文件大小"])
        
        # 设置列宽
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.file_table)
        
        return widget
    
    def create_right_panel(self):
        """创建右侧面板 - 参数设置和控制"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.StyledPanel)
        widget.setStyleSheet("QFrame { background-color: white; border-radius: 8px; }")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(25)
        
        # 标题
        title_label = QLabel("参数设置")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # 尺寸设置
        size_container = QWidget()
        size_layout = QVBoxLayout(size_container)
        size_layout.setSpacing(15)
        
        # 宽度设置
        width_container = QWidget()
        width_layout = QHBoxLayout(width_container)
        width_layout.setContentsMargins(0, 0, 0, 0)
        
        width_label = QLabel("宽度:")
        width_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #555; }")
        width_label.setAlignment(Qt.AlignCenter)
        
        self.width_input = QLineEdit()
        self.width_input.setText("800")
        self.width_input.setValidator(QIntValidator(1, 10000))
        self.width_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
        """)
        self.width_input.setAlignment(Qt.AlignCenter)
        
        width_px_label = QLabel("px")
        width_px_label.setStyleSheet("QLabel { font-size: 16px; color: #777; }")
        
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_input)
        width_layout.addWidget(width_px_label)
        size_layout.addWidget(width_container)
        
        # 高度设置
        height_container = QWidget()
        height_layout = QHBoxLayout(height_container)
        height_layout.setContentsMargins(0, 0, 0, 0)
        
        height_label = QLabel("高度:")
        height_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #555; }")
        height_label.setAlignment(Qt.AlignCenter)
        
        self.height_input = QLineEdit()
        self.height_input.setText("600")
        self.height_input.setValidator(QIntValidator(1, 10000))
        self.height_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
        """)
        self.height_input.setAlignment(Qt.AlignCenter)
        
        height_px_label = QLabel("px")
        height_px_label.setStyleSheet("QLabel { font-size: 16px; color: #777; }")
        
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_input)
        height_layout.addWidget(height_px_label)
        size_layout.addWidget(height_container)
        
        # 调整模式
        mode_container = QWidget()
        mode_layout = QVBoxLayout(mode_container)
        mode_layout.setSpacing(10)
        
        mode_label = QLabel("调整模式:")
        mode_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #555; }")
        mode_label.setAlignment(Qt.AlignCenter)
        
        # 单选按钮组
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(20)
        
        self.stretch_radio = QRadioButton("拉伸")
        self.keep_ratio_radio = QRadioButton("保持比例")
        self.crop_radio = QRadioButton("裁剪")
        
        # 默认选择"保持比例"
        self.keep_ratio_radio.setChecked(True)
        
        # 设置单选按钮样式
        radio_style = """
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #555;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #ddd;
                border-radius: 9px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #4a90e2;
                border-radius: 9px;
                background-color: #4a90e2;
            }
            QRadioButton::indicator:checked:hover {
                background-color: #357abd;
            }
        """
        
        self.stretch_radio.setStyleSheet(radio_style)
        self.keep_ratio_radio.setStyleSheet(radio_style)
        self.crop_radio.setStyleSheet(radio_style)
        
        radio_layout.addWidget(self.stretch_radio)
        radio_layout.addWidget(self.keep_ratio_radio)
        radio_layout.addWidget(self.crop_radio)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addLayout(radio_layout)
        size_layout.addWidget(mode_container)
        
        layout.addWidget(size_container)
        
        # 输出目录设置
        output_container = QWidget()
        output_layout = QVBoxLayout(output_container)
        output_layout.setSpacing(10)
        
        output_label = QLabel("输出目录")
        output_label.setAlignment(Qt.AlignCenter)
        output_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #555; }")
        
        dir_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("选择输出目录...")
        self.output_dir_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
        """)
        
        self.select_output_btn = QPushButton("浏览")
        self.select_output_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 6px;
                background-color: #6c757d;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        dir_layout.addWidget(self.output_dir_input)
        dir_layout.addWidget(self.select_output_btn)
        
        output_layout.addWidget(output_label)
        output_layout.addLayout(dir_layout)
        layout.addWidget(output_container)
        
        # 质量设置
        quality_container = QWidget()
        quality_layout = QVBoxLayout(quality_container)
        quality_layout.setSpacing(10)
        
        quality_label = QLabel("图片质量")
        quality_label.setAlignment(Qt.AlignCenter)
        quality_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #555; }")
        
        slider_layout = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 10px;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #4a90e2;
                border: 1px solid #777;
                height: 10px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4a90e2;
                border: 1px solid #777;
                width: 18px;
                margin-top: -2px;
                margin-bottom: -2px;
                border-radius: 3px;
            }
        """)
        
        self.quality_label = QLabel("85%")
        self.quality_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #4a90e2; }")
        self.quality_label.setAlignment(Qt.AlignCenter)
        self.quality_label.setMinimumWidth(50)
        
        slider_layout.addWidget(self.quality_slider)
        slider_layout.addWidget(self.quality_label)
        
        quality_layout.addWidget(quality_label)
        quality_layout.addLayout(slider_layout)
        layout.addWidget(quality_container)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 底部按钮区域
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(10)
        
        self.start_btn = QPushButton("开始处理")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                background-color: #28a745;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        self.cancel_btn = QPushButton("取消处理")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setMinimumHeight(50)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                background-color: #dc3545;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addWidget(button_container)
        
        return widget
    
    def setup_connections(self):
        """设置信号连接"""
        # 文件操作
        self.file_table.files_dropped.connect(self.add_files)
        self.select_files_btn.clicked.connect(self.select_files)
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.clear_files_btn.clicked.connect(self.clear_files)
        
        # 输出目录
        self.select_output_btn.clicked.connect(self.select_output_directory)
        
        # 参数变化
        self.width_input.textChanged.connect(self.update_file_table)
        self.height_input.textChanged.connect(self.update_file_table)
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        
        # 处理控制
        self.start_btn.clicked.connect(self.start_processing)
        self.cancel_btn.clicked.connect(self.cancel_processing)
    
    def add_files(self, files: List[str]):
        """添加文件到列表"""
        # 过滤支持的文件格式
        valid_files = []
        for file_path in files:
            if self.image_processor.is_supported_format(file_path):
                valid_files.append(file_path)
        
        if valid_files:
            # 去重并添加到现有列表
            existing_files = set(self.selected_files)
            new_files = [f for f in valid_files if f not in existing_files]
            
            self.selected_files.extend(new_files)
            self.update_file_info()
            self.update_file_table()
        else:
            QMessageBox.warning(self, "警告", "没有找到支持的图片文件")
    
    def select_files(self):
        """选择文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.webp);;所有文件 (*.*)"
        )
        if files:
            self.add_files(files)
    
    def select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择包含图片的文件夹")
        if folder:
            files = []
            for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
                files.extend(Path(folder).glob(f'*{ext}'))
                files.extend(Path(folder).glob(f'*{ext.upper()}'))
            
            if files:
                self.add_files([str(f) for f in files])
            else:
                QMessageBox.information(self, "信息", "所选文件夹中没有找到支持的图片文件")
    
    def clear_files(self):
        """清空文件列表"""
        self.selected_files.clear()
        self.update_file_info()
        self.update_file_table()
    
    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_directory = directory
            self.output_dir_input.setText(directory)
    
    def update_file_info(self):
        """更新文件信息"""
        if not self.selected_files:
            return
        
        validation = self.file_manager.validate_files(self.selected_files)
    
    def update_file_table(self):
        """更新文件表格"""
        self.file_table.setRowCount(len(self.selected_files))
        
        try:
            target_width = int(self.width_input.text()) if self.width_input.text() else 0
            target_height = int(self.height_input.text()) if self.height_input.text() else 0
        except ValueError:
            target_width = 0
            target_height = 0
        
        for i, file_path in enumerate(self.selected_files):
            # 文件名
            filename = os.path.basename(file_path)
            self.file_table.setItem(i, 0, QTableWidgetItem(filename))
            
            # 原始尺寸
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    original_size = f"{img.width}×{img.height}"
                    file_size = f"{os.path.getsize(file_path) / (1024*1024):.2f} MB"
            except Exception:
                original_size = "无法读取"
                file_size = "未知"
            
            self.file_table.setItem(i, 1, QTableWidgetItem(original_size))
            
            # 目标尺寸
            target_size = f"{target_width}×{target_height}" if target_width > 0 and target_height > 0 else "未设置"
            self.file_table.setItem(i, 2, QTableWidgetItem(target_size))
            
            # 文件大小
            self.file_table.setItem(i, 3, QTableWidgetItem(file_size))
    
    def update_quality_label(self, value):
        """更新质量标签"""
        self.quality_label.setText(f"{value}%")
    
    def validate_inputs(self) -> bool:
        """验证输入"""
        if not self.selected_files:
            QMessageBox.warning(self, "错误", "请先选择要处理的文件")
            return False
        
        if not self.output_directory:
            QMessageBox.warning(self, "错误", "请选择输出目录")
            return False
        
        try:
            width = int(self.width_input.text()) if self.width_input.text() else 0
            height = int(self.height_input.text()) if self.height_input.text() else 0
        except ValueError:
            width = 0
            height = 0
        if width <= 0 or height <= 0:
            QMessageBox.warning(self, "错误", "请输入有效的宽度和高度")
            return False
        
        return True
    
    def start_processing(self):
        """开始处理"""
        if not self.validate_inputs():
            return
        
        # 获取参数
        target_width = int(self.width_input.text())
        target_height = int(self.height_input.text())
        quality = self.quality_slider.value()
        
        # 获取选择的调整模式
        if self.stretch_radio.isChecked():
            resize_mode = ResizeMode.STRETCH
        elif self.keep_ratio_radio.isChecked():
            resize_mode = ResizeMode.KEEP_RATIO
        else:
            resize_mode = ResizeMode.CROP
        
        # 更新UI状态
        self.start_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 创建处理线程
        self.processing_thread = ProcessingThread(
            self.image_processor,
            self.selected_files,
            self.output_directory,
            (target_width, target_height),
            resize_mode,
            quality
        )
        
        # 连接信号
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.processing_finished.connect(self.processing_finished)
        
        # 启动线程
        self.processing_thread.start()
    
    def cancel_processing(self):
        """取消处理"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait()
        
        self.reset_ui_state()
    
    def update_progress(self, progress: float, filename: str, success: bool):
        """更新进度"""
        self.progress_bar.setValue(int(progress))
    
    def processing_finished(self, result: dict):
        """处理完成"""
        self.reset_ui_state()
        
        # 显示结果
        message = f"""处理完成！

总文件数：{result['total']}
成功处理：{result['processed']}
处理失败：{result['failed']}"""
        
        if result['failed_files']:
            message += f"\n\n失败的文件："
            for file_path, error in result['failed_files'][:5]:
                filename = os.path.basename(file_path)
                message += f"\n• {filename}: {error}"
            
            if len(result['failed_files']) > 5:
                message += f"\n... 还有 {len(result['failed_files']) - 5} 个失败文件"
        
        QMessageBox.information(self, "处理结果", message)
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.start_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("批量图片尺寸调整工具")
    app.setOrganizationName("ImageResizer")
    
    # 设置应用程序图标（如果有的话）
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = ModernImageResizerGUI()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())