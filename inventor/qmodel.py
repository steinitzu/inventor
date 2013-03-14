from PySide.QtCore import QAbstractTableModel
from PySide.QtCore import Qt
from PySide.QtCore import QModelIndex

from .db import ITEM_FIELDS


class ItemModel(QAbstractTableModel):
    
    def __init__(self, database):
        self.db = database
        self.items = []

    def fetch_items(self, labels=None):
        """Fill model with items based on given labels."""
        items = self.db.items(labels=labels)
        self.beginResetModel()
        self.items = items
        self.endResetModel()

    def get_item(self, index):
        item = index.internalPointer() if index.isValid() else None
        return item
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            item = self.get_item(index)
            return getattr(item, ITEM_FIELDS[index.column])
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role==Qt.DisplayRole:
            return self.ITEM_FIELDS[section]

    def index(self, row, column, parent):
        return self.createIndex(row, column, self.items[row])

    def rowCount(self, parent):
        return len(self.items)
    
    def columnCount(self, parent):
        return len(ITEM_FIELDS)
    
    def parent(self, index):
        return QModelIndex()
