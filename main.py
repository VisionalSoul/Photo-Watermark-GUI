#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片水印GUI应用
根据需求文档实现的图片水印处理工具
"""

import sys
import os
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QListWidget, QListWidgetItem, 
    QTabWidget, QLineEdit, QSlider, QComboBox, QGroupBox, QRadioButton,
    QGridLayout, QColorDialog, QSpinBox, QDoubleSpinBox, QCheckBox,
    QMessageBox, QSplitter
)
from PyQt5.QtGui import (
    QPixmap, QImage, QFont, QFontDatabase, QPainter, QColor, 
    QIcon, QCursor
)
from PyQt5.QtCore import (
    Qt, QSize, QPoint, QRect, QSettings, QDir, 
    pyqtSignal, pyqtSlot
)

from PIL import Image, ImageDraw, ImageFont, ImageQt
import numpy as np


class WatermarkApp(QMainWindow):
    """主应用窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 设置应用程序信息
        self.setWindowTitle("图片水印工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化数据
        self.image_paths = []  # 存储导入的图片路径
        self.current_index = -1  # 当前选中的图片索引
        self.watermark_type = "text"  # 默认水印类型
        self.watermark_text = "水印文字"  # 默认水印文本
        self.watermark_image_path = ""  # 水印图片路径
        self.watermark_opacity = 50  # 默认透明度（0-100）
        self.watermark_position = (0.5, 0.5)  # 默认位置（中心点）
        self.watermark_size = 100  # 默认水印大小占原图百分比
        self.watermark_rotation = 0  # 默认旋转角度
        self.watermark_color = QColor(0, 0, 0, 128)  # 默认颜色（半透明黑色）
        self.watermark_font = QFont("SimHei", 36)  # 默认字体
        self.is_dragging = False  # 是否正在拖拽水印
        self.drag_start_pos = QPoint()  # 拖拽起始位置
        
        # 加载设置
        # 使用同目录下的配置文件存储设置，而不是注册表
        config_path = QDir.currentPath() + "/watermark_config.ini"
        self.settings = QSettings(config_path, QSettings.IniFormat)
        self.load_settings()
        
        # 创建UI
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # ===== 左侧面板：图片列表 =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 添加图片按钮
        btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("添加文件")
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_add_folder = QPushButton("添加文件夹")
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_remove_files = QPushButton("移除选中")
        self.btn_remove_files.clicked.connect(self.remove_files)
        
        btn_layout.addWidget(self.btn_add_files)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_remove_files)
        
        # 图片列表
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setIconSize(QSize(100, 100))
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setMovement(QListWidget.Static)
        self.image_list.itemClicked.connect(self.on_image_selected)
        # 设置为接受拖放模式
        self.image_list.setAcceptDrops(True)
        self.image_list.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        # 设置viewport接受拖放
        self.image_list.viewport().setAcceptDrops(True)
        
        # 导出按钮
        self.btn_export = QPushButton("导出所选图片")
        self.btn_export.clicked.connect(self.export_images)
        self.btn_export.setDisabled(True)
        
        left_layout.addLayout(btn_layout)
        left_layout.addWidget(QLabel("图片列表:"))
        left_layout.addWidget(self.image_list)
        left_layout.addWidget(self.btn_export)
        
        # ===== 右侧面板：预览和设置 =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 预览区域
        self.preview_label = QLabel("预览区域")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("background-color: #f0f0f0;")
        self.preview_label.mousePressEvent = self.on_preview_mouse_press
        self.preview_label.mouseMoveEvent = self.on_preview_mouse_move
        self.preview_label.mouseReleaseEvent = self.on_preview_mouse_release
        
        # 水印设置选项卡
        self.settings_tab = QTabWidget()
        
        # 文本水印设置
        self.text_watermark_tab = QWidget()
        self.init_text_watermark_tab()
        self.settings_tab.addTab(self.text_watermark_tab, "文本水印")
        
        # 图片水印设置
        self.image_watermark_tab = QWidget()
        self.init_image_watermark_tab()
        self.settings_tab.addTab(self.image_watermark_tab, "图片水印")
        
        # 通用设置
        self.common_settings_tab = QWidget()
        self.init_common_settings_tab()
        self.settings_tab.addTab(self.common_settings_tab, "通用设置")
        
        # 模板设置
        self.template_tab = QWidget()
        self.init_template_tab()
        self.settings_tab.addTab(self.template_tab, "模板管理")
        
        right_layout.addWidget(QLabel("预览:"))
        right_layout.addWidget(self.preview_label, 1)
        right_layout.addWidget(QLabel("水印设置:"))
        right_layout.addWidget(self.settings_tab, 2)
        
        # 将面板添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 900])  # 设置初始大小比例
        
        main_layout.addWidget(splitter)
    
    def init_text_watermark_tab(self):
        """初始化文本水印设置选项卡"""
        layout = QVBoxLayout(self.text_watermark_tab)
        
        # 文本输入
        text_group = QGroupBox("水印文本")
        text_group_layout = QVBoxLayout(text_group)
        self.text_input = QLineEdit(self.watermark_text)
        self.text_input.textChanged.connect(self.update_watermark_text)
        text_group_layout.addWidget(self.text_input)
        
        # 字体设置
        font_group = QGroupBox("字体设置")
        font_group_layout = QGridLayout(font_group)
        
        # 字体下拉列表
        font_group_layout.addWidget(QLabel("字体:"), 0, 0)
        self.font_combo = QComboBox()
        # QFontDatabase().families()直接返回字符串列表，不需要再调用family()方法
        fonts = QFontDatabase().families()
        self.font_combo.addItems(fonts)
        self.font_combo.setCurrentText(self.watermark_font.family())
        self.font_combo.currentTextChanged.connect(self.update_font)
        font_group_layout.addWidget(self.font_combo, 0, 1)
        
        # 字号
        font_group_layout.addWidget(QLabel("字号:"), 0, 2)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 120)
        self.font_size_spin.setValue(self.watermark_font.pointSize())
        self.font_size_spin.valueChanged.connect(self.update_font)
        font_group_layout.addWidget(self.font_size_spin, 0, 3)
        
        # 粗体
        self.bold_check = QCheckBox("粗体")
        self.bold_check.setChecked(self.watermark_font.bold())
        self.bold_check.stateChanged.connect(self.update_font)
        font_group_layout.addWidget(self.bold_check, 1, 0)
        
        # 斜体
        self.italic_check = QCheckBox("斜体")
        self.italic_check.setChecked(self.watermark_font.italic())
        self.italic_check.stateChanged.connect(self.update_font)
        font_group_layout.addWidget(self.italic_check, 1, 1)
        
        # 颜色选择
        font_group_layout.addWidget(QLabel("颜色:"), 1, 2)
        self.color_button = QPushButton()
        self.color_button.setStyleSheet(f"background-color: {self.watermark_color.name()}")
        self.color_button.clicked.connect(self.select_color)
        font_group_layout.addWidget(self.color_button, 1, 3)
        
        layout.addWidget(text_group)
        layout.addWidget(font_group)
        layout.addStretch()
    
    def init_image_watermark_tab(self):
        """初始化图片水印设置选项卡"""
        layout = QVBoxLayout(self.image_watermark_tab)
        
        # 选择水印图片
        self.btn_select_watermark = QPushButton("选择水印图片")
        self.btn_select_watermark.clicked.connect(self.select_watermark_image)
        
        # 取消选择水印图片
        self.btn_clear_watermark = QPushButton("取消选择水印图片")
        self.btn_clear_watermark.clicked.connect(self.clear_watermark_image)
        self.btn_clear_watermark.setEnabled(False)  # 初始禁用，因为还没有选择图片
        
        # 显示水印图片路径
        self.watermark_path_label = QLabel("未选择水印图片")
        self.watermark_path_label.setWordWrap(True)
        
        layout.addWidget(self.btn_select_watermark)
        layout.addWidget(self.btn_clear_watermark)
        layout.addWidget(self.watermark_path_label)
        layout.addStretch()
    
    def init_common_settings_tab(self):
        """初始化通用设置选项卡"""
        layout = QVBoxLayout(self.common_settings_tab)
        
        # 透明度设置
        opacity_group = QGroupBox("透明度")
        opacity_layout = QVBoxLayout(opacity_group)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(self.watermark_opacity)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        self.opacity_label = QLabel(f"{self.watermark_opacity}%")
        
        opacity_sub_layout = QHBoxLayout()
        opacity_sub_layout.addWidget(self.opacity_slider)
        opacity_sub_layout.addWidget(self.opacity_label)
        
        opacity_layout.addLayout(opacity_sub_layout)
        
        # 水印大小
        size_group = QGroupBox("水印大小（占原图百分比）")
        size_layout = QVBoxLayout(size_group)
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(10, 100)
        self.size_slider.setValue(self.watermark_size)
        self.size_slider.valueChanged.connect(self.update_size)
        self.size_label = QLabel(f"{self.watermark_size}%")
        
        size_sub_layout = QHBoxLayout()
        size_sub_layout.addWidget(self.size_slider)
        size_sub_layout.addWidget(self.size_label)
        
        size_layout.addLayout(size_sub_layout)
        
        # 旋转角度
        rotation_group = QGroupBox("旋转角度")
        rotation_layout = QVBoxLayout(rotation_group)
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(0, 359)
        self.rotation_slider.setValue(self.watermark_rotation)
        self.rotation_slider.valueChanged.connect(self.update_rotation)
        self.rotation_label = QLabel(f"{self.watermark_rotation}°")
        
        rotation_sub_layout = QHBoxLayout()
        rotation_sub_layout.addWidget(self.rotation_slider)
        rotation_sub_layout.addWidget(self.rotation_label)
        
        rotation_layout.addLayout(rotation_sub_layout)
        
        # 预设位置
        position_group = QGroupBox("预设位置")
        position_layout = QGridLayout(position_group)
        
        positions = [
            ("左上", 0, 0, 0.0, 0.0),
            ("上中", 0, 1, 0.5, 0.0),
            ("右上", 0, 2, 1.0, 0.0),
            ("左中", 1, 0, 0.0, 0.5),
            ("中心", 1, 1, 0.5, 0.5),
            ("右中", 1, 2, 1.0, 0.5),
            ("左下", 2, 0, 0.0, 1.0),
            ("下中", 2, 1, 0.5, 1.0),
            ("右下", 2, 2, 1.0, 1.0),
        ]
        
        for text, row, col, x, y in positions:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, x=x, y=y: self.set_watermark_position(x, y))
            position_layout.addWidget(btn, row, col)
        
        layout.addWidget(opacity_group)
        layout.addWidget(size_group)
        layout.addWidget(rotation_group)
        layout.addWidget(position_group)
        layout.addStretch()
    
    def init_template_tab(self):
        """初始化模板管理选项卡"""
        layout = QVBoxLayout(self.template_tab)
        
        # 模板操作按钮
        btn_layout = QHBoxLayout()
        self.btn_save_template = QPushButton("保存当前设置为模板")
        self.btn_save_template.clicked.connect(self.save_template)
        self.btn_load_template = QPushButton("加载模板")
        self.btn_load_template.clicked.connect(self.load_template)
        self.btn_delete_template = QPushButton("删除模板")
        self.btn_delete_template.clicked.connect(self.delete_template)
        
        btn_layout.addWidget(self.btn_save_template)
        btn_layout.addWidget(self.btn_load_template)
        btn_layout.addWidget(self.btn_delete_template)
        
        # 模板列表
        self.template_list = QListWidget()
        self.load_template_list()
        
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("已保存的模板:"))
        layout.addWidget(self.template_list)
    
    def add_files(self):
        """添加文件"""
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;所有文件 (*)", 
            options=options
        )
        
        if files:
            self.add_images(files)
    
    def add_folder(self):
        """添加文件夹"""
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(
            self, "选择图片文件夹", "", options=options
        )
        
        if folder:
            # 获取文件夹中所有支持的图片文件
            supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
            files = []
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in supported_formats):
                        files.append(os.path.join(root, filename))
            
            if files:
                self.add_images(files)
            else:
                QMessageBox.information(self, "提示", "所选文件夹中没有找到支持的图片文件")
    
    def add_images(self, files):
        """添加图片到列表"""
        for file_path in files:
            if file_path not in self.image_paths:
                self.image_paths.append(file_path)
                
                # 创建列表项
                item = QListWidgetItem(os.path.basename(file_path))
                
                # 创建缩略图，添加错误处理
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(scaled_pixmap))
                else:
                    # 如果无法加载图片，设置默认文本
                    item.setText(f"{os.path.basename(file_path)} (无法加载)")
                
                self.image_list.addItem(item)
        
        # 如果是第一次添加图片，自动选中第一张
        if self.image_list.count() > 0 and self.current_index == -1:
            self.image_list.setCurrentRow(0)
            self.on_image_selected(self.image_list.currentItem())
        
        # 启用导出按钮
        self.btn_export.setEnabled(self.image_list.count() > 0)
    
    def remove_files(self):
        """移除选中的文件"""
        selected_items = self.image_list.selectedItems()
        if not selected_items:
            return
        
        # 保存当前选中索引
        current_row = self.image_list.currentRow()
        
        # 移除选中项
        for item in selected_items:
            index = self.image_list.row(item)
            if index < len(self.image_paths):
                del self.image_paths[index]
            self.image_list.takeItem(self.image_list.row(item))
        
        # 更新当前索引
        if self.image_list.count() == 0:
            self.current_index = -1
            self.preview_label.setText("预览区域")
        else:
            # 尝试保持选中相同位置的项
            new_row = min(current_row, self.image_list.count() - 1)
            self.image_list.setCurrentRow(new_row)
            self.on_image_selected(self.image_list.currentItem())
        
        # 更新导出按钮状态
        self.btn_export.setEnabled(self.image_list.count() > 0)
    
    def on_image_selected(self, item):
        """图片选中事件"""
        if item:
            index = self.image_list.row(item)
            if 0 <= index < len(self.image_paths):
                self.current_index = index
                self.update_preview()
    
    def update_preview(self):
        """更新预览"""
        if self.current_index >= 0 and self.current_index < len(self.image_paths):
            image_path = self.image_paths[self.current_index]
            
            try:
                # 打开原图
                image = Image.open(image_path)
                
                # 应用水印
                watermarked_image = self.apply_watermark(image)
                
                # 转换为QPixmap显示
                q_image = self.pil_to_qimage(watermarked_image)
                if not q_image.isNull():
                    pixmap = QPixmap.fromImage(q_image)
                    
                    # 缩放以适应预览区域
                    scaled_pixmap = pixmap.scaled(
                        self.preview_label.size(), 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    
                    self.preview_label.setPixmap(scaled_pixmap)
                else:
                    self.preview_label.setText("无法显示预览图片")
            except Exception as e:
                self.preview_label.setText(f"预览错误: {str(e)}")
        else:
            self.preview_label.setText("预览区域")
    
    def apply_watermark(self, image):
        """应用水印到图片"""
        # 创建图像副本
        watermarked = image.copy()
        
        # 根据水印类型应用不同的处理
        if self.watermark_type == "text":
            result = self.apply_text_watermark(watermarked)
            # 确保结果不为空
            if result is None:
                return watermarked
            return result
        elif self.watermark_type == "image" and self.watermark_image_path:
            result = self.apply_image_watermark(watermarked)
            if result is None:
                return watermarked
            return result
        
        return watermarked
    
    def apply_text_watermark(self, image):
        """应用文本水印"""
        # 确保图像有alpha通道
        original_mode = image.mode
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # 创建水印层
        watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # 获取水印文本
        text = self.watermark_text
        if not text.strip():
            return image  # 如果文本为空，返回原图
        
        # 计算字体大小（基于用户设置和图像尺寸）
        base_size = min(image.width, image.height) * (self.watermark_size / 100)
        font_size = max(8, min(120, int(base_size / 5)))  # 限制字体大小范围
        
        # Windows系统中常见的中文字体路径
        chinese_fonts = [
            r"C:\Windows\Fonts\simsun.ttc",     # 宋体
            r"C:\Windows\Fonts\simhei.ttf",    # 黑体
            r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
            r"C:\Windows\Fonts\simkai.ttf",    # 楷体
            r"C:\Windows\Fonts\msyhbd.ttc",    # 微软雅黑粗体
        ]
        
        # 查找可用的中文字体
        font = None
        
        # 尝试加载中文字体
        for font_path in chinese_fonts:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            except Exception:
                continue
        
        # 如果找不到中文字体，使用默认字体
        if font is None:
            try:
                # 尝试使用PIL默认字体
                font = ImageFont.load_default()
            except Exception:
                # 如果默认字体也加载失败，使用备用字体大小计算
                pass
        
        # 获取用户设置的颜色和透明度
        color = self.watermark_color
        text_color = (color.red(), color.green(), color.blue(), int(color.alpha() * self.watermark_opacity / 100))
        
        # 计算文本尺寸和位置
        try:
            # 尝试获取文本尺寸
            if hasattr(draw, 'textsize'):
                # PIL 10.0.0之前的版本
                text_width, text_height = draw.textsize(text, font=font)
            else:
                # PIL 10.0.0及以后的版本
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
        except Exception:
            # 如果无法获取文本尺寸，使用估计值
            text_width = font_size * len(text) * 0.7
            text_height = font_size * 1.2
        
        # 计算水印位置（基于用户设置的位置）
        x = int((self.watermark_position[0] * image.width) - (text_width / 2))
        y = int((self.watermark_position[1] * image.height) - (text_height / 2))
        
        # 确保文本在图像范围内
        x = max(0, min(x, image.width - text_width))
        y = max(0, min(y, image.height - text_height))
        
        # 绘制文本
        try:
            draw.text((x, y), text, font=font, fill=text_color)
        except Exception:
            # 如果使用font参数失败，尝试不使用font参数
            try:
                draw.text((x, y), text, fill=text_color)
            except Exception:
                # 如果仍然失败，记录错误但继续执行
                pass
        
        # 合并水印层到原图
        result = Image.new("RGBA", image.size)
        result.paste(image, (0, 0))
        result.paste(watermark_layer, (0, 0), watermark_layer)
        
        # 转换回原始模式
        if original_mode == "RGB":
            result = result.convert("RGB")
        
        return result
    
    def apply_image_watermark(self, image):
        """应用图片水印"""
        try:
            # 打开水印图片
            watermark = Image.open(self.watermark_image_path)
            
            # 确保水印图片有alpha通道
            if watermark.mode != "RGBA":
                watermark = watermark.convert("RGBA")
            
            # 确保原图有alpha通道
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            
            # 计算水印大小
            base_size = min(image.width, image.height) * (self.watermark_size / 100)
            scale_factor = base_size / max(watermark.width, watermark.height)
            
            new_width = int(watermark.width * scale_factor)
            new_height = int(watermark.height * scale_factor)
            
            # 调整水印大小
            watermark = watermark.resize((new_width, new_height), Image.LANCZOS)
            
            # 应用透明度
            if self.watermark_opacity != 100:
                # 获取水印的alpha通道
                r, g, b, a = watermark.split()
                # 调整alpha通道
                a = a.point(lambda x: int(x * self.watermark_opacity / 100))
                # 合并回水印图片
                watermark = Image.merge("RGBA", (r, g, b, a))
            
            # 应用旋转
            if self.watermark_rotation != 0:
                watermark = watermark.rotate(self.watermark_rotation, expand=1, fillcolor=(0, 0, 0, 0))
            
            # 计算水印位置
            x = int((self.watermark_position[0] * image.width) - (watermark.width / 2))
            y = int((self.watermark_position[1] * image.height) - (watermark.height / 2))
            
            # 创建结果图片并合并
            result = Image.new("RGBA", image.size)
            result.paste(image, (0, 0))
            result.paste(watermark, (x, y), watermark)
            
            # 转换回原始模式
            if image.mode == "RGB":
                result = result.convert("RGB")
            
            return result
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用图片水印时出错: {str(e)}")
            return image
    
    def pil_to_qimage(self, pil_image):
        """将PIL Image转换为QImage"""
        if pil_image.mode == "RGB":
            r, g, b = pil_image.split()
            q_image = QImage(pil_image.tobytes(), pil_image.width, pil_image.height, pil_image.width * 3, QImage.Format_RGB888)
            return q_image.rgbSwapped()
        elif pil_image.mode == "RGBA":
            r, g, b, a = pil_image.split()
            q_image = QImage(pil_image.tobytes(), pil_image.width, pil_image.height, pil_image.width * 4, QImage.Format_RGBA8888)
            return q_image.rgbSwapped()
        else:
            return QImage(pil_image.tobytes(), pil_image.width, pil_image.height, pil_image.width, QImage.Format_Grayscale8)
    
    def update_watermark_text(self, text):
        """更新水印文本"""
        self.watermark_text = text
        self.update_preview()
    
    def update_opacity(self, value):
        """更新透明度"""
        self.watermark_opacity = value
        self.opacity_label.setText(f"{value}%")
        self.update_preview()
    
    def update_size(self, value):
        """更新水印大小"""
        self.watermark_size = value
        self.size_label.setText(f"{value}%")
        self.update_preview()
    
    def update_rotation(self, value):
        """更新旋转角度"""
        self.watermark_rotation = value
        self.rotation_label.setText(f"{value}°")
        self.update_preview()
    
    def set_watermark_position(self, x, y):
        """设置水印位置"""
        self.watermark_position = (x, y)
        self.update_preview()
    
    def select_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.watermark_color, self, "选择水印颜色")
        if color.isValid():
            self.watermark_color = color
            self.color_button.setStyleSheet(f"background-color: {color.name()}")
            self.update_preview()
    
    def update_font(self):
        """更新字体设置"""
        font_family = self.font_combo.currentText()
        font_size = self.font_size_spin.value()
        bold = self.bold_check.isChecked()
        italic = self.italic_check.isChecked()
        
        self.watermark_font = QFont(font_family, font_size)
        self.watermark_font.setBold(bold)
        self.watermark_font.setItalic(italic)
        
        self.update_preview()
    
    def select_watermark_image(self):
        """选择水印图片"""
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;所有文件 (*)", 
            options=options
        )
        
        if file:
            self.watermark_image_path = file
            self.watermark_path_label.setText(file)
            self.btn_clear_watermark.setEnabled(True)  # 启用取消选择按钮
            self.watermark_type = "image"
            self.settings_tab.setCurrentIndex(1)  # 切换到图片水印选项卡
            self.update_preview()
    
    def clear_watermark_image(self):
        """取消选择水印图片"""
        self.watermark_image_path = ""
        self.watermark_path_label.setText("未选择水印图片")
        self.btn_clear_watermark.setEnabled(False)  # 禁用取消选择按钮
        # 如果当前是图片水印类型，则切换到文本水印
        if self.watermark_type == "image":
            self.watermark_type = "text"
            self.settings_tab.setCurrentIndex(0)  # 切换到文本水印选项卡
        self.update_preview()
    
    def export_images(self):
        """导出图片"""
        if not self.image_paths:
            return
        
        # 选择导出文件夹
        options = QFileDialog.Options()
        export_dir = QFileDialog.getExistingDirectory(
            self, "选择导出文件夹", "", options=options
        )
        
        if not export_dir:
            return
        
        # 检查是否选择了原文件夹
        for image_path in self.image_paths:
            if os.path.dirname(image_path) == export_dir:
                reply = QMessageBox.warning(
                    self, "警告", 
                    "您选择了原图片所在的文件夹作为导出目录，这可能会覆盖原文件。确定要继续吗？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
                break
        
        # 显示导出设置对话框
        from export_dialog import ExportDialog
        dialog = ExportDialog(self)
        if dialog.exec_():
            # 获取导出设置
            export_format = dialog.format_combo.currentText().lower()
            naming_rule = dialog.get_naming_rule()
            quality = dialog.quality_spin.value() if export_format == "jpeg" else 100
            resize_option = dialog.get_resize_option()
            
            # 开始导出
            for i, image_path in enumerate(self.image_paths):
                try:
                    # 打开图片
                    image = Image.open(image_path)
                    
                    # 应用水印
                    watermarked_image = self.apply_watermark(image)
                    
                    # 调整尺寸（如果需要）
                    if resize_option:
                        option_type, value = resize_option
                        if option_type == "width":
                            width = value
                            height = int(image.height * (width / image.width))
                        elif option_type == "height":
                            height = value
                            width = int(image.width * (height / image.height))
                        else:  # percentage
                            width = int(image.width * value / 100)
                            height = int(image.height * value / 100)
                        
                        watermarked_image = watermarked_image.resize((width, height), Image.LANCZOS)
                    
                    # 生成输出文件名
                    base_name = os.path.basename(image_path)
                    name_without_ext = os.path.splitext(base_name)[0]
                    
                    if naming_rule["type"] == "original":
                        output_name = f"{name_without_ext}.{export_format}"
                    elif naming_rule["type"] == "prefix":
                        output_name = f"{naming_rule['value']}{name_without_ext}.{export_format}"
                    else:  # suffix
                        output_name = f"{name_without_ext}{naming_rule['value']}.{export_format}"
                    
                    # 保存文件
                    output_path = os.path.join(export_dir, output_name)
                    
                    # 根据格式保存
                    if export_format == "jpeg":
                        # 确保是RGB模式
                        if watermarked_image.mode == "RGBA":
                            background = Image.new("RGB", watermarked_image.size, (255, 255, 255))
                            background.paste(watermarked_image, mask=watermarked_image.split()[3])
                            watermarked_image = background
                        watermarked_image.save(output_path, "JPEG", quality=quality)
                    else:  # png
                        watermarked_image.save(output_path, "PNG")
                    
                except Exception as e:
                    QMessageBox.warning(
                        self, "导出失败", 
                        f"导出图片 '{os.path.basename(image_path)}' 时出错: {str(e)}"
                    )
            
            QMessageBox.information(self, "完成", "图片导出成功！")
    
    def save_template(self):
        """保存当前设置为模板"""
        from template_dialog import TemplateDialog
        dialog = TemplateDialog(self, "save")
        if dialog.exec_():
            template_name = dialog.template_name.text()
            if template_name:
                # 保存模板设置
                self.save_template_to_settings(template_name)
                self.load_template_list()
                QMessageBox.information(self, "成功", f"模板 '{template_name}' 已保存")
    
    def load_template(self):
        """加载模板"""
        selected_item = self.template_list.currentItem()
        if selected_item:
            template_name = selected_item.text()
            self.load_template_from_settings(template_name)
            self.update_ui_from_settings()
            self.update_preview()
            QMessageBox.information(self, "成功", f"模板 '{template_name}' 已加载")
        else:
            QMessageBox.warning(self, "警告", "请先选择一个模板")
    
    def delete_template(self):
        """删除模板"""
        selected_item = self.template_list.currentItem()
        if selected_item:
            template_name = selected_item.text()
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除模板 '{template_name}' 吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.delete_template_from_settings(template_name)
                self.load_template_list()
                QMessageBox.information(self, "成功", f"模板 '{template_name}' 已删除")
        else:
            QMessageBox.warning(self, "警告", "请先选择一个模板")
    
    def save_template_to_settings(self, template_name):
        """保存模板到设置"""
        template_key = f"templates/{template_name}"
        
        self.settings.setValue(f"{template_key}/type", self.watermark_type)
        self.settings.setValue(f"{template_key}/text", self.watermark_text)
        self.settings.setValue(f"{template_key}/image_path", self.watermark_image_path)
        self.settings.setValue(f"{template_key}/opacity", self.watermark_opacity)
        self.settings.setValue(f"{template_key}/position_x", self.watermark_position[0])
        self.settings.setValue(f"{template_key}/position_y", self.watermark_position[1])
        self.settings.setValue(f"{template_key}/size", self.watermark_size)
        self.settings.setValue(f"{template_key}/rotation", self.watermark_rotation)
        self.settings.setValue(f"{template_key}/color", self.watermark_color.name())
        self.settings.setValue(f"{template_key}/font_family", self.watermark_font.family())
        self.settings.setValue(f"{template_key}/font_size", self.watermark_font.pointSize())
        self.settings.setValue(f"{template_key}/font_bold", self.watermark_font.bold())
        self.settings.setValue(f"{template_key}/font_italic", self.watermark_font.italic())
    
    def load_template_from_settings(self, template_name):
        """从设置加载模板"""
        template_key = f"templates/{template_name}"
        
        self.watermark_type = self.settings.value(f"{template_key}/type", "text")
        self.watermark_text = self.settings.value(f"{template_key}/text", "水印文字")
        self.watermark_image_path = self.settings.value(f"{template_key}/image_path", "")
        self.watermark_opacity = self.settings.value(f"{template_key}/opacity", 50, type=int)
        pos_x = self.settings.value(f"{template_key}/position_x", 0.5, type=float)
        pos_y = self.settings.value(f"{template_key}/position_y", 0.5, type=float)
        self.watermark_position = (pos_x, pos_y)
        self.watermark_size = self.settings.value(f"{template_key}/size", 100, type=int)
        self.watermark_rotation = self.settings.value(f"{template_key}/rotation", 0, type=int)
        
        color_name = self.settings.value(f"{template_key}/color", "#FFFFFF")
        self.watermark_color = QColor(color_name)
        
        font_family = self.settings.value(f"{template_key}/font_family", "SimHei")
        font_size = self.settings.value(f"{template_key}/font_size", 36, type=int)
        font_bold = self.settings.value(f"{template_key}/font_bold", False, type=bool)
        font_italic = self.settings.value(f"{template_key}/font_italic", False, type=bool)
        
        self.watermark_font = QFont(font_family, font_size)
        self.watermark_font.setBold(font_bold)
        self.watermark_font.setItalic(font_italic)
    
    def delete_template_from_settings(self, template_name):
        """从设置删除模板"""
        template_key = f"templates/{template_name}"
        
        # 删除所有模板相关的设置
        for key in self.settings.allKeys():
            if key.startswith(template_key):
                self.settings.remove(key)
    
    def load_template_list(self):
        """加载模板列表"""
        self.template_list.clear()
        
        # 获取所有模板名称
        template_names = set()
        for key in self.settings.allKeys():
            if key.startswith("templates/"):
                parts = key.split("/")
                if len(parts) >= 2:
                    template_names.add(parts[1])
        
        # 添加到列表
        for name in sorted(template_names):
            self.template_list.addItem(name)
    
    def update_ui_from_settings(self):
        """从设置更新UI"""
        # 更新文本水印设置
        self.text_input.setText(self.watermark_text)
        
        # 更新字体设置
        font_index = self.font_combo.findText(self.watermark_font.family())
        if font_index >= 0:
            self.font_combo.setCurrentIndex(font_index)
        self.font_size_spin.setValue(self.watermark_font.pointSize())
        self.bold_check.setChecked(self.watermark_font.bold())
        self.italic_check.setChecked(self.watermark_font.italic())
        
        # 更新颜色
        self.color_button.setStyleSheet(f"background-color: {self.watermark_color.name()}")
        
        # 更新图片水印设置
        self.watermark_path_label.setText(self.watermark_image_path)
        
        # 更新通用设置
        self.opacity_slider.setValue(self.watermark_opacity)
        self.opacity_label.setText(f"{self.watermark_opacity}%")
        self.size_slider.setValue(self.watermark_size)
        self.size_label.setText(f"{self.watermark_size}%")
        self.rotation_slider.setValue(self.watermark_rotation)
        self.rotation_label.setText(f"{self.watermark_rotation}°")
        
        # 切换到正确的选项卡
        if self.watermark_type == "image":
            self.settings_tab.setCurrentIndex(1)
        else:
            self.settings_tab.setCurrentIndex(0)
    
    def load_settings(self):
        """加载应用设置"""
        # 尝试加载上次使用的设置
        try:
            if self.settings.contains("last_settings/type"):
                self.watermark_type = self.settings.value("last_settings/type", "text")
                self.watermark_text = self.settings.value("last_settings/text", "水印文字")
                self.watermark_image_path = self.settings.value("last_settings/image_path", "")
                self.watermark_opacity = self.settings.value("last_settings/opacity", 50, type=int)
                pos_x = self.settings.value("last_settings/position_x", 0.5, type=float)
                pos_y = self.settings.value("last_settings/position_y", 0.5, type=float)
                self.watermark_position = (pos_x, pos_y)
                self.watermark_size = self.settings.value("last_settings/size", 100, type=int)
                self.watermark_rotation = self.settings.value("last_settings/rotation", 0, type=int)
                
                color_name = self.settings.value("last_settings/color", "#FFFFFF")
                self.watermark_color = QColor(color_name)
                
                font_family = self.settings.value("last_settings/font_family", "SimHei")
                font_size = self.settings.value("last_settings/font_size", 36, type=int)
                font_bold = self.settings.value("last_settings/font_bold", False, type=bool)
                font_italic = self.settings.value("last_settings/font_italic", False, type=bool)
                
                self.watermark_font = QFont(font_family, font_size)
                self.watermark_font.setBold(font_bold)
                self.watermark_font.setItalic(font_italic)
        except:
            # 如果加载失败，使用默认设置
            pass
    
    def save_settings(self):
        """保存应用设置"""
        try:
            self.settings.setValue("last_settings/type", self.watermark_type)
            self.settings.setValue("last_settings/text", self.watermark_text)
            self.settings.setValue("last_settings/image_path", self.watermark_image_path)
            self.settings.setValue("last_settings/opacity", self.watermark_opacity)
            self.settings.setValue("last_settings/position_x", self.watermark_position[0])
            self.settings.setValue("last_settings/position_y", self.watermark_position[1])
            self.settings.setValue("last_settings/size", self.watermark_size)
            self.settings.setValue("last_settings/rotation", self.watermark_rotation)
            self.settings.setValue("last_settings/color", self.watermark_color.name())
            self.settings.setValue("last_settings/font_family", self.watermark_font.family())
            self.settings.setValue("last_settings/font_size", self.watermark_font.pointSize())
            self.settings.setValue("last_settings/font_bold", self.watermark_font.bold())
            self.settings.setValue("last_settings/font_italic", self.watermark_font.italic())
        except:
            pass
    
    def on_preview_mouse_press(self, event):
        """预览区域鼠标按下事件"""
        if event.button() == Qt.LeftButton and self.current_index >= 0:
            # 检查是否点击了水印区域
            # 这里简化处理，实际上需要更精确的碰撞检测
            self.is_dragging = True
            self.drag_start_pos = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
    
    def on_preview_mouse_move(self, event):
        """预览区域鼠标移动事件"""
        if self.is_dragging:
            # 计算移动距离
            delta = event.pos() - self.drag_start_pos
            
            # 获取预览标签的尺寸和图像的实际尺寸
            if self.preview_label.pixmap():
                pixmap = self.preview_label.pixmap()
                label_width = self.preview_label.width()
                label_height = self.preview_label.height()
                
                # 计算移动比例
                scale_x = 1.0 / label_width
                scale_y = 1.0 / label_height
                
                # 更新水印位置
                new_x = self.watermark_position[0] + delta.x() * scale_x
                new_y = self.watermark_position[1] + delta.y() * scale_y
                
                # 限制在有效范围内
                new_x = max(0.0, min(1.0, new_x))
                new_y = max(0.0, min(1.0, new_y))
                
                self.watermark_position = (new_x, new_y)
                
                # 更新预览
                self.update_preview()
                
                # 更新起始位置
                self.drag_start_pos = event.pos()
    
    def on_preview_mouse_release(self, event):
        """预览区域鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.setCursor(QCursor(Qt.ArrowCursor))
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.update_preview()
    
    def dragEnterEvent(self, event):
        """处理拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """处理拖动移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        """处理拖放事件"""
        if event.mimeData().hasUrls():
            # 获取拖放的文件路径
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                # 检查是否为文件且是支持的图片格式
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file_path)
                    if ext.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']:
                        files.append(file_path)
                # 检查是否为文件夹
                elif os.path.isdir(file_path):
                    # 递归获取文件夹中所有支持的图片文件
                    supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
                    for root, _, filenames in os.walk(file_path):
                        for filename in filenames:
                            if any(filename.lower().endswith(ext) for ext in supported_formats):
                                files.append(os.path.join(root, filename))
            
            # 添加图片
            if files:
                self.add_images(files)
            
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存设置
        self.save_settings()
        event.accept()


if __name__ == "__main__":
    # 确保中文显示正常
    import sys
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = WatermarkApp()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())