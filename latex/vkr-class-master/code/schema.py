
"""
Модуль создания структуры базы данных и заполнения справочников.
Содержит функции create_all_tables, init_dictionaries, init_admin_user и init_test_table.
"""

def create_all_tables(conn):
    """Создаёт все таблицы приложения"""
    with conn.cursor() as cur:
        # Справочники
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_status (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS program_type (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS department (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS learning_form (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS funding_source (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customer_type (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_type (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_status (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS economic_activity (
                id SERIAL PRIMARY KEY,
                name VARCHAR(300) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS professional_field (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ugs (
                id SERIAL PRIMARY KEY,
                name VARCHAR(300) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS qualification (
                id SERIAL PRIMARY KEY,
                name VARCHAR(300) UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS education_level (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL
            )
        """)

        # Основные таблицы
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                last_name VARCHAR(100) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                patronymic VARCHAR(100),
                birth_date DATE NOT NULL,
                gender VARCHAR(10),
                snils VARCHAR(20) UNIQUE,
                phone VARCHAR(20),
                citizenship_code VARCHAR(10),
                status_id INTEGER REFERENCES student_status(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS programs (
                id SERIAL PRIMARY KEY,
                name VARCHAR(300) NOT NULL,
                program_type_id INTEGER REFERENCES program_type(id),
                department_id INTEGER REFERENCES department(id),
                learning_form_id INTEGER REFERENCES learning_form(id),
                uses_dot BOOLEAN DEFAULT FALSE,
                duration_hours INTEGER,
                professional_field_id INTEGER REFERENCES professional_field(id),
                economic_activity_id INTEGER REFERENCES economic_activity(id),
                ugs_id INTEGER REFERENCES ugs(id),
                qualification_id INTEGER REFERENCES qualification(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) NOT NULL,
                program_id INTEGER REFERENCES programs(id),
                start_date DATE,
                end_date DATE,
                order_enrollment VARCHAR(100)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_group (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
                group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
                status VARCHAR(50),
                expulsion_date DATE,
                expulsion_reason TEXT,
                order_expulsion VARCHAR(100)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
                document_type_id INTEGER REFERENCES document_type(id),
                status_id INTEGER REFERENCES document_status(id),
                series VARCHAR(50),
                number VARCHAR(50),
                issue_date DATE,
                registration_number VARCHAR(100),
                order_issue VARCHAR(100)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS financing (
                id SERIAL PRIMARY KEY,
                student_group_id INTEGER REFERENCES student_group(id) ON DELETE CASCADE,
                funding_source_id INTEGER REFERENCES funding_source(id),
                customer_type_id INTEGER REFERENCES customer_type(id),
                customer_name VARCHAR(300),
                cost NUMERIC(12,2)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_characteristics (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
                is_pedagogical VARCHAR(200),
                is_manager VARCHAR(200)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS prior_education (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
                lastname_in_diploma VARCHAR(100),
                diploma_series VARCHAR(50),
                diploma_number VARCHAR(50),
                education_level_id INTEGER REFERENCES education_level(id)
            )
        """)

        # Добавляем таблицу пользователей
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(200) NOT NULL,
                        is_admin BOOLEAN DEFAULT FALSE
                    )
                """)
        conn.commit()

def init_dictionaries(conn):
    """Заполняет справочники начальными данными (если их ещё нет)"""
    with conn.cursor() as cur:
        # Статусы слушателей (из листа "Лист1" Excel)
        statuses = [
            "Работник сторонней организации",
            "Сотрудник ЮЗГУ",
            "Безработный по направлению службы занятости",
            "Незанятый по направлению службы занятости",
            "Государственный служащий (замещает государственную должность)",
            "Муниципальный служащий (замещает должность)",
            "Уволенный с военной службы",
            "Студент ВО",
            "Студент СПО",
            "Другие"
        ]
        for name in statuses:
            cur.execute("INSERT INTO student_status (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))

        # Типы программ
        program_types = ["Повышение квалификации", "Профессиональная переподготовка"]
        for name in program_types:
            cur.execute("INSERT INTO program_type (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))

        # Формы обучения
        forms = ["Очная", "Заочная"]
        for name in forms:
            cur.execute("INSERT INTO learning_form (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))

        # Источники финансирования
        funding = ["Федеральный бюджет", "Региональный бюджет", "Местный бюджет", "Платное обучение"]
        for name in funding:
            cur.execute("INSERT INTO funding_source (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))

        # Типы заказчиков
        customers = ["физическое лицо", "юридическое лицо", "собственные средства ЮЗГУ"]
        for name in customers:
            cur.execute("INSERT INTO customer_type (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))

        # Виды документов
        doc_types = [
            "Удостоверение о повышении квалификации",
            "Диплом о профессиональной переподготовке",
            "Свидетельство о повышении квалификации",
            "Диплом о присвоении квалификации",
            "Справка об обучении"
        ]
        for name in doc_types:
            cur.execute("INSERT INTO document_type (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))

        # Статусы документов
        doc_statuses = ["Оригинал", "Дубликат"]
        for name in doc_statuses:
            cur.execute("INSERT INTO document_status (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))

        # Уровни образования
        edu_levels = ["Высшее образование", "Среднее профессиональное образование", "Справка", "Стаж", "Пункт 1 правил формирования ФИС ФРДО"]
        for name in edu_levels:
            cur.execute("INSERT INTO education_level (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (name,))

    conn.commit()


def init_admin_user(conn):
    """Создаёт администратора, если его ещё нет"""
    from werkzeug.security import generate_password_hash
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = %s", ('admin',))
        if not cur.fetchone():
            # Пароль по умолчанию 
            password_hash = generate_password_hash('admin123')
            cur.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)",
                ('admin', password_hash, True)
            )
            conn.commit()


def init_test_table(conn):
    """Создаёт тестовую таблицу (можно оставить для проверки)"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL
            )
        """)
        conn.commit()