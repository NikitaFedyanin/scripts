# coding=utf-8
import uuid


class SuperData:
    """Класс родитель для класса Data"""

    @classmethod
    def __get_var__(cls):
        """Служебный метод для получения словаря с переменными"""

        data_dict = {}
        for key in cls.__dict__.keys():
            if not key.startswith('__'):
                data_dict[key] = cls.__dict__[key]
        return data_dict

    def __get_var_new__(self):
        """Служебный метод для получения словаря с переменными"""

        data_dict = {}
        dir_self = dir(self)
        for key in dir_self:
            if not key.startswith('__'):
                data_dict[key] = getattr(self, key)
        return data_dict

    @classmethod
    def set(cls, name, value):
        setattr(cls, name, value)

    @classmethod
    def get(cls, name):
        return cls.__dict__[name]

    @classmethod
    def set_many(cls, **kwargs):
        for name, value in kwargs.items():
            setattr(cls, name, value)

    @classmethod
    def get_many(cls, *args):
        return [cls.__dict__[arg] for arg in args]

    @classmethod
    def set_uuid(cls, attr_name):
        """
        Добавляет атрубут классу Data
        :param attr_name: имя атрубута
        значение атрубута - guid
        """
        setattr(cls, attr_name, str(uuid.uuid1()))

    @classmethod
    def set_uuid_many(cls, *attr_name):
        """
        Добавляет атрубуты классу Data
        :param attr_name: имя атрубута
        значение атрубута - guid
        """
        for name in attr_name:
            setattr(cls, name, str(uuid.uuid1()))