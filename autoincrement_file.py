import re
from PyQt4.QtGui import QFileDialog
from PyQt4.QtCore import QSettings

def get_save_filename(*args, **kwargs):
    qset = QSettings()
    filename = QFileDialog.getSaveFileName(*args,
            directory=qset.value('path', ''), **kwargs)
    if filename != '':
        # If filename ends with a counter, increment it and save as default
        match = re.match(r'(.*)_(\d\d\d)\.(.*)$', filename)
        if match:
            qset.setValue('path', '{}_{:03d}.{}'.format(match.group(1),
                int(match.group(2)) + 1, match.group(3)))
        else:
            qset.setValue('path', re.sub(r'(\.\w+|)$', r'_001\1', filename))
    return filename
