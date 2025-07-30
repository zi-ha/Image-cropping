"""
图片处理核心模块
负责图片的加载、调整尺寸、裁剪等操作
支持单进程和多进程处理
"""
from PIL import Image, ImageOps
import os
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Tuple, List, Optional, Callable
from enum import Enum
import time
from functools import partial


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


def process_single_image_worker(args):
    """
    多进程工作函数 - 处理单张图片
    这个函数需要在模块级别定义以支持pickle序列化
    """
    input_path, output_path, target_size, mode, quality = args
    
    try:
        with Image.open(input_path) as img:
            # 处理EXIF旋转信息，避免图片旋转问题
            img = ImageOps.exif_transpose(img)
            
            # 转换为RGB模式（如果需要）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # 调整尺寸
            target_width, target_height = target_size
            
            if mode == ResizeMode.STRETCH:
                # 直接拉伸
                processed_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            elif mode == ResizeMode.KEEP_RATIO:
                # 保持比例，添加填充
                img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                # 创建白色背景
                processed_img = Image.new('RGB', (target_width, target_height), 'white')
                # 计算居中位置
                x = (target_width - img.width) // 2
                y = (target_height - img.height) // 2
                processed_img.paste(img, (x, y))
            
            elif mode == ResizeMode.CROP:
                # 保持比例，裁剪多余部分
                processed_img = ImageOps.fit(img, (target_width, target_height), 
                                          Image.Resampling.LANCZOS)
            
            # 保存图片
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            processed_img.save(output_path, quality=quality, optimize=True)
            
            return True, input_path, None
            
    except Exception as e:
        return False, input_path, str(e)


class MultiProcessImageProcessor:
    """多进程图片处理器"""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        初始化多进程图片处理器
        
        Args:
            max_workers: 最大工作进程数，默认为CPU核心数的一半
        """
        if max_workers is None:
            # 默认使用CPU核心数的一半，最少1个进程
            self.max_workers = max(1, mp.cpu_count() // 2)
        else:
            self.max_workers = max_workers
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
    
    def batch_process(self, file_list: List[str], output_dir: str, 
                     target_size: Tuple[int, int], mode: ResizeMode,
                     quality: int = 95, progress_callback: Optional[Callable] = None) -> dict:
        """
        多进程批量处理图片
        
        Args:
            file_list: 输入文件列表
            output_dir: 输出目录
            target_size: 目标尺寸 (width, height)
            mode: 调整模式
            quality: 图片质量 (1-100)
            progress_callback: 进度回调函数
            
        Returns:
            处理结果字典
        """
        self.processed_count = 0
        self.failed_files = []
        
        # 过滤支持的文件格式
        valid_files = []
        for file_path in file_list:
            if self.is_supported_format(file_path):
                valid_files.append(file_path)
            else:
                self.failed_files.append((file_path, "不支持的文件格式"))
        
        total_files = len(valid_files)
        if total_files == 0:
            return {
                'total': len(file_list),
                'processed': 0,
                'failed': len(self.failed_files),
                'failed_files': self.failed_files
            }
        
        # 准备任务参数
        tasks = []
        for input_path in valid_files:
            filename = os.path.basename(input_path)
            name, ext = os.path.splitext(filename)
            output_filename = f"{name}_resized{ext}"
            output_path = os.path.join(output_dir, output_filename)
            
            tasks.append((input_path, output_path, target_size, mode, quality))
        
        # 使用进程池处理
        start_time = time.time()
        completed_count = 0
        
        try:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_task = {
                    executor.submit(process_single_image_worker, task): task 
                    for task in tasks
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    input_path = task[0]
                    filename = os.path.basename(input_path)
                    
                    try:
                        success, processed_path, error = future.result()
                        completed_count += 1
                        
                        if success:
                            self.processed_count += 1
                        else:
                            self.failed_files.append((processed_path, error))
                        
                        # 更新进度
                        if progress_callback:
                            progress = completed_count / total_files * 100
                            progress_callback(progress, filename, success)
                            
                    except Exception as e:
                        completed_count += 1
                        self.failed_files.append((input_path, f"处理异常: {str(e)}"))
                        
                        if progress_callback:
                            progress = completed_count / total_files * 100
                            progress_callback(progress, filename, False)
        
        except Exception as e:
            # 如果多进程处理失败，回退到单进程处理
            print(f"多进程处理失败，回退到单进程模式: {e}")
            return self._fallback_single_process(file_list, output_dir, target_size, mode, quality, progress_callback)
        
        processing_time = time.time() - start_time
        
        return {
            'total': len(file_list),
            'processed': self.processed_count,
            'failed': len(self.failed_files),
            'failed_files': self.failed_files,
            'processing_time': processing_time,
            'workers_used': self.max_workers
        }
    
    def _fallback_single_process(self, file_list: List[str], output_dir: str, 
                                target_size: Tuple[int, int], mode: ResizeMode,
                                quality: int = 95, progress_callback: Optional[Callable] = None) -> dict:
        """回退到单进程处理"""
        single_processor = ImageProcessor()
        return single_processor.batch_process(file_list, output_dir, target_size, mode, quality, progress_callback)