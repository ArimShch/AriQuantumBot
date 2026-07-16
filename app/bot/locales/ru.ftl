bcmnd_menu = Главная страница
cmnd_admin = Админ-панель 
cmnd_help = Помощь и справка
cmnd_create_circuit = Создание новой схемы

choose_language = 👋 Привет! Выберите язык: 
set_language = 🌐 Язык установлен!

menu =
    { $complexity_level ->
        [Novice] <b><u>AriQuantum | Эмулятор квантовых вычислений</u></b>
        
        Воспользуйтесь командой <b>/help</b> для получения рекомендаций.
        
        Используйте команду <b>/create_circuit</b>, чтобы создать новую квантовую схему.
        
        ℹ️ Ниже приведены доступные разделы.
       *[default] <b><u>AriQuantum | Эмулятор квантовых вычислений</u></b>
       
       Используйте команду <b>/create_circuit</b>, чтобы создать новую квантовую схему.
       
       ℹ️ Ниже приведены доступные разделы.
    }

menu_button = ⏪ Меню
back_button = ⬅️ Назад
menu_circuit_button = ⛓️ Мои схемы
menu_profile_button = 👤 Профиль
menu_settings_button = ⚙️ Настройки

input_circuit_name = 
    { $complexity_level ->
        [Novice] Придумайте имя для вашей квантовой схемы и отправьте его (например, «Моя первая схема»).
        [Student] Укажите имя схемы (это поможет вам найти её позже).
        [Searcher] Укажите уникальное имя схемы для последующего доступа.
       *[default] Введите имя схемы:
    }

input_num_qubits_text = 
    { $complexity_level ->
        [Novice] 🔢 Сколько кубитов будет в вашей схеме?
            Отправьте число от 1 до { $num_qubits }. Например: «3».
        [Student] Отправьте количество кубитов (1–{ $num_qubits }):
        [Searcher] Задайте число кубитов (макс. { $num_qubits }):
       *[default] Отправьте количество кубитов (1–{ $num_qubits }):
    }

input_num_qubits_keyboard = 
    { $complexity_level ->
        [Novice] 🔢 Сколько кубитов будет в вашей схеме?
            Нажмите на кнопку с нужным числом (от 1 до { $num_qubits }). 
        [Student] Выберите количество кубитов:
        [Searcher] Укажите число кубитов:
       *[default] Выберите количество кубитов:
    }

circuit_limit_reached = 
    ⚠️ Вы достигли лимита сохранённых схем.  
    Удалите ненужные в разделе <b>⛓️ Мои схемы</b>, чтобы создать новую. Или вернитесь в меню.

my_circuits = 
    { $have_circuits -> 
        [True] 🗂 <b>Ваши сохранённые квантовые схемы.</b> 

               Чтобы создать новую, воспользуйтесь командой <b>/create_circuit</b>.
    
               ℹ️ Выберите схему, чтобы запустить, изменить или удалить её.
        [False] 🗂 <b>Ваши сохранённые квантовые схемы.</b>  

                ℹ️ У вас пока нет сохранённых схем.  
                Чтобы создать новую, воспользуйтесь командой <b>/create_circuit</b>.
       *[default] 🗂 <b>Ваши сохранённые квантовые схемы.</b>  

                  Чтобы создать новую, воспользуйтесь командой <b>/create_circuit</b>.
    
                  ℹ️ Выберите схему, чтобы запустить, изменить или удалить её.
    }

circuit_details = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    Бэкенд: <b>{ $backend }</b>
    <br><br>
    { $has_simulation ->
        [True] Результат последней симуляции:
        [False] Текущее состояние (до симуляции):
       *[default] Текущее состояние:
    }
    <pre>{ $state_vector }</pre>

apply_gate_prompt = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Выберите гейт, который хотите применить к квантовой схеме.

apply_gate_select_angle = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Укажите угол поворота для гейта <b>«{ $gate_name }»</b>.<br>
    Вы можете выбрать значение из предложенных (например, π/2, π/4).

apply_gate_select_target_qubit = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Выберите целевой кубит для применения гейта <b>«{ $gate_name }»</b>.

apply_gate_select_target_qubit_measurement = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Выберите кубиты для измерения.<br> 
    Вы можете измерить все кубиты сразу или выбрать конкретный.

