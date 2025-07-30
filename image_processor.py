"""
图片处理核心模块
负责图片的加载、调整尺寸、裁剪等操作
"""
from PIL import Image, ImageOps
import os
from typing import Tuple, List, Optional
from enum import Enum


class ResizeMode(Enum):
    """调整尺寸模式"""
    STRETCH = "拉伸"  # 直接拉伸到目标尺寸
    KEEP_RATIO = "保持比例"  # 保持宽高比，可能有空白
    CROP = "裁剪"  # 保持宽高比，裁剪多余部分


class ImageProcessor:
    """图片处理器"""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    def __init__(self):
        self.processed_count = 0
        self.failed_files = []
    
    def is_supported_format(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS
    
    def get_image_info(self, file_path: str) -> Optional[dict]:
        """获取图片信息"""
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_mb': os.path.getsize(file_path) / (1024 * 1024)
                }
        except Exception:
            return None
    
    def resize_image(self, image: Image.Image, target_size: Tuple[int, int], 
                    mode: ResizeMode) -> Image.Image:
        """调整图片尺寸"""
        target_width, target_height = target_size
        
        if mode == ResizeMode.STRETCH:
            # 直接拉伸
            return image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        elif mode == ResizeMode.KEEP_RATIO:
            # 保持比例，添加填充
            image.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            # 创建白色背景
            new_image = Image.new('RGB', (target_width, target_height), 'white')
            # 计算居中位置
            x = (target_width - image.width) // 2
            y = (target_height - image.height) // 2
            new_image.paste(image, (x, y))
            return new_image
        
        elif mode == ResizeMode.CROP:
            # 保持比例，裁剪多余部分
            return ImageOps.fit(image, (target_width, target_height), 
                              Image.Resampling.LANCZOS)
    
    def process_single_image(self, input_path: str, output_path: str, 
                           target_size: Tuple[int, int], mode: ResizeMode,
                           quality: int = 95) -> bool:
        """处理单张图片"""
        try:
            with Image.open(input_path) as img:
                # 处理EXIF旋转信息，避免图片旋转问题
                img = ImageOps.exif_transpose(img)
                
                # 转换为RGB模式（如果需要）
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # 调整尺寸
                processed_img = self.resize_image(img, target_size, mode)
                
                # 保存图片
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                processed_img.save(output_path, quality=quality, optimize=True)
                
                self.processed_count += 1
                return True
                
        except Exception as e:
            self.failed_files.append((input_path, str(e)))
            return False
    
    def batch_process(self, file_list: List[str], output_dir: str, 
                     target_size: Tuple[int, int], mode: ResizeMode,
                     quality: int = 95, progress_callback=None) -> dict:
        """批量处理图片"""
        self.processed_count = 0
        self.failed_files = []
        
        total_files = len(file_list)
        
        for i, input_path in enumerate(file_list):
            if not self.is_supported_format(input_path):
                self.failed_files.append((input_path, "不支持的文件格式"))
                continue
            
            # 生成输出文件名
            filename = os.path.basename(input_path)
            name, ext = os.path.splitext(filename)
            output_filename = f"{name}_resized{ext}"
            output_path = os.path.join(output_dir, output_filename)
            
            # 处理图片
            success = self.process_single_image(input_path, output_path, 
                                              target_size, mode, quality)
            
            # 更新进度
            if progress_callback:
                progress = (i + 1) / total_files * 100
                progress_callback(progress, filename, success)
        
        return {
            'total': total_files,
            'processed': self.processed_count,
            'failed': len(self.failed_files),
            'failed_files': self.failed_files
        }