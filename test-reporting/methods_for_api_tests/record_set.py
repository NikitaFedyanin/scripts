class RecordSet:
    """RecordSet"""

    def __init__(self, record_set):
        """Конструктор"""

        self.__data = record_set['d']
        self.__fields = [record['n'] for record in record_set['s']]
        self.__records_count = len(self.__data)
        self.__fields_count = len(self.__fields)
        # is empty
        if self.__records_count == 0:
            self.__is_empty = True
        else:
            self.__is_empty = False
        # is one record
        if self.__records_count == 1:
            self.__is_one_record = True
        else:
            self.__is_one_record = False

    def __has_field(self, field_name):
        """Имеет ли RecordSet заданное поле"""

        try:
            self.__fields.index(field_name)
            return True
        except ValueError:
            return False

    @property
    def records_count(self):
        """Колличество записей в RecordSet"""

        return self.__records_count

    @property
    def fields_count(self):
        """Колличество полей в RecordSet"""

        return self.__fields_count

    @property
    def is_empty(self):
        """Пустой ли RecordSet"""

        return self.__is_empty

    @property
    def is_one_record(self):
        """Одна ли запись в RecordSet"""

        return self.__is_one_record

    def as_list(self):
        """Представляет RecordSet как список списков значений"""

        return self.__data

    def as_dict(self):
        """Представляет RecordSet как список словарей значений"""

        result = list()
        for record_index, record in enumerate(self.__data):
            temp = dict()
            for field_index, field in enumerate(self.__fields):
                temp[field] = record[field_index]
            result.append(temp)
        return result

    def __getitem__(self, field_name):

        if self.__has_field(field_name):
            return [data[self._RecordSet__fields.index(field_name)] for data in self._RecordSet__data]  # _RecordSet__fields
        else:
            raise ValueError

    def __len__(self):

        return self.__records_count
