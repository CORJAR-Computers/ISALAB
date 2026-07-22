# utils/validators.py
"""Validaciones de datos IsaLab"""

import re
from typing import Dict, Any
from config import VALIDACIONES
from utils.exceptions import ValidationError


class Validator:
    """Clase base para validaciones"""

    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        if not value or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"El campo '{field_name}' es obligatorio")

    @staticmethod
    def validate_length(
            value: str,
            field_name: str,
            min_len: int = None,
            max_len: int = None) -> None:
        if min_len and len(value) < min_len:
            raise ValidationError(
                f"'{field_name}' debe tener al menos {min_len} caracteres")
        if max_len and len(value) > max_len:
            raise ValidationError(
                f"'{field_name}' no puede exceder {max_len} caracteres")

    @staticmethod
    def validate_pattern(value: str, field_name: str, pattern: str) -> None:
        if not re.match(pattern, value):
            raise ValidationError(f"El formato de '{field_name}' no es válido")

    @staticmethod
    def validate_numeric(
            value: Any,
            field_name: str,
            min_val: float = None,
            max_val: float = None) -> None:
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                raise ValidationError(
                    f"'{field_name}' debe ser mayor o igual a {min_val}")
            if max_val is not None and num > max_val:
                raise ValidationError(
                    f"'{field_name}' debe ser menor o igual a {max_val}")
        except (ValueError, TypeError):
            raise ValidationError(f"'{field_name}' debe ser un valor numérico")


class AnimalValidator(Validator):
    """Validaciones específicas para animales"""

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> None:
        errores = []

        try:
            cls.validate_required(data.get('codigo'), 'Código')
            cls.validate_length(data.get('codigo'), 'Código',
                                VALIDACIONES['codigo_animal']['min'],
                                VALIDACIONES['codigo_animal']['max'])
            cls.validate_pattern(data.get('codigo'), 'Código',
                                 VALIDACIONES['codigo_animal']['pattern'])
        except ValidationError as e:
            errores.append(str(e))

        try:
            cls.validate_required(data.get('nombre'), 'Nombre')
            cls.validate_length(data.get('nombre'), 'Nombre',
                                VALIDACIONES['nombre']['min'],
                                VALIDACIONES['nombre']['max'])
        except ValidationError as e:
            errores.append(str(e))

        try:
            cls.validate_required(data.get('especie'), 'Especie')
        except ValidationError as e:
            errores.append(str(e))

        if data.get('edad'):
            try:
                cls.validate_numeric(data.get('edad'), 'Edad', 0, 100)
            except ValidationError as e:
                errores.append(str(e))

        if data.get('peso'):
            try:
                cls.validate_numeric(data.get('peso'), 'Peso', 0.1, 5000)
            except ValidationError as e:
                errores.append(str(e))

        if data.get('email'):
            try:
                cls.validate_pattern(data.get('email'), 'Email',
                                     VALIDACIONES['email']['pattern'])
            except ValidationError as e:
                errores.append(str(e))

        if errores:
            raise ValidationError(
                "Errores de validación", details={
                    'errores': errores})


class MuestraValidator(Validator):
    """Validaciones específicas para muestras"""

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> None:
        errores = []

        try:
            # codigo es opcional: se auto-genera si no se proporciona
            if data.get('codigo'):
                cls.validate_length(data.get('codigo'), 'Código',
                                    VALIDACIONES['codigo_muestra']['min'],
                                    VALIDACIONES['codigo_muestra']['max'])
        except ValidationError as e:
            errores.append(str(e))

        try:
            cls.validate_required(data.get('animal_id'), 'Animal')
            cls.validate_numeric(data.get('animal_id'), 'Animal ID', 1)
        except ValidationError as e:
            errores.append(str(e))

        try:
            cls.validate_required(data.get('tipo_muestra'), 'Tipo de Muestra')
        except ValidationError as e:
            errores.append(str(e))

        try:
            cls.validate_required(
                data.get('fecha_recoleccion'),
                'Fecha de Recolección')
        except ValidationError as e:
            errores.append(str(e))

        if errores:
            raise ValidationError(
                "Errores de validación", details={
                    'errores': errores})
