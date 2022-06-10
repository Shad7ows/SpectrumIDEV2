######################################################################
# استيراد المكاتب
######################################################################

from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QToolBar, QVBoxLayout, QHBoxLayout, QTabWidget, \
    QDockWidget, QFileDialog, QMessageBox, QStatusBar, QLabel, QTreeView, QDialog, QFrame, QPushButton
from PyQt6.QtGui import QIcon, QFont, QAction, QFontDatabase, QFileSystemModel, QPixmap
from PyQt6.QtCore import Qt, QProcess, QTimer, QObject, pyqtSignal, pyqtSlot, QThread, QDir
from tempfile import gettempdir
import CodeEditor
from Console import Consol, InputLine
import sys
import os

try:
    from ctypes import windll

    appID = 'com.Shad7ows.SpectrumIDE.V2'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID)
except ImportError:
    print('Can\'t import ctypes lib')


######################################################################
# الصنف الرئيسي
######################################################################

class MainWin(QMainWindow):
    def __init__(self):
        super(MainWin, self).__init__()
        self.resize(1280, 720)
        self.setWindowTitle("طيف")
        self.setWindowIcon(QIcon('./icons/TaifLogo.svg'))
        self.version = '0.4.5'
        self.set_fonts_database()

        self.centerWidget = QWidget(self)

        # self.setStyleSheet('QMenu::item::selected {background-color: red; color: yellow}')

        self.codeLay = QVBoxLayout(self.centerWidget)
        self.codeLay.setContentsMargins(0, 0, 0, 0)

        self.fileModel = QFileSystemModel()
        self.fileModel.setRootPath(QDir.currentPath())
        self.fileView = QTreeView()
        self.fileView.doubleClicked.connect(lambda idx: self.open_selected_file(idx))
        self.fileView.setModel(self.fileModel)
        # self.fileView.setRootIndex(self.fileModel.index((QDir.currentPath())))

        self.fileWidget = QDockWidget('مسار المشروع')
        self.fileWidget.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.fileWidget)
        self.fileWidget.setWidget(self.fileView)

        self.codeWin = CodeEditor.CodeEditor()

        self.tabWin = QTabWidget()
        self.tabWin.setTabsClosable(True)
        self.tabWin.setMovable(True)
        self.tabWin.tabCloseRequested.connect(lambda idx: self.close_tab(idx))
        self.new_file(False)

        self.consoleWidget = QWidget()
        self.consoleLayout = QVBoxLayout()
        self.consoleLayout.setContentsMargins(0, 0, 0, 0)
        self.resultWin = Consol()
        self.inputLine = InputLine()

        self.dockWin = QDockWidget('الطرفية')
        self.dockWin.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dockWin)
        self.dockWin.setWidget(self.consoleWidget)
        self.consoleWidget.setLayout(self.consoleLayout)
        self.consoleLayout.addWidget(self.resultWin)
        self.consoleLayout.addWidget(self.inputLine)

        self.charCount = CharCont(self)
        self.alif_version()

        self.setCentralWidget(self.centerWidget)
        self.codeLay.addWidget(self.tabWin)

        self._Actions()
        self._menu_bar()
        self._tool_bar()
        self._status_bar()

        ######################################################################
        # المتغيرات
        ######################################################################

        self.tempFile = gettempdir()
        self.filePath = ''
        self.tabName = []
        self.compileResult = 1

        ######################################################################
        # الدوال
        ######################################################################

    def set_fonts_database(self):
        fontsDir = 'fonts'
        for font in os.listdir(fontsDir):
            QFontDatabase.addApplicationFont(os.path.join(fontsDir, font))

    def _menu_bar(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&ملف')
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.settingAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitApp)

        examplesMenu = menuBar.addMenu('أمثلة')
        examplesMenu.addAction(self.printExampleAction)
        examplesMenu.addAction(self.importExampleAction)
        examplesMenu.addAction(self.varExampleAction)
        examplesMenu.addAction(self.mathExampleAction)
        examplesMenu.addAction(self.funcExampleAction)
        examplesMenu.addAction(self.ifExampleAction)
        examplesMenu.addAction(self.whileExampleAction)
        examplesMenu.addAction(self.inputExampleAction)
        examplesMenu.addAction(self.classExampleAction)
        examplesMenu.addAction(self.cppExampleAction)

        helpMenu = menuBar.addMenu('مساعدة')
        helpMenu.addAction(self.helpDialogAction)

    def _tool_bar(self):
        runToolBar = QToolBar('تشغيل')
        self.addToolBar(Qt.ToolBarArea.RightToolBarArea, runToolBar)
        runToolBar.setMovable(False)
        runToolBar.addAction(self.compileAction)
        runToolBar.addAction(self.runAction)

    def _Actions(self):
        self.newAction = QAction(QIcon('./icons/add_black.svg'), '&جديد', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('فتح تبويب جديد... ')
        self.newAction.triggered.connect(lambda clear: self.new_file(True))

        self.openAction = QAction(QIcon('./icons/folder_open_black.svg'), '&فتح', self)
        self.openAction.setShortcut("Ctrl+O")
        self.openAction.setStatusTip('فتح ملف... ')
        self.openAction.triggered.connect(self.open_file)

        self.saveAction = QAction(QIcon('./icons/save_black.svg'), '&حفظ', self)
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.setStatusTip('حفظ شفرة التبويب الحالي... ')
        self.saveAction.triggered.connect(self.save_file)

        self.settingAction = QAction('&إعدادات', self)
        self.settingAction.setShortcut('Ctrl+E')
        self.settingAction.setStatusTip('الإعدادات...')
        self.settingAction.triggered.connect(self.setting_Dialog)

        self.exitApp = QAction("خروج", self)
        self.exitApp.setStatusTip("الخروج من البرنامج... ")
        self.exitApp.triggered.connect(self.exit_app)

        self.compileAction = QAction(QIcon('./icons/compile_black.svg'), 'ترجمة', self)
        self.compileAction.setShortcut('Ctrl+f2')
        self.compileAction.setStatusTip('بناء شفرة التبويب الحالي... ')
        self.compileAction.triggered.connect(self.compile_thread_task)

        self.runAction = QAction(QIcon('./icons/run_arrow.svg'), 'تشغيل', self)
        self.runAction.setShortcut('Ctrl+f10')
        self.runAction.setStatusTip('تنفيذ الشفرة التي تم بناؤها... ')
        self.runAction.triggered.connect(self.run_thread_task)

        self.printExampleAction = QAction('دالة طباعة', self)
        self.printExampleAction.setStatusTip('فتح مثال "دالة طباعة.alif"')
        self.printExampleAction.triggered.connect(self.print_example)

        self.importExampleAction = QAction('استيراد مكتبة', self)
        self.importExampleAction.setStatusTip('فتح مثال "استيراد مكتبة.alif"')
        self.importExampleAction.triggered.connect(self.import_example)

        self.varExampleAction = QAction('تعريف متغير', self)
        self.varExampleAction.setStatusTip('فتح مثال "تعريف متغير.alif"')
        self.varExampleAction.triggered.connect(self.var_example)

        self.mathExampleAction = QAction('العمليات الحسابية', self)
        self.mathExampleAction.setStatusTip('فتح مثال "العمليات الحسابية.alif"')
        self.mathExampleAction.triggered.connect(self.math_example)

        self.funcExampleAction = QAction('تعريف دالة', self)
        self.funcExampleAction.setStatusTip('فتح مثال "تعريف دالة.alif"')
        self.funcExampleAction.triggered.connect(self.func_example)

        self.ifExampleAction = QAction('إذا الشرطية', self)
        self.ifExampleAction.setStatusTip('فتح مثال "إذا الشرطية.alif"')
        self.ifExampleAction.triggered.connect(self.if_example)

        self.whileExampleAction = QAction('حلقة كلما', self)
        self.whileExampleAction.setStatusTip('فتح مثال "حلقة كلما.alif"')
        self.whileExampleAction.triggered.connect(self.while_example)

        self.inputExampleAction = QAction('طلب بيانات من المستخدم', self)
        self.inputExampleAction.setStatusTip('فتح مثال "طلب بيانات من المستخدم.alif"')
        self.inputExampleAction.triggered.connect(self.input_example)

        self.classExampleAction = QAction('تعريف صنف', self)
        self.classExampleAction.setStatusTip('فتح مثال "تعريف صنف.alif"')
        self.classExampleAction.triggered.connect(self.class_example)

        self.cppExampleAction = QAction('C++ حقن لغة', self)
        self.cppExampleAction.setStatusTip('فتح مثال "C++ حقن لغة.alif"')
        self.cppExampleAction.triggered.connect(self.cpp_injection_example)

        self.helpDialogAction = QAction("حول", self)
        self.helpDialogAction.setStatusTip("عن برنامج طيف... ")
        self.helpDialogAction.triggered.connect(self.info_dialog)

    def _status_bar(self):
        self.stateBar = QStatusBar()
        self.setStatusBar(self.stateBar)
        self.stateBar.addPermanentWidget(self.charCount.charCountLable)

    def setting_Dialog(self):
        settingDialog = QDialog()
        settingDialog.setContentsMargins(0, 0, 0, 0)
        settingDialog.setWindowTitle('إعدادات')
        settingDialog.setWindowIcon(QIcon('./icons/TaifLogo.svg'))

        settingLayout = QHBoxLayout()
        settingLayout.setContentsMargins(0, 0, 0, 0)
        settingDialog.setLayout(settingLayout)

        menuFrame = QFrame()
        menuLayout = QVBoxLayout()
        menuLayout.setContentsMargins(0, 0, 0, 0)
        menuFrame.setLayout(menuLayout)

        editorButton = QPushButton('المحرر')
        editorButton.setFixedWidth(192)
        editorButton.setFlat(True)

        proparityFrame = QFrame()
        proparityFrame.setMinimumWidth(512)
        proparityLayout = QVBoxLayout()
        proparityFrame.setLayout(proparityLayout)

        settingLayout.addWidget(menuFrame)
        settingLayout.addWidget(proparityFrame)
        menuLayout.addWidget(editorButton)


        settingDialog.exec()

    def info_dialog(self):
        dialog = QDialog()
        dialog.setWindowTitle("عن طيف")
        dialog.setWindowIcon(QIcon('./icons/TaifLogo.svg'))

        with open('About.sha', 'r', encoding="utf-8") as About:
            about = About.read()
            About.close()

        infoLayout = QHBoxLayout()
        infoLabel = QLabel(about)
        infoLabel.setContentsMargins(8, 8, 16, 8)

        imageLable = QLabel()
        imageLable.setContentsMargins(8, 8, 8, 8)
        taifLogo = QPixmap("icons/TaifLogo.png")
        imageLable.setPixmap(taifLogo)

        dialog.setLayout(infoLayout)
        infoLayout.addWidget(imageLable)
        infoLayout.addWidget(infoLabel)

        dialog.exec()

    def close_tab(self, idx):
        if self.is_saved(idx):
            self.tabWin.removeTab(idx)
        if self.tabWin.tabText(idx) in self.tabName:
            self.tabName.remove(self.tabWin.tabText(idx))

    def open_selected_file(self, idx):
        filePath = self.fileModel.filePath(idx)
        fileExtention = filePath.split('.')[-1]
        if fileExtention == 'alif':
            if filePath in self.tabName:
                self.set_tab_by_name(filePath)
                idx = self.tabWin.currentIndex()
                self.is_saved(idx)
            else:
                self.new_file(True)
                with open(filePath, "r", encoding="utf-8") as openFile:
                    fileCode = openFile.read()
                    self.tabWin.currentWidget().setPlainText(fileCode)
                    openFile.close()
                self.tabWin.setTabText(self.tabWin.currentIndex(), filePath)
                self.tabName.append(filePath)

    def new_file(self, clear):
        codeWin = CodeEditor.CodeEditor()
        if clear:
            codeWin.clear()
        if self.tabWin.count() <= 4:
            self.tabWin.addTab(codeWin, 'غير معنون')
            self.tabWin.setCurrentWidget(codeWin)

    def open_file(self):
        self.filePath, _ = QFileDialog.getOpenFileName(self, "فتح ملف ألف", "", "كل الملفات (*.alif)")
        if self.filePath:
            if self.filePath in self.tabName:
                self.set_tab_by_name(self.filePath)
                idx = self.tabWin.currentIndex()
                self.is_saved(idx)
            else:
                self.new_file(True)
                with open(self.filePath, "r", encoding="utf-8") as openFile:
                    fileCode = openFile.read()
                    self.tabWin.currentWidget().setPlainText(fileCode)
                    openFile.close()
                self.tabWin.setTabText(self.tabWin.currentIndex(), self.filePath)
                self.tabName.append(self.filePath)

    def set_tab_by_name(self, pathName):
        for indx in range(self.tabWin.count()):
            tabName = self.tabWin.tabText(indx)
            if pathName == tabName:
                return self.tabWin.setCurrentIndex(indx)

    def save_file(self, idx):
        tabChild = self.tabWin.widget(idx)
        alifCode = tabChild.toPlainText()

        if self.tabWin.tabText(idx) != 'غير معنون':
            with open(self.tabWin.tabText(idx), "w", encoding="utf-8") as saveFile:
                saveFile.write(alifCode)
                saveFile.close()
        else:
            self.filePath, _ = QFileDialog.getSaveFileName(self, "حفظ ملف ألف", "غير معنون.alif", "ملف ألف (*.alif)")
            if self.filePath:
                with open(self.filePath, "w", encoding="utf-8") as saveFile:
                    saveFile.write(alifCode)
                    saveFile.close()
                self.tabWin.setTabText(idx, self.filePath)
                self.tabName.append(self.filePath)
            else:
                return ''

    def is_saved(self, idx):
        if self.tabWin.widget(idx).document().isModified():
            result = self.msg_box("حفظ الملف", "هل تريد حفظ الملف؟", "حفظ", "عدم الحفظ", "إلغاء")
            if result == 0:
                self.save_file(idx)
                if not self.filePath:
                    return False
            elif result == 2:
                return False
        return True

    def msg_box(self, title, text, firstBtn, secondBtn, therdBtn):
        msgBox = QMessageBox()
        msgBox.addButton(firstBtn, QMessageBox.ButtonRole.YesRole)
        msgBox.addButton(secondBtn, QMessageBox.ButtonRole.NoRole)
        msgBox.addButton(therdBtn, QMessageBox.ButtonRole.RejectRole)
        msgBox.setWindowTitle(title)
        msgBox.setWindowIcon(QIcon("./Icons/TaifLogo.svg"))
        msgBox.setText(text)
        msgBox.exec()
        return msgBox.result()

    def compile_thread_task(self):
        self.compileThread = CompileThread()
        self.thread = QThread()
        self.compileThread.moveToThread(self.thread)
        self.thread.started.connect(self.compileThread.run)
        self.compileThread.resultSignal.connect(self.code_compile)
        self.thread.start()
        self.compileAction.setEnabled(False)
        self.runAction.setEnabled(False)
        self.thread.finished.connect(lambda: self.compileAction.setEnabled(True))
        self.thread.finished.connect(lambda: self.runAction.setEnabled(True))

    def run_thread_task(self):
        self.runThread = RunThread()
        self.thread = QThread()
        self.runThread.moveToThread(self.thread)
        self.thread.started.connect(self.runThread.run)
        self.runThread.readDataSignal.connect(self.run_code)
        self.thread.start()
        self.compileAction.setEnabled(False)
        self.runAction.setEnabled(False)
        self.thread.finished.connect(lambda: self.compileAction.setEnabled(True))
        self.thread.finished.connect(lambda: self.runAction.setEnabled(True))

    @pyqtSlot(int, float)
    def code_compile(self, compileResult: int, build_time: float):
        self.compileResult = compileResult

        if compileResult == 0:
            self.resultWin.setPlainText(f"[انتهى البناء خلال: {build_time} ثانية]")
        elif compileResult == 1:
            log = os.path.join(self.tempFile, "temp.alif.log")
            logOpen = open(log, "r", encoding="utf-8")
            self.resultWin.setPlainText(logOpen.read())
            logOpen.close()
        elif compileResult == -2:
            self.resultWin.setPlainText("تحقق من أن لغة ألف 3 مثبتة بشكل صحيح")

    @pyqtSlot(str)
    def run_code(self, data: str):
        self.resultWin.appendPlainText(data)

    def print_example(self):
        PlainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(PlainTextExample, 'دالة طباعة.alif')
        self.tabWin.setCurrentWidget(PlainTextExample)
        with open("./example/دالة طباعة.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def import_example(self):
        PlainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(PlainTextExample, 'استيراد مكتبة.alif')
        self.tabWin.setCurrentWidget(PlainTextExample)
        with open("./example/استيراد مكتبة.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def var_example(self):
        plainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(plainTextExample, 'تعريف متغير.alif')
        self.tabWin.setCurrentWidget(plainTextExample)
        with open("./example/تعريف متغير.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def math_example(self):
        plainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(plainTextExample, 'العمليات الحسابية.alif')
        self.tabWin.setCurrentWidget(plainTextExample)
        with open("./example/العمليات الحسابية.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def func_example(self):
        plainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(plainTextExample, 'تعريف دالة.alif')
        self.tabWin.setCurrentWidget(plainTextExample)
        with open("./example/تعريف دالة.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def if_example(self):
        plainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(plainTextExample, 'إذا الشرطية.alif')
        self.tabWin.setCurrentWidget(plainTextExample)
        with open("./example/إذا الشرطية.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def while_example(self):
        plainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(plainTextExample, 'حلقة كلما.alif')
        self.tabWin.setCurrentWidget(plainTextExample)
        with open("./example/حلقة كلما.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def input_example(self):
        plainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(plainTextExample, 'طلب بيانات من المستخدم.alif')
        self.tabWin.setCurrentWidget(plainTextExample)
        with open("./example/طلب بيانات من المستخدم.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def class_example(self):
        plainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(plainTextExample, 'تعريف صنف.alif')
        self.tabWin.setCurrentWidget(plainTextExample)
        with open("./example/تعريف صنف.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def cpp_injection_example(self):
        plainTextExample = CodeEditor.CodeEditor()
        self.tabWin.addTab(plainTextExample, 'C++ حقن لغة.alif')
        self.tabWin.setCurrentWidget(plainTextExample)
        with open("./example/C++ حقن لغة.alif", "r", encoding="utf-8") as example:
            exampleRead = example.read()
            self.tabWin.currentWidget().setPlainText(exampleRead)
            example.close()

    def alif_version(self):
        alifVersion = '--v'
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.alif_version_statusbar)
        self.process.start("alif", [alifVersion])

    def alif_version_statusbar(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        stdout = stdout.split(' ')
        stdout = stdout[2].strip('v')
        stdout = f'ألف {stdout}'
        versionLable = QLabel(stdout)
        versionLable.setFont(QFont('Alusus Mono Medium'))
        self.stateBar.addPermanentWidget(versionLable)

    def exit_app(self):
        sys.exit(app)


######################################################################
# مسلك الترجمة
######################################################################

class CompileThread(QObject):
    resultSignal = pyqtSignal(int, float)

    def __init__(self):
        super(CompileThread, self).__init__()

    def run(self):
        timer = QTimer()
        timer.start(60000)

        code = mainWin.tabWin.currentWidget().toPlainText()
        tempFile = mainWin.tempFile

        with open(os.path.join(tempFile, "temp.alif"), "w", encoding="utf-8") as temporaryFile:
            temporaryFile.write(code)
            temporaryFile.close()

        process = QProcess()
        alifCodeCompile = os.path.join(tempFile, "temp.alif")
        compileResult = process.execute("alif", [alifCodeCompile])
        process.kill()

        remineTime = timer.remainingTime()
        buildTime = (60000 - remineTime) / 1000
        timer.stop()

        self.resultSignal.emit(compileResult, buildTime)
        mainWin.thread.quit()


######################################################################
# مسلك التشغيل
######################################################################

class RunThread(QObject):
    readDataSignal = pyqtSignal(str)

    def __init__(self):
        super(RunThread, self).__init__()
        mainWin.inputLine.returnPressed.connect(self.wait_input)
        self.process = None

    def run(self):
        compileResult = mainWin.compileResult
        tempFile = mainWin.tempFile

        if compileResult == 0:
            if sys.platform == "linux":
                self.process = QProcess()
                self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
                self.process.readyRead.connect(self.ifReadReady)
                self.process.start(os.path.join(tempFile, "./temp"))
            else:
                self.process = QProcess()
                self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
                self.process.readyRead.connect(self.ifReadReady)
                self.process.start(os.path.join(tempFile, "temp.exe"))
        else:
            mainWin.resultWin.appendPlainText("قم ببناء الشفرة أولاً")
            mainWin.thread.quit()

    def ifReadReady(self):
        data = self.process.readAll()
        data = bytes(data).decode('utf8')
        self.readDataSignal.emit(data)
        self.process.finished.connect(mainWin.thread.quit)

    def wait_input(self):
        if self.process != None:
            dataWrite = mainWin.inputLine.text() + '\n'
            dataWriteByte = dataWrite.encode()
            self.process.write(dataWriteByte)


######################################################################
# عداد الحروف
######################################################################

class CharCont:
    def __init__(self, MainWin):
        super(CharCont, self).__init__()
        self.mainWin = MainWin
        self.charCountLable = QLabel(f'{self.char_count()} حرف   ')
        self.charCountLable.setFont(QFont("Alusus Mono Medium"))
        self.mainWin.tabWin.widget(0).textChanged.connect(self.charCount)
        self.mainWin.tabWin.currentChanged.connect(lambda idx: self.changeCharCount(idx))

    def changeCharCount(self, idx):
        self.charCountTab = len(self.mainWin.tabWin.widget(idx).toPlainText())
        self.charCountLable.setText(f'{self.charCountTab} حرف   ')
        self.mainWin.tabWin.widget(idx).textChanged.connect(self.charCount)

    def charCount(self):
        self.charCountLable.setText(f'{self.char_count()} حرف   ')

    def char_count(self):
        return len(self.mainWin.tabWin.currentWidget().toPlainText())


######################################################################
# تشغيل التطبيق
######################################################################

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setFont(QFont('Tajawal', 10))
    mainWin = MainWin()
    mainWin.show()
    sys.exit(app.exec())
