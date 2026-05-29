import re

class ValidationError(Exception):
    pass

def validate_snils(snils):
    """СНИЛС: 11 цифр, контрольная сумма"""
    if not snils:
        return True
    cleaned = re.sub(r'\D', '', snils)
    if len(cleaned) != 11:
        raise ValidationError("СНИЛС должен содержать 11 цифр")
    total = 0
    for i, digit in enumerate(cleaned[:9]):
        total += int(digit) * (9 - i)
    check = total % 101
    if check == 100:
        check = 0
    if check != int(cleaned[9:]):
        raise ValidationError("Неверный контрольный номер СНИЛС")
    return True

def validate_phone(phone):
    """Проверка российского телефона: +7XXXXXXXXXX, 8XXXXXXXXXX или 11 цифр"""
    if not phone:
        return True
    cleaned = re.sub(r'[^\d+]', '', phone)
    if cleaned.startswith('+7') and len(cleaned) == 12:
        return True
    if cleaned.startswith('8') and len(cleaned) == 11:
        return True
    if len(cleaned) == 11 and cleaned.isdigit():
        return True
    raise ValidationError("Телефон должен быть в формате +7XXXXXXXXXX, 8XXXXXXXXXX или 11 цифр")

def validate_citizenship_code(code):
    """Проверка кода гражданства (3 цифры)"""
    if not code:
        return True
    code_str = str(code).strip()
    if not code_str.isdigit() or len(code_str) != 3:
        raise ValidationError("Код гражданства должен состоять из 3 цифр")
    return True

def validate_date(date_str, field_name="Дата"):
    """Общая проверка даты (формат ГГГГ-ММ-ДД)"""
    if not date_str:
        return True
    # Приводим к строке и удаляем пробелы
    date_str = str(date_str).strip()
    # Если после приведения пусто или это 'nan'/'none'/'null' – считаем пустым
    if date_str.lower() in ('', 'nan', 'none', 'null'):
        return True
    # Если пришло число (серийный номер Excel), преобразуем в строку даты
    try:
        num = float(date_str)
        # Серийный номер Excel: 1 = 1900-01-01, поправка на ошибку в Excel
        if num > 0:
            from datetime import datetime, timedelta
            excel_date = datetime(1900, 1, 1) + timedelta(days=num - 2)
            date_str = excel_date.strftime('%Y-%m-%d')
    except ValueError:
        pass
    # Проверяем формат
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        raise ValidationError(f"{field_name} должна быть в формате ГГГГ-ММ-ДД")

def validate_birth_date(date_str):
    """Дата рождения: не в будущем, не старше 120 лет"""
    if not date_str:
        return True
    validate_date(date_str, "Дата рождения")
    from datetime import datetime
    birth_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    today = datetime.now().date()
    if birth_date > today:
        raise ValidationError("Дата рождения не может быть в будущем")
    age = today.year - birth_date.year
    if age > 120:
        raise ValidationError("Возраст не может превышать 120 лет")
    return True

def validate_cost(cost_str):
    """Стоимость: положительное число, не более 10 млн"""
    if not cost_str:
        return True
    try:
        cost = float(cost_str)
        if cost < 0:
            raise ValidationError("Стоимость не может быть отрицательной")
        if cost > 10_000_000:
            raise ValidationError("Стоимость не может превышать 10 000 000 руб")
        return True
    except ValueError:
        raise ValidationError("Стоимость должна быть числом")

def validate_duration_hours(hours_str):
    """Срок обучения: от 1 до 10000 часов"""
    if not hours_str:
        return True
    try:
        hours = int(hours_str)
        if hours <= 0:
            raise ValidationError("Срок обучения должен быть положительным числом")
        if hours > 10000:
            raise ValidationError("Срок обучения не может превышать 10000 часов")
        return True
    except ValueError:
        raise ValidationError("Срок обучения должен быть целым числом")

