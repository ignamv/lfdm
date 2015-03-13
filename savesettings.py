from PyQt4.QtCore import QSettings, QObject

class SaveSettings(QObject):
    def __init__(self, properties, parent):
        super().__init__(parent)
        self.properties = properties
        qset = QSettings()
        for child, property in self.properties:
            string = child + '/' + property
            if qset.contains(string):
                parent.findChild(QObject, child).setProperty(property,
                        qset.value(string))
    def save(self):
        qset = QSettings()
        for child, property in self.properties:
            obj = self.parent().findChild(QObject, child)
            if obj is None:
                raise RuntimeError("Could not find " + child)
            qset.setValue(child + '/' + property, obj.property(property))
