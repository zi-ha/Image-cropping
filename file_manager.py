"""
文件管理模块
负责文件的选择、验证、路径处理等操作
"""
import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from typing import List, Optional


class FileManager:
    """文件管理器"""
    
    def __init__(self):
        self.selected_files = []
        self.output_directory = ""
    
    def select_files(self, parent_window=None) -> List[str]:
        """选择多个图片文件"""
        file_filter = (
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.webp);;"
            "JPEG文件 (*.jpg *.jpeg);;"
            "PNG文件 (*.png);;"
            "BMP文件 (*.bmp);;"
            "TIFF文件 (*.tiff);;"
            "WebP文件 (*.webp);;"
            "所有文件 (*.*)"
        )
        
        files, _ = QFileDialog.getOpenFileNames(
            parent_window,
            "选择要处理的图片文件",
            "",
            file_filter
        )
        
        self.selected_files = files if files else []
        return self.selected_files
    
    def select_folder(self, parent_window=None) -> List[str]:
        """选择文件夹并获取其中的图片文件"""
        folder = QFileDialog.getExistingDirectory(
            parent_window,
            "选择包含图片的文件夹"
        )
        
        if not folder:
            return []
        
        image_files = []
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        
        try:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in supported_extensions:
                        image_files.append(file_path)
        except Exception as e:
            if parent_window:
                QMessageBox.critical(parent_window, "错误", f"读取文件夹失败：{str(e)}")
            return []
        
        self.selected_files = image_files
        return image_files
    
    def select_output_directory(self, parent_window=None) -> str:
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(
            parent_window,
            "选择输出目录"
        )
        
        self.output_directory = directory if directory else ""
        return self.output_directory
    
    def validate_files(self, file_list: List[str]) -> dict:
        """验证文件列表"""
        valid_files = []
        invalid_files = []
        total_size = 0
        
        for file_path in file_list:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    size = os.path.getsize(file_path)
                    total_size += size
                    valid_files.append(file_path)
                except Exception:
                    invalid_files.append(file_path)
            else:
                invalid_files.append(file_path)
        
        return {
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'total_count': len(file_list),
            'valid_count': len(valid_files),
            'invalid_count': len(invalid_files),
            'total_size_mb': total_size / (1024 * 1024)
        }
    
    def get_safe_filename(self, original_path: str, output_dir: str, 
                         suffix: str = "_resized") -> str:
        """生成安全的输出文件名，避免覆盖"""
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        
        counter = 0
        while True:
            if counter == 0:
                new_filename = f"{name}{suffix}{ext}"
            else:
                new_filename = f"{name}{suffix}_{counter}{ext}"
            
            output_path = os.path.join(output_dir, new_filename)
            if not os.path.exists(output_path):
                return output_path
            
            counter += 1
            if counter > 1000:  # 防止无限循环
                raise ValueError("无法生成唯一文件名")
    
    def create_output_directory(self, base_dir: str, folder_name: str = "resized_images") -> str:
        """创建输出目录"""
        output_dir = os.path.join(base_dir, folder_name)
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            return output_dir
        except Exception as e:
            raise Exception(f"创建输出目录失败：{str(e)}")
    
    def get_file_info_summary(self, file_list: List[str]) -> str:
        """获取文件信息摘要"""
        if not file_list:
            return "未选择文件"
        
        validation = self.validate_files(file_list)
        
        summary = f"总文件数：{validation['total_count']}\n"
        summary += f"有效文件：{validation['valid_count']}\n"
        summary += f"无效文件：{validation['invalid_count']}\n"
        summary += f"总大小：{validation['total_size_mb']:.2f} MB"
        
        return summary