apply_gate_select_first_control = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Укажите контролирующий кубит для гейта <b>«{ $gate_name }»</b>.

apply_gate_select_second_control = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Укажите второй контролирующий кубит для гейта <b>«{ $gate_name }»</b>.

circuit_edit_menu = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Выберите действие:

circuit_rename_prompt = Укажите новое имя для квантовой схемы (макс. 50 символов):
circuit_name_invalid = ❌ Некорректное имя! Имя не должно быть пустым и превышать 50 символов.



# Статусы
control_qubit_already_selected = Этот кубит уже выбран! ⚪️
gate_applied_successfully = Гейт успешно применён! ✅
selection_reset = Выбор сброшен 🔄
circuit_cleared = Схема очищена! Все гейты удалены. ✅
circuit_deleted = Схема удалена! 🗑️
measurement_applied_single = Измерение применено! 📏
measurement_applied_multiple = Измерение применено к { $count } кубитам! 📏
gate_cannot_be_applied_to_measured_qubits = ❌ Нельзя применять квантовый гейт «{ $gate_name }» к измеренным кубитам.


# Кнопки
circuit_edit_clear_button = 🧹 Очистить схему
circuit_edit_delete_button = 🗑️ Удалить схему  
circuit_edit_rename_button = ✏️ Переименовать
reset_qubit_selection = 🔄 Отменить выбор
circuit_apply_gate_button = ➕ Применить гейт
circuit_edit_button = 📋 Редактировать схему
circuit_simulate_button = 🚀 Запустить симуляцию
measure_all_qubits_button = 📏 Измерить все кубиты



error_input_circuit_name = 
    Возникла ошибка! Пожалуйста, отправьте <b>текстовое сообщение</b> с уникальным названием схемы. 
    Например: «Моя схема» или «Bell-состояние». Имя схемы не должно превышать 50 символов.
    

error_num_qubits_invalid = 
    Недопустимое количество кубитов.  
    Максимум: { $max_qubits }.  
    Вы можете вернуться в главное меню командой /start.
    

error_input_num_qubits = 
    Некорректное значение.  
    Укажите число от 1 до { $max_qubits } — именно столько кубитов поддерживает выбранный бэкенд.
    

test = OK

// Настройки пользователя
settings_menu = 
    ⚙️ <b>Настройки</b>

    🌐 Язык: <b>{ $language }</b>
    🎓 Уровень сложности: <b>{ $complexity }</b>
    💻 Бэкенд: <b>{ $backend }</b>
    🤖 Автоматическое имя схемы: <b>{ $automatic_name }</b>
    🔢 Ввод кубитов текстом: <b>{ $qubit_input_text }</b>
    📊 Запусков симуляции: <b>{ $simulation_shots }</b>

settings_language_button = 🌐 Язык
settings_complexity_button = 🎓 Уровень сложности  
settings_backend_button = 💻 Бэкенд
settings_automatic_name_button = 🤖 Автоматическое имя схемы
settings_qubit_input_text_button = 🔢 Ввод кубитов текстом
settings_simulation_shots_button = 📊 Запуски симуляции

settings_language_menu = 
    🌐 <b>Выбор языка</b>
    
    ℹ️ Текущий язык: { $current }

settings_complexity_menu = 
    🎓 <b>Уровень сложности</b>
    <br>
    <ul>
        <li>🐣 <b>Новичок</b> — подробные объяснения, пошаговые инструкции, упрощённые термины</li>
        <li>👨🏼‍🎓 <b>Студент</b> — баланс между деталями и краткостью, основные концепции без излишней простоты</li>
        <li>👨🏼‍💻 <b>Исследователь</b> — минимум пояснений, только технические детали и продвинутые функции</li>
    </ul>
    <br>
    ℹ️ Текущий уровень: <b>{ $current }</b>

