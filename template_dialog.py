#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
template_dialog.py - 模板管理对话框
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget
)
from PyQt5.QtCore import Qt


class TemplateDialog(QDialog):
    """模板管理对话框"""
    
    def __init__(self, parent=None, dialog_type="save"):
        """
        初始化模板对话框
        
        Args:
            parent: 父窗口
            dialog_type: 对话框类型，'save' 保存模板或 'load' 加载模板
        """
        super().__init__(parent)
        self.dialog_type = dialog_type
        
        if dialog_type == "save":
            self.setWindowTitle("保存模板")
        else:
            self.setWindowTitle("加载模板")
        
        self.resize(350, 250)
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        
        if self.dialog_type == "save":
            # 保存模板界面
            main_layout.addWidget(QLabel("请输入模板名称:"))
            
            self.template_name = QLineEdit()
            self.template_name.setPlaceholderText("输入模板名称...")
            self.template_name.setFocus()
            
            main_layout.addWidget(self.template_name)
            
            # 显示现有模板列表
            main_layout.addWidget(QLabel("现有模板:"))
            self.existing_templates = QListWidget()
            self.load_existing_templates()
            self.existing_templates.itemClicked.connect(self.on_template_selected)
            
            main_layout.addWidget(self.existing_templates)
        else:
            # 加载模板界面
            main_layout.addWidget(QLabel("请选择要加载的模板:"))
            
            self.template_list = QListWidget()
            self.load_existing_templates()
            self.template_list.setCurrentRow(0)  # 默认选中第一个
            
            main_layout.addWidget(self.template_list)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        
        # 连接信号
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        main_layout.addLayout(button_layout)
    
    def load_existing_templates(self):
        """加载现有模板列表"""
        # 从父窗口获取设置对象
        if self.parent() and hasattr(self.parent(), 'settings'):
            settings = self.parent().settings
            
            # 获取所有模板名称
            template_names = set()
            for key in settings.allKeys():
                if key.startswith("templates/"):
                    parts = key.split("/")
                    if len(parts) >= 2:
                        template_names.add(parts[1])
            
            # 添加到列表
            if self.dialog_type == "save":
                for name in sorted(template_names):
                    self.existing_templates.addItem(name)
            else:
                for name in sorted(template_names):
                    self.template_list.addItem(name)
    
    def on_template_selected(self, item):
        """当选择现有模板时，将其名称填充到输入框"""
        if item and self.dialog_type == "save":
            self.template_name.setText(item.text())
    
    def get_selected_template(self):
        """获取选中的模板名称"""
        if self.dialog_type == "save":
            return self.template_name.text().strip()
        else:
            selected_item = self.template_list.currentItem()
            if selected_item:
                return selected_item.text()
        return ""
    
    def accept(self):
        """确认按钮处理"""
        if self.dialog_type == "save":
            # 检查模板名称是否为空
            template_name = self.template_name.text().strip()
            if not template_name:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "警告", "模板名称不能为空")
                return
            
            # 检查是否与现有模板重名
            if self.parent() and hasattr(self.parent(), 'settings'):
                settings = self.parent().settings
                if settings.contains(f"templates/{template_name}/type"):
                    from PyQt5.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self, "确认覆盖", 
                        f"模板 '{template_name}' 已存在，是否覆盖？",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
        
        super().accept()