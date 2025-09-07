# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'knowledge_manager.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QPushButton,
    QSizePolicy, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_KnowledgeManager(object):
    def setupUi(self, KnowledgeManager):
        if not KnowledgeManager.objectName():
            KnowledgeManager.setObjectName(u"KnowledgeManager")
        KnowledgeManager.resize(800, 600)
        self.centralwidget = QWidget(KnowledgeManager)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.title_label = QLabel(self.centralwidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setFamilies([u"\u963f\u91cc\u5df4\u5df4\u666e\u60e0\u4f53 M"])
        font.setPointSize(16)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.title_label)

        self.search_frame = QFrame(self.centralwidget)
        self.search_frame.setObjectName(u"search_frame")
        self.search_frame.setMaximumSize(QSize(16777215, 50))
        self.horizontalLayout = QHBoxLayout(self.search_frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.search_label = QLabel(self.search_frame)
        self.search_label.setObjectName(u"search_label")
        font1 = QFont()
        font1.setFamilies([u"\u963f\u91cc\u5df4\u5df4\u666e\u60e0\u4f53 R"])
        font1.setPointSize(10)
        self.search_label.setFont(font1)

        self.horizontalLayout.addWidget(self.search_label)

        self.search_input = QLineEdit(self.search_frame)
        self.search_input.setObjectName(u"search_input")
        self.search_input.setMaximumSize(QSize(300, 30))
        self.search_input.setFont(font1)

        self.horizontalLayout.addWidget(self.search_input)

        self.search_button = QPushButton(self.search_frame)
        self.search_button.setObjectName(u"search_button")
        self.search_button.setMaximumSize(QSize(80, 30))
        self.search_button.setFont(font1)
        self.search_button.setStyleSheet(u"background-color: rgb(0, 150, 255); color: white;")

        self.horizontalLayout.addWidget(self.search_button)

        self.refresh_button = QPushButton(self.search_frame)
        self.refresh_button.setObjectName(u"refresh_button")
        self.refresh_button.setMaximumSize(QSize(80, 30))
        self.refresh_button.setFont(font1)
        self.refresh_button.setStyleSheet(u"background-color: rgb(100, 100, 100); color: white;")

        self.horizontalLayout.addWidget(self.refresh_button)

        self.verticalLayout.addWidget(self.search_frame)

        self.table_widget = QTableWidget(self.centralwidget)
        if (self.table_widget.columnCount() < 4):
            self.table_widget.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.table_widget.setObjectName(u"table_widget")
        self.table_widget.setFont(font1)
        self.table_widget.setStyleSheet(u"QTableWidget { background-color: white; }")

        self.verticalLayout.addWidget(self.table_widget)

        self.detail_frame = QFrame(self.centralwidget)
        self.detail_frame.setObjectName(u"detail_frame")
        self.detail_frame.setMaximumSize(QSize(16777215, 200))
        self.verticalLayout_2 = QVBoxLayout(self.detail_frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.detail_label = QLabel(self.detail_frame)
        self.detail_label.setObjectName(u"detail_label")
        self.detail_label.setFont(font1)

        self.verticalLayout_2.addWidget(self.detail_label)

        self.knowledge_text = QTextEdit(self.detail_frame)
        self.knowledge_text.setObjectName(u"knowledge_text")
        self.knowledge_text.setFont(font1)
        self.knowledge_text.setReadOnly(True)

        self.verticalLayout_2.addWidget(self.knowledge_text)

        self.verticalLayout.addWidget(self.detail_frame)

        self.button_frame = QFrame(self.centralwidget)
        self.button_frame.setObjectName(u"button_frame")
        self.button_frame.setMaximumSize(QSize(16777215, 60))
        self.horizontalLayout_2 = QHBoxLayout(self.button_frame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.delete_button = QPushButton(self.button_frame)
        self.delete_button.setObjectName(u"delete_button")
        self.delete_button.setMaximumSize(QSize(100, 40))
        self.delete_button.setFont(font1)
        self.delete_button.setStyleSheet(u"background-color: rgb(255, 80, 80); color: white;")

        self.horizontalLayout_2.addWidget(self.delete_button)

        self.edit_button = QPushButton(self.button_frame)
        self.edit_button.setObjectName(u"edit_button")
        self.edit_button.setMaximumSize(QSize(100, 40))
        self.edit_button.setFont(font1)
        self.edit_button.setStyleSheet(u"background-color: rgb(0, 150, 255); color: white;")

        self.horizontalLayout_2.addWidget(self.edit_button)

        self.close_button = QPushButton(self.button_frame)
        self.close_button.setObjectName(u"close_button")
        self.close_button.setMaximumSize(QSize(100, 40))
        self.close_button.setFont(font1)
        self.close_button.setStyleSheet(u"background-color: rgb(100, 100, 100); color: white;")

        self.horizontalLayout_2.addWidget(self.close_button)

        self.verticalLayout.addWidget(self.button_frame)

        KnowledgeManager.setCentralWidget(self.centralwidget)

        self.retranslateUi(KnowledgeManager)

        QMetaObject.connectSlotsByName(KnowledgeManager)
    # setupUi

    def retranslateUi(self, KnowledgeManager):
        KnowledgeManager.setWindowTitle(QCoreApplication.translate("KnowledgeManager", u"\u5546\u54c1\u77e5\u8bc6\u5e93\u7ba1\u7406", None))
        self.title_label.setText(QCoreApplication.translate("KnowledgeManager", u"\u5546\u54c1\u77e5\u8bc6\u5e93\u7ba1\u7406", None))
        self.search_label.setText(QCoreApplication.translate("KnowledgeManager", u"\u641c\u7d22\uff1a", None))
        self.search_input.setPlaceholderText(QCoreApplication.translate("KnowledgeManager", u"\u8f93\u5165\u5546\u54c1\u540d\u79f0\u6216\u94fe\u63a5", None))
        self.search_button.setText(QCoreApplication.translate("KnowledgeManager", u"\u641c\u7d22", None))
        self.refresh_button.setText(QCoreApplication.translate("KnowledgeManager", u"\u5237\u65b0", None))
        ___qtablewidgetitem = self.table_widget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("KnowledgeManager", u"ID", None));
        ___qtablewidgetitem1 = self.table_widget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("KnowledgeManager", u"\u5546\u54c1\u540d\u79f0", None));
        ___qtablewidgetitem2 = self.table_widget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("KnowledgeManager", u"\u5546\u54c1\u94fe\u63a5", None));
        ___qtablewidgetitem3 = self.table_widget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("KnowledgeManager", u"\u66f4\u65b0\u65f6\u95f4", None));
        self.detail_label.setText(QCoreApplication.translate("KnowledgeManager", u"\u77e5\u8bc6\u5e93\u5185\u5bb9\uff1a", None))
        self.delete_button.setText(QCoreApplication.translate("KnowledgeManager", u"\u5220\u9664", None))
        self.edit_button.setText(QCoreApplication.translate("KnowledgeManager", u"\u7f16\u8f91", None))
        self.close_button.setText(QCoreApplication.translate("KnowledgeManager", u"\u5173\u95ed", None))
    # retranslateUi