settings_backend_menu = 
    💻 <b>Бэкенд квантовых вычислений</b>
    <br>
    { $complexity_level ->
        [Novice]
            <ul>
                <li><b>AriQuantum</b> — наш собственный эмулятор, быстрее для простых схем (до 6 кубитов).</li>
                <li><b>Qiskit</b> — промышленный стандарт от IBM, надёжнее для сложных схем с измерениями.</li>
            </ul>
       *[default]
            <ul>
                <li><b>AriQuantum</b> — наш оптимизированный эмулятор, быстрее на небольших схемах (до 6 кубитов), но может некорректно работать с гейтами после измерений, так как выводит только результаты последнего измерения.</li>
                <li><b>Qiskit</b> — промышленный стандарт от IBM, корректно обрабатывает измерения и последующие гейты, сохраняя результаты в классический регистр.</li>
            </ul>
    }
    <br>
    ℹ️ Текущий бэкенд: { $current }

qubits = кубитов

settings_simulation_shots_menu = 
    📊 <b>Количество запусков симуляции</b>
    
    Больше запусков = точнее статистика, но дольше расчёт.

    ℹ️ Текущее значение: { $current }

bool_yes = Да ✅
bool_no = Нет ❌

settings_language_updated = 🌐 Язык обновлён!
settings_complexity_updated = 🎓 Уровень сложности обновлён!
settings_backend_updated = 💻 Бэкенд обновлён!
settings_simulation_shots_updated = 📊 Количество запусков обновлено!
settings_automatic_name_updated = 🤖 Автоматическое имя схемы обновлено!
settings_qubit_input_text_updated = 🔢 Режим ввода кубитов обновлён!

simulation_result_with_measurements = 
    🚀 <b>Симуляция схемы «{ $circuit_name }»</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    💻 Использованный бэкенд: <b>{ $backend }</b><br>
    ⏱️ Время выполнения: <b>{ $execution_time } сек</b>
    <br><br>
    📌 <b>Состояние до первого измерения:</b>
    <pre>{ $braket_state }</pre>
    <br>
    📊 <b>Результаты { $shots } запусков:</b>
    <pre>{ $counts }</pre>

simulation_result_without_measurements = 
    🚀 <b>Симуляция схемы «{ $circuit_name }»</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    💻 Использованный бэкенд: <b>{ $backend }</b><br>
    ⏱️ Время выполнения: <b>{ $execution_time } сек</b>
    <br><br>
    📌 <b>Вектор состояния:</b>
    <pre>{ $braket_state }</pre>

simulation_back_to_circuit_button = ◀️ Вернуться к схеме
simulation_error = ❌ Ошибка при симуляции схемы!
simulation_timeout_error = ❌ Симуляция превысила лимит времени (10 сек)!

profile = 
    👤 <b>Профиль</b>

    Имя: { $first_name }
    Юзернейм: { $username }

    📊 <b>Статистика:</b>
    • Создано схем: { $circuits_count }/{ $max_circuits }
    • Проведено симуляций: { $simulations_count }


command_admin = 
    🥷🏼 <b>Админ-панель</b>

    1. Статистика по пользователям
    2. Статистика по схемам и симуляциям
    3. Статистика по бэкендам
    4. Заблокировать пользователя

    ℹ️ Выберите действие ниже:

admin_users_btn = Статистика «👤 Пользователи»
admin_circuits_btn = Статистика «⛓️ Схемы» 
admin_backends_btn = Статистика «💻 Бэкенды»
admin_blocked_btn = ❌ Заблокировать юзера
admin_message_btn = 📩 Разослать сообщение
admin_stat_btn = Статистика «📊 Настройки»
admin_menu_btn = ⏪ Админ меню

admin_users = 
    <b>Статистика «👤 Пользователи»</b>

    <b>ВСЕГО пользователей:</b> 👥 { $all_users }

    <b>ТОП 5 по использованию (дни):</b>
    { $top5_days_text }

    <b>ТОП 5 по использованию (схемы):</b>
    { $top5_circuits_text }

    <b>ТОП 5 по использованию (симуляции):</b>
    { $top5_simulations_text }

    <b>Статистика использования за последние 20 дней:</b>
    { $stat_users20 }

admin_circuits = 
    <b>Статистика «⛓️ Схемы»</b>

    <b>СЕЙЧАС схем:</b> { $circuits_now }
    <b>ВСЕГО создано схем:</b> { $circuits_all }

    <b>СЕЙЧАС симуляций:</b> { $simulations_now }
    <b>ВСЕГО проведено симуляций:</b> { $simulations_all }

    <b>СРЕДНЕЕ кол-во кубитов:</b> { $avg_qubits }
    <b>СРЕДНЕЕ время исполнения:</b> { $avg_time } сек. 

    <b>Статистика создания схем и симуляций за последние 20 дней:</b>
    { $stat_circuits20 }

