from src.ui.knowledge_manager import Ui_KnowledgeManager
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem
from PySide6 import QtCore, QtGui

class KnowledgeManager(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.ui = Ui_KnowledgeManager()
        self.ui.setupUi(self)
        
        # 设置无标题窗口
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # 设置背景透明
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        # 绑定事件
        self.ui.close_button.clicked.connect(self.close)
        self.ui.refresh_button.clicked.connect(self.load_data)
        self.ui.search_button.clicked.connect(self.search_data)
        self.ui.delete_button.clicked.connect(self.delete_selected)
        self.ui.edit_button.clicked.connect(self.edit_selected)
        self.ui.table_widget.itemSelectionChanged.connect(self.show_details)
        
        # 加载数据
        self.load_data()
        
        self.show()

    def load_data(self):
        """加载所有商品知识库数据"""
        try:
            knowledge_list = self.db.get_all_product_knowledge()
            self.ui.table_widget.setRowCount(len(knowledge_list))
            
            for row, item in enumerate(knowledge_list):
                self.ui.table_widget.setItem(row, 0, QTableWidgetItem(str(item['id'])))
                self.ui.table_widget.setItem(row, 1, QTableWidgetItem(item['product_name']))
                self.ui.table_widget.setItem(row, 2, QTableWidgetItem(item['product_url']))
                # 更新时间暂时留空，因为数据库中没有这个字段
                self.ui.table_widget.setItem(row, 3, QTableWidgetItem(""))
            
            # 设置列宽
            self.ui.table_widget.setColumnWidth(0, 50)
            self.ui.table_widget.setColumnWidth(1, 150)
            self.ui.table_widget.setColumnWidth(2, 300)
            self.ui.table_widget.setColumnWidth(3, 120)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {str(e)}")

    def search_data(self):
        """搜索商品知识库"""
        search_text = self.ui.search_input.text().strip()
        if not search_text:
            self.load_data()
            return
            
        try:
            knowledge_list = self.db.get_all_product_knowledge()
            filtered_list = [
                item for item in knowledge_list 
                if search_text.lower() in item['product_name'].lower() 
                or search_text.lower() in item['product_url'].lower()
            ]
            
            self.ui.table_widget.setRowCount(len(filtered_list))
            
            for row, item in enumerate(filtered_list):
                self.ui.table_widget.setItem(row, 0, QTableWidgetItem(str(item['id'])))
                self.ui.table_widget.setItem(row, 1, QTableWidgetItem(item['product_name']))
                self.ui.table_widget.setItem(row, 2, QTableWidgetItem(item['product_url']))
                self.ui.table_widget.setItem(row, 3, QTableWidgetItem(""))
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {str(e)}")

    def show_details(self):
        """显示选中项的详细信息"""
        current_row = self.ui.table_widget.currentRow()
        if current_row >= 0:
            try:
                item_id = int(self.ui.table_widget.item(current_row, 0).text())
                knowledge_list = self.db.get_all_product_knowledge()
                selected_item = next((item for item in knowledge_list if item['id'] == item_id), None)
                
                if selected_item:
                    self.ui.knowledge_text.setPlainText(selected_item['knowledge_content'])
                else:
                    self.ui.knowledge_text.clear()
            except Exception:
                self.ui.knowledge_text.clear()
        else:
            self.ui.knowledge_text.clear()

    def delete_selected(self):
        """删除选中的知识库记录"""
        current_row = self.ui.table_widget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的记录")
            return
            
        try:
            item_id = int(self.ui.table_widget.item(current_row, 0).text())
            item_name = self.ui.table_widget.item(current_row, 1).text()
            
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除商品 '{item_name}' 的知识库记录吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.db.delete_product_knowledge(item_id)
                if success:
                    QMessageBox.information(self, "成功", "删除成功")
                    self.load_data()
                else:
                    QMessageBox.critical(self, "错误", "删除失败")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def edit_selected(self):
        """编辑选中的知识库记录"""
        current_row = self.ui.table_widget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要编辑的记录")
            return
            
        try:
            item_id = int(self.ui.table_widget.item(current_row, 0).text())
            item_name = self.ui.table_widget.item(current_row, 1).text()
            new_content = self.ui.knowledge_text.toPlainText().strip()
            
            if not new_content:
                QMessageBox.warning(self, "警告", "知识库内容不能为空")
                return
                
            # 更新知识库
            success = self.db.update_product_knowledge(item_id, new_content)
            if success:
                QMessageBox.information(self, "成功", "知识库内容已更新")
                self.load_data()
            else:
                QMessageBox.critical(self, "错误", "更新失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.isMaximized() == False:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()
            event.accept()
            self.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))

    def mouseMoveEvent(self, mouse_event):
        if QtCore.Qt.LeftButton and self.m_flag:
            self.move(mouse_event.globalPos() - self.m_Position)
            mouse_event.accept()

    def mouseReleaseEvent(self, mouse_event):
        self.m_flag = False
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
