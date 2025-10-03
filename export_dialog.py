#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
export_dialog.py - 导出设置对话框
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QRadioButton, QLineEdit, QSpinBox, QGroupBox, QGridLayout,
    QPushButton, QCheckBox
)
from PyQt5.QtCore import Qt


class ExportDialog(QDialog):
    """导出设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出设置")
        self.resize(400, 300)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 输出格式设置
        format_group = QGroupBox("输出格式")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG"])
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        
        format_layout.addWidget(QLabel("选择格式:"))
        format_layout.addWidget(self.format_combo)
        
        # 文件名设置
        naming_group = QGroupBox("文件命名")
        naming_layout = QVBoxLayout(naming_group)
        
        # 命名规则单选按钮
        self.radio_original = QRadioButton("保留原文件名")
        self.radio_prefix = QRadioButton("添加前缀")
        self.radio_suffix = QRadioButton("添加后缀")
        
        # 设置默认选中
        self.radio_original.setChecked(True)
        
        # 前缀/后缀输入框
        self.prefix_input = QLineEdit("wm_")
        self.suffix_input = QLineEdit("_watermarked")
        
        # 默认禁用前缀/后缀输入框
        self.prefix_input.setEnabled(False)
        self.suffix_input.setEnabled(False)
        
        # 连接信号
        self.radio_original.toggled.connect(self.on_naming_rule_changed)
        self.radio_prefix.toggled.connect(self.on_naming_rule_changed)
        self.radio_suffix.toggled.connect(self.on_naming_rule_changed)
        
        naming_layout.addWidget(self.radio_original)
        naming_layout.addWidget(self.radio_prefix)
        naming_layout.addWidget(self.prefix_input)
        naming_layout.addWidget(self.radio_suffix)
        naming_layout.addWidget(self.suffix_input)
        
        # JPEG质量设置
        quality_group = QGroupBox("JPEG 质量")
        quality_layout = QVBoxLayout(quality_group)
        
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(0, 100)
        self.quality_spin.setValue(90)
        self.quality_label = QLabel("90%")
        
        quality_spin_layout = QHBoxLayout()
        quality_spin_layout.addWidget(self.quality_spin)
        quality_spin_layout.addWidget(self.quality_label)
        
        self.quality_spin.valueChanged.connect(lambda value: self.quality_label.setText(f"{value}%"))
        
        quality_layout.addWidget(QLabel("设置图片质量:"))
        quality_layout.addLayout(quality_spin_layout)
        
        # 调整尺寸设置
        resize_group = QGroupBox("调整尺寸")
        resize_layout = QVBoxLayout(resize_group)
        
        self.resize_check = QCheckBox("导出时调整图片尺寸")
        self.resize_check.toggled.connect(self.on_resize_toggled)
        
        # 尺寸调整选项
        resize_options_layout = QGridLayout()
        
        self.radio_width = QRadioButton("按宽度:")
        self.radio_height = QRadioButton("按高度:")
        self.radio_percent = QRadioButton("按百分比:")
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(1920)
        self.width_spin.setEnabled(False)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(1080)
        self.height_spin.setEnabled(False)
        
        self.percent_spin = QSpinBox()
        self.percent_spin.setRange(1, 200)
        self.percent_spin.setValue(100)
        self.percent_spin.setEnabled(False)
        
        # 连接信号
        self.radio_width.toggled.connect(self.on_resize_option_changed)
        self.radio_height.toggled.connect(self.on_resize_option_changed)
        self.radio_percent.toggled.connect(self.on_resize_option_changed)
        
        resize_options_layout.addWidget(self.radio_width, 0, 0)
        resize_options_layout.addWidget(self.width_spin, 0, 1)
        resize_options_layout.addWidget(QLabel("像素"), 0, 2)
        
        resize_options_layout.addWidget(self.radio_height, 1, 0)
        resize_options_layout.addWidget(self.height_spin, 1, 1)
        resize_options_layout.addWidget(QLabel("像素"), 1, 2)
        
        resize_options_layout.addWidget(self.radio_percent, 2, 0)
        resize_options_layout.addWidget(self.percent_spin, 2, 1)
        resize_options_layout.addWidget(QLabel("%"), 2, 2)
        
        # 默认选中按百分比100%
        self.radio_percent.setChecked(True)
        
        resize_layout.addWidget(self.resize_check)
        resize_layout.addLayout(resize_options_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        
        # 连接信号
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        # 添加到主布局
        main_layout.addWidget(format_group)
        main_layout.addWidget(naming_group)
        main_layout.addWidget(quality_group)
        main_layout.addWidget(resize_group)
        main_layout.addLayout(button_layout)
        
        # 初始化状态
        self.on_format_changed(self.format_combo.currentText())
    
    def on_format_changed(self, format_text):
        """输出格式改变时的处理"""
        # 只有JPEG格式才启用质量设置
        is_jpeg = format_text.lower() == "jpeg"
        
        # 查找质量设置组并更新启用状态
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if isinstance(item.widget(), QGroupBox) and item.widget().title() == "JPEG 质量":
                item.widget().setEnabled(is_jpeg)
                break
    
    def on_naming_rule_changed(self):
        """命名规则改变时的处理"""
        self.prefix_input.setEnabled(self.radio_prefix.isChecked())
        self.suffix_input.setEnabled(self.radio_suffix.isChecked())
    
    def on_resize_toggled(self, checked):
        """调整尺寸选项切换时的处理"""
        # 启用或禁用所有尺寸调整选项
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if isinstance(item.widget(), QGroupBox) and item.widget().title() == "调整尺寸":
                # 获取内部布局
                resize_layout = item.widget().layout()
                for j in range(1, resize_layout.count()):  # 跳过第一个（复选框）
                    sub_item = resize_layout.itemAt(j)
                    if sub_item.widget():
                        sub_item.widget().setEnabled(checked)
                    elif sub_item.layout():
                        # 启用/禁用网格布局中的所有控件
                        for k in range(sub_item.layout().count()):
                            grid_item = sub_item.layout().itemAt(k)
                            if grid_item.widget():
                                grid_item.widget().setEnabled(checked)
                break
        
        # 如果启用了调整尺寸，确保至少有一个选项被选中
        if checked:
            if not (self.radio_width.isChecked() or self.radio_height.isChecked() or self.radio_percent.isChecked()):
                self.radio_percent.setChecked(True)
    
    def on_resize_option_changed(self):
        """尺寸调整选项改变时的处理"""
        self.width_spin.setEnabled(self.radio_width.isChecked())
        self.height_spin.setEnabled(self.radio_height.isChecked())
        self.percent_spin.setEnabled(self.radio_percent.isChecked())
    
    def get_naming_rule(self):
        """获取命名规则设置"""
        if self.radio_original.isChecked():
            return {"type": "original", "value": ""}
        elif self.radio_prefix.isChecked():
            return {"type": "prefix", "value": self.prefix_input.text()}
        elif self.radio_suffix.isChecked():
            return {"type": "suffix", "value": self.suffix_input.text()}
        
        # 默认返回原始名称
        return {"type": "original", "value": ""}
    
    def get_resize_option(self):
        """获取尺寸调整选项"""
        if not self.resize_check.isChecked():
            return None
        
        if self.radio_width.isChecked():
            return ("width", self.width_spin.value())
        elif self.radio_height.isChecked():
            return ("height", self.height_spin.value())
        elif self.radio_percent.isChecked():
            return ("percent", self.percent_spin.value())
        
        return None