admin_backends = 
    <b>Статистика «💻 Бэкенды»</b>

    <b>⛓️ Схемы: </b>
    { $backends_circuits_text }

    <b>🚀 Симуляции: </b>
    { $backends_simulations_text }

    <b>📊 Кубиты: </b>
    { $backends_avg_qubits_text }

    <b>⏱️ Время выполнения:</b>
    { $backends_avg_time_text }

admin_block_prompt = 
    🔒 Введите ID пользователя или его юзернейм (с @ или без), которого нужно заблокировать:

admin_block_success = 
    ✅ Пользователь { $user } успешно заблокирован!

admin_block_not_found = 
    ❌ Пользователь "{ $user }" не найден в базе данных.

admin_statistics = 
    📊 <b>Статистика по настройкам пользователей</b>

    🔗 <b>Источники перехода</b>:
    { $ref_sources }

    🌍 <b>Язык Telegram</b>:
    { $tg_locales }

    🌐 <b>Языки</b>:
    { $languages }

    🎓 <b>Уровни сложности</b>:
    { $complexity_levels }

    💻 <b>Бэкенды</b>:
    { $backends }

    🤖 <b>Автоматическое имя схемы</b>:
    { $automatic_name }

    🔢 <b>Ввод кубитов текстом</b>:
    { $qubit_input }

    📈 <b>Запуски симуляции</b>:
    { $simulation_shots }
    Среднее значение: { $shots_avg }


help_message = 
    🌌 <b>AriQuantum | Эмулятор квантовых вычислений</b>
    <br><br>
    Это бот для изучения и экспериментов с квантовыми вычислениями прямо в Telegram.
    <br><br>
    🔹 <b>Основные возможности:</b>
    <ul>
        <li>Создавайте квантовые схемы с 1 до 10 кубитов</li>
        <li>Применяйте однокубитные, двухкубитные и трёхкубитные гейты</li>
        <li>Выполняйте измерения и анализируйте результаты</li>
        <li>Запускайте симуляции и получайте статистику</li>
    </ul>
    <br>
    💻 <b>Бэкенды:</b>
    <ul>
        <li><b>AriQuantum</b> — наш собственный эмулятор. Быстрый на небольших схемах (до 6 кубитов), но не сохраняет результаты измерений в классический регистр.</li>
        <li><b>Qiskit</b> — промышленный стандарт от IBM. Поддерживает полную совместимость с измерениями и последующими операциями.</li>
    </ul>
    <br>
    🎓 <b>Уровни сложности:</b>
    <ul>
        <li>🐣 <b>Новичок</b> — подробные объяснения, пошаговые инструкции, упрощённые термины</li>
        <li>👨🏼‍🎓 <b>Студент</b> — баланс между деталями и краткостью, основные концепции без излишней простоты</li>
        <li>👨🏼‍💻 <b>Исследователь</b> — минимум пояснений, только технические детали и продвинутые функции</li>
    </ul>
    <br>
    ⚠️ <b>Важно:</b>
    <ul>
        <li>После измерения кубита к нему нельзя применять квантовые гейты</li>
        <li>Схемы без измерений показывают вектор состояния в нотации Дирака</li>
        <li>Схемы с измерениями показывают состояние до первого измерения + статистику запусков</li>
        <li>Результаты измерений (базисные состояния вектора и результаты отдельных запусков) записываются в классические биты в том же порядке, что и кубиты. Например, состояние |110⟩ означает: q₀=1, q₁=1, q₂=0 → классический результат «110».</li>
    </ul>
    <br>
    ℹ️ Используйте меню или команды для навигации.


admin_broadcast_prompt = 
    📢 Введите текст для рассылки всем пользователям. 
    Сообщение будет автоматически разослано каждому пользователю.

admin_broadcast_started = 
    🚀 Рассылка запущена в фоновом режиме. Вы получите отчёт по завершении.

admin_broadcast_empty = 
    ❌ Текст рассылки не может быть пустым.