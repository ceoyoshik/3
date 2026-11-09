"""Исключения, общие для всех модулей системы «МатрСум-11»."""


class IntegrationError(Exception):
    """Базовое исключение ошибок интеграции модулей."""


class InputDataError(IntegrationError):
    """Некорректные данные: ввод пользователя или содержимое сообщения."""


class ProtocolError(IntegrationError):
    """Сообщение нарушает формат протокола обмена."""


class VersionConflictError(ProtocolError):
    """Модули используют несовместимые версии протокола."""


class ModuleUnavailableError(IntegrationError):
    """Модуль недоступен: не найден, не запустился или завершился сбоем."""


class ModuleTimeoutError(IntegrationError):
    """Модуль не ответил за отведённое время."""