def validate_text_field(value, field_name, min_len=2, max_len=300):
    """Проверка текстовых полей (ФИО, названия и т.д.)"""
    if not value:
        return True
    if len(value) < min_len:
        raise ValidationError(f"{field_name} должен содержать минимум {min_len} символа")
    if len(value) > max_len:
        raise ValidationError(f"{field_name} не может превышать {max_len} символов")
    return True

def validate_document_number(number):
    """Номер документа: не более 50 символов, только буквы/цифры/дефис"""
    if not number:
        return True
    if len(number) > 50:
        raise ValidationError("Номер документа не может превышать 50 символов")
    if not re.match(r'^[A-Za-zА-Яа-я0-9\-]+$', number):
        raise ValidationError("Номер документа может содержать только буквы, цифры и дефис")
    return True

def validate_required_fields(data, required_fields):
    """Проверка обязательных полей"""
    missing = []
    for field in required_fields:
        if not data.get(field):
            missing.append(field)
    if missing:
        raise ValidationError(f"Обязательные поля не заполнены: {', '.join(missing)}")

def validate_student_data(form_data):
    """Полная проверка всех полей студента"""
    errors = []
    try:
        required = ['last_name', 'first_name', 'birth_date']
        validate_required_fields(form_data, required)

        validate_text_field(form_data.get('last_name', ''), "Фамилия", 2, 100)
        validate_text_field(form_data.get('first_name', ''), "Имя", 2, 100)
        validate_text_field(form_data.get('patronymic', ''), "Отчество", 0, 100)

        validate_birth_date(form_data.get('birth_date'))

        validate_snils(form_data.get('snils', ''))
        validate_phone(form_data.get('phone', ''))
        validate_citizenship_code(form_data.get('citizenship_code', ''))

        validate_cost(form_data.get('cost', ''))
        validate_duration_hours(form_data.get('duration_hours', ''))
        validate_text_field(form_data.get('customer_name', ''), "Наименование заказчика", 0, 300)

        validate_document_number(form_data.get('document_series', ''))
        validate_document_number(form_data.get('document_number', ''))
        validate_text_field(form_data.get('registration_number', ''), "Регистрационный номер", 0, 100)

        if form_data.get('document_issue_date'):
            validate_date(form_data.get('document_issue_date'), "Дата выдачи документа")

        start_date = form_data.get('start_date')
        end_date = form_data.get('end_date')
        if start_date and end_date:
            validate_date(start_date, "Дата начала обучения")
            validate_date(end_date, "Дата окончания обучения")
            if start_date > end_date:
                errors.append("Дата начала не может быть позже даты окончания")

        validate_text_field(form_data.get('group_code', ''), "Номер группы", 0, 50)
        validate_text_field(form_data.get('program_name', ''), "Наименование программы", 0, 300)
        validate_text_field(form_data.get('department_name', ''), "Кафедра", 0, 200)

        validate_text_field(form_data.get('professional_field', ''), "Область деятельности", 0, 200)
        validate_text_field(form_data.get('ugs', ''), "Укрупнённая группа", 0, 300)
        validate_text_field(form_data.get('economic_activity', ''), "Вид деятельности", 0, 300)
        validate_text_field(form_data.get('qualification', ''), "Квалификация", 0, 300)

        validate_text_field(form_data.get('diploma_lastname', ''), "Фамилия в дипломе", 0, 100)
        validate_document_number(form_data.get('diploma_series', ''))
        validate_document_number(form_data.get('diploma_number', ''))

        doc_issue = form_data.get('document_issue_date')
        if doc_issue and start_date:
            validate_date(doc_issue, "Дата выдачи документа")
            validate_date(start_date, "Дата начала обучения")
            if doc_issue < start_date:
                errors.append("Дата выдачи документа не может быть раньше даты зачисления")

        # Проверка: дата окончания не может быть раньше даты начала
        if start_date and end_date:
            if end_date < start_date:
                errors.append("Дата окончания обучения не может быть раньше даты начала")

    except ValidationError as e:
        errors.append(str(e))

    if errors:
        return False, errors
    return True, []

def format_validation_errors(errors):
    return "<br>".join(errors)