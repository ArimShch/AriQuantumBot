cmnd_menu = Main page
cmnd_admin = Admin-panel 
cmnd_help = Help & Guide
cmnd_create_circuit = Create a new circuit

choose_language = 👋 Hello! Choose your language: 
set_language = 🌐 The language is set!

menu =
    { $complexity_level ->
        [Novice] <b><u>AriQuantum | Quantum computing emulator</u></b>
        
        Try the <b>/help</b> command for guidance.
        
        Use the <b>/create_circuit</b> command to create a new quantum circuit.
        
        ℹ️ Below are the available sections.
       *[default] <b><u>AriQuantum | Quantum computing emulator</u></b>
       
       Use the <b>/create_circuit</b> command to create a new quantum circuit.
       
       ℹ️ Below are the available sections.
    }

menu_button = ⏪ Menu
back_button = ⬅️ Back
menu_circuit_button = ⛓️ My Circuits
menu_profile_button = 👤 Profile
menu_settings_button = ⚙️ Settings
menu_template_button = 🗃️ Templates

templates_list_title = 
    🗃️ <b>Templates</b>
    <br><br>
    Here are classic quantum algorithms and states. You can explore them and use them as a base for your own circuits.
    <br><br>
    ℹ️ Select a template below:

template_details = 
    🗃️ <b>Templates: { $name }</b>
    <br><br>
    { $description }
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Click the <b>"➕ Create circuit"</b> button below to create your own circuit based on this algorithm.

template_not_found = ❌ Template not found

template_create_btn = ➕ Create circuit 

input_circuit_name = 
    { $complexity_level ->
        [Novice] Give your quantum circuit a name and send it (e.g., "My first circuit").
        [Student] Provide a name circuit (this will help you find it later).
        [Researcher] Provide a unique name for the circuit.
       *[default] Enter circuit name:
    }

input_num_qubits_text = 
    { $complexity_level ->
        [Novice] 
            🔢 How many qubits will your circuit have?  
            Send a number from 1 to { $num_qubits }. Example: "3".
        [Student] Specify the number of qubits (1–{ $num_qubits }):
        [Researcher] Set the number of qubits (max { $num_qubits }):
       *[default] Specify the number of qubits (1–{ $num_qubits }):
    }

input_num_qubits_keyboard = 
    { $complexity_level ->
        [Novice] 
            🔢 How many qubits will your circuit have?  
            Tap the button with the desired number (1 to { $num_qubits }).  
        [Student] Choose the number of qubits:
        [Researcher] Specify the number of qubits:
       *[default] Choose the number of qubits:
    }

circuit_limit_reached = 
    ⚠️ You’ve reached the circuit storage limit.  
    Delete unused circuits in <b>⛓️ My Circuits</b> to create a new one. Or return to menu.

my_circuits = 
    { $have_circuits -> 
        [True] 🗂 <b>Your saved quantum circuits.</b> 
               
               To create circuit, use the <b>/create_circuit</b> command.

               ℹ️ Select a circuit to run, edit, or delete it.
        [False] 🗂 <b>Your saved quantum circuits.</b>  

                ℹ️ You don’t have any saved circuits yet.  
                To create one, use the <b>/create_circuit</b> command.
       *[default] 🗂 <b>Your saved quantum circuits.</b>  
    
                  To create circuit, use the <b>/create_circuit</b> command.

                  ℹ️ Select a circuit to run, edit, or delete it.
    }

circuit_details = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    { $has_simulation ->
        [True] Result of the last simulation:
        [False] Current state (before simulation):
       *[default] Current state:
    }
    <pre>{ $state_vector }</pre>

apply_gate_prompt = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Select a gate to apply to the quantum circuit.

apply_gate_select_angle = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Specify the rotation angle for the <b>«{ $gate_name }»</b> gate.<br>
    You can pick a value from the options (e.g., π/2, π/4).

apply_gate_select_target_qubit = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Select the target qubit to apply the <b>«{ $gate_name }»</b> gate.

apply_gate_select_target_qubit_measurement = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Select qubits to measure.<br>
    You can measure all qubits at once or choose a specific one.


apply_gate_select_first_control = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Select the control qubit for the <b>«{ $gate_name }»</b> gate.

apply_gate_select_second_control = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Select the second control qubit for the <b>«{ $gate_name }»</b> gate.

circuit_edit_menu = 
    <b>{ $circuit_name }</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    ℹ️ Choose an action:ㅤㅤㅤㅤ

circuit_rename_prompt = Enter a new name for the quantum circuit (max 50 characters):
circuit_name_invalid = ❌ Invalid name! Name must not be empty and exceed 50 characters.
circuit_name_not_unique = ❌ A circuit with this name already exists! Please choose another one.

delete_gate_message = 
    { $has_gates ->
        [True]  <b>{ $circuit_name }</b>
                <br>
                <pre>{ $circuit_diagram }</pre>
                <br>
                Applied gates history:
                { $gates_table }
                ℹ️ Select the gate number to delete.
        [False] <b>{ $circuit_name }</b>
                <br>
                <pre>{ $circuit_diagram }</pre>
                <br>
                ℹ️ History is empty. No gates to delete.
        *[default]  <b>{ $circuit_name }</b>
                    <br>
                    <pre>{ $circuit_diagram }</pre>
                    <br>
                    Applied gates history:
                    { $gates_table }
                    ℹ️ Select the gate number to delete.
    }

export_menu_text = 
    { $complexity_level -> 
        [Researcher] 
                <b>{ $circuit_name }</b>
                <br>
                <pre>{ $circuit_diagram }</pre>
                <br>
                ℹ️ Choose export format:
        *[default]
                <b>{ $circuit_name }</b>
                <br>
                <pre>{ $circuit_diagram }</pre>
                <br>
                • 🔹 <b>OpenQASM 2.0</b> — .qasm file with declarative circuit description. Supported by many quantum platforms<br>
                • 🔸 <b>OpenQASM 3.0</b> — Modern .qasm format with extended syntax (functions, loops, classical operations)<br>
                • 🐍 <b>AriQuantum</b> — .py file with Python code using the ariquantum library<br>
                • 🐍 <b>Qiskit</b> — .py file with Python code using qiskit and qiskit_aer
                <br><br>
                ℹ️ Choose export format:
    }


export_success_text =
    { $format_name ->
        [AriQuantum]
            📤 <b>Export of "{ $circuit_name }"</b>
    
            🔄 Format: <b>{ $format_name }</b>

            <pre><code class="language-python">{ $code }</code></pre>
        [Qiskit]
            📤 <b>Export of "{ $circuit_name }"</b>
    
            🔄 Format: <b>{ $format_name }</b>
            
            <blockquote expandable>⚠️ In Qiskit, measurement results (basis states of the state vector and individual shot outcomes) are written to classical bits in the reverse order relative to qubits. For example, the state |110⟩ means: q₂=1, q₁=1, q₀=0 → classical result "110".
            
            In AriQuantum (both in the Python library and Telegram bot), |110⟩ is read as |q₀q₁q₂⟩ (q₀=1, q₁=1, q₂=0). This isn't a bug — just different conventions: AriQuantum uses big-endian (human-intuitive), while Qiskit uses little-endian (like classical numbers).
            </blockquote>
            <pre><code class="language-python">{ $code }</code></pre>
        *[default]
            📤 <b>Export of "{ $circuit_name }"</b>
    
            🔄 Format: <b>{ $format_name }</b>

            <pre>{ $code }</pre>
    }


# Statuses
control_qubit_already_selected = This qubit is already selected! ⚪️
gate_applied_successfully = Gate applied successfully! ✅
selection_reset = Selection reset 🔄
circuit_cleared = Circuit cleared! All gates removed. ✅
circuit_deleted = Circuit deleted! 🗑️
measurement_applied_single = Measurement applied! 📏
measurement_applied_multiple = Measurement applied to { $count } qubits! 📏
gate_cannot_be_applied_to_measured_qubits = ❌ Quantum gate "{ $gate_name }" cannot be applied to measured qubits.
delete_gate_success = ✅ Gate successfully deleted from the circuit.
delete_measurements_success = ✅ Removed { $count } measurements. 
export_success_alert = ✅ Circuit exported successfully!


# Buttons
circuit_edit_clear_button = 🧹 Clear circuit
circuit_edit_delete_button = 🗑️ Delete circuit
circuit_edit_rename_button = ✏️ Rename
circuit_edit_export_button = 📤 Export circuit
reset_qubit_selection = 🔄 Cancel selection
circuit_apply_gate_button = ➕ Apply gate
circuit_edit_button = 📋 Edit circuit
circuit_simulate_button = 🚀 Run simulation
gate_measure_btn = 📏 Measure
measure_all_qubits_button = 📏 Measure all qubits
circuit_edit_delete_gate_button = ✂️ Delete gate
delete_all_measurements_button = Remove all measurements

settings_ask_at_runtime = ❓ Choose at runtime

error_input_circuit_name = 
    An error has occurred! Please send a <b>text message</b> with the unique circuit name.  
    For example: "My Circuit" or "Bell State". The circuit name must not exceed 50 characters.
    

error_num_qubits_invalid = 
    Invalid number of qubits.  
    Maximum allowed: { $max_qubits }.  
    You can return to the main menu with /start.
    

error_input_num_qubits = 
    Invalid input.  
    Please enter a number from 1 to { $max_qubits } (this is the maximum number of qubits per circuit).
    

test = OK

// User settings 
settings_menu = 
    ⚙️ <b>Settings</b>

    🌐 Language: <b>{ $language }</b>
    🎓 Complexity level: <b>{ $complexity }</b>
    💻 Backend: <b>{ $backend }</b>
    🤖 Automatic circuit naming: <b>{ $automatic_name }</b>
    🔢 Text input for qubits: <b>{ $qubit_input_text }</b>
    📊 Simulation shots: <b>{ $simulation_shots }</b>
    🖼 Charts format: <b>{ $output_mode }</b>

settings_language_button = 🌐 Language
settings_complexity_button = 🎓 Complexity level
settings_backend_button = 💻 Backend
settings_automatic_name_button = 🤖 Automatic circuit naming
settings_qubit_input_text_button = 🔢 Text input for qubits
settings_simulation_shots_button = 📊 Simulation shots

settings_output_mode_button = 🖼 Output format

settings_output_mode_menu = 
    🖼 <b>Charts and circuits output format</b>

    🧩 <b>HTML widget</b> — a nice interactive chart right in the message (private chat with the bot only).
    🔤 <b>ASCII text</b> — plain text output that works everywhere.

    ℹ️ Current format: { $current }

settings_output_mode_widget = 🧩 HTML widget
settings_output_mode_ascii = 🔤 ASCII text
settings_output_mode_updated = 🖼 Output format updated!

settings_language_menu = 
    🌐 <b>Language Selection</b>
    
    ℹ️ Current language: { $current }

settings_complexity_menu = 
    🎓 <b>Complexity Level</b>
    <br>
    <ul>
        <li>🐣 <b>Novice</b> — detailed explanations, step-by-step instructions, simplified terminology</li>
        <li>👨🏼‍🎓 <b>Student</b> — balanced approach with essential concepts without oversimplification</li>
        <li>👨🏼‍💻 <b>Researcher</b> — minimal explanations, only technical details and advanced features</li>
    </ul>
    <br>
    ℹ️ Current level: <b>{ $current }</b>

settings_backend_menu = 
    💻 <b>Quantum Computing Backend</b>    
    <br>
    { $complexity_level ->
        [Novice]
            <ul>
                <li><b>AriQuantum</b> — our own emulator, faster for simple circuits (up to 6 qubits).</li>
                <li><b>Qiskit</b> — industry standard from IBM, more reliable for complex circuits with measurements.</li>
            </ul>
       *[default]
            <ul>
                <li><b>AriQuantum</b> — our optimized emulator, faster on small circuits (up to 6 qubits), but may work incorrectly with gates applied after measurements, as it only displays the results of the last measurement.</li>
                <li><b>Qiskit</b> — industry standard from IBM, correctly handles measurements and subsequent gates by storing results in a classical register.</li>
            </ul>
    }
    <br>
    ℹ️ Current backend: { $current }

qubits = qubits 

settings_simulation_shots_menu = 
    📊 <b>Number of Simulation Shots</b>
    
    More shots = more accurate statistics, but slower calculation.

    ℹ️ Current value: { $current }

bool_yes = Yes ✅

bool_no = No ❌

settings_language_updated = 🌐 Language updated!
settings_complexity_updated = 🎓 Complexity level updated!
settings_backend_updated = 💻 Backend updated!
settings_simulation_shots_updated = 📊 Number of shots updated!
settings_automatic_name_updated = 🤖 Automatic circuit naming updated!
settings_qubit_input_text_updated = 🔢 Qubit input mode updated!

simulation_select_backend = 
    💻 <b>Please select a backend for this simulation:</b>
    <br><br>
    • <b>AriQuantum</b> — faster for simple circuits (up to 6 qubits).
    • <b>Qiskit</b> — IBM standard, supports complex circuits up to 10 qubits.

simulation_select_shots = 
    📊 <b>Please select the number of simulation shots:</b>

simulation_forced_qiskit = ℹ️ Circuit has > 6 qubits, so the simulation was forced to use the <b>Qiskit</b> backend.<br><br>

simulation_result_with_measurements = 
    🚀 <b>Circuit Simulation "{ $circuit_name }"</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    { $forced_warning }💻 Backend used: <b>{ $backend }</b><br>
    ⏱️ Execution time: <b>{ $execution_time } sec</b>
    <br><br>
    📌 <b>State before first measurement:</b>
    <pre>{ $braket_state }</pre>
    <br>
    📊 <b>Results of { $shots } shots:</b>
    <pre>{ $counts }</pre>

simulation_result_without_measurements = 
    🚀 <b>Circuit Simulation "{ $circuit_name }"</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    { $forced_warning }💻 Backend used: <b>{ $backend }</b><br>
    ⏱️ Execution time: <b>{ $execution_time } sec</b>
    <br><br>
    📌 <b>State vector:</b>
    <pre>{ $braket_state }</pre>

simulation_result_with_measurements_widget = 
    🚀 <b>Circuit Simulation "{ $circuit_name }"</b>
    <br>
    <pre>{ $circuit_diagram }</pre>
    <br>
    { $forced_warning }💻 Backend used: <b>{ $backend }</b><br>
    ⏱️ Execution time: <b>{ $execution_time } sec</b>
    <br><br>
    📌 <b>State before first measurement:</b>
    <pre>{ $braket_state }</pre>

simulation_widget_detail_count = Occurred
simulation_widget_detail_of = of
simulation_widget_detail_share = Share
simulation_widget_detail_qubits = Qubits

simulation_widget_title = 📊 <b>Results of { $shots } shots</b>

simulation_widget_hidden_note = ℹ️ Showing the { $shown } most frequent states out of { $total }

simulation_counts_fallback = 
    📊 <b>Results of { $shots } shots:</b>
    <pre>{ $counts }</pre>

simulation_back_to_circuit_button = ◀️ Back to circuit
simulation_error = ❌ Error during circuit simulation!
simulation_timeout_error = ❌ Симуляция превысила лимит времени (10 сек)!

profile = 
    👤 <b>Profile</b>

    Name: { $first_name }
    Username: { $username }

    📊 <b>Statistics:</b>
    • Circuits created: { $circuits_count }/{ $max_circuits }
    • Simulations run: { $simulations_count }

command_admin = 
    🥷🏼 <b>Admin Panel</b>

    1. User statistics
    2. Circuit and simulation statistics
    3. Backend statistics
    4. Block user

    ℹ️ Select an_action below:

admin_users_btn = 👥 Users
admin_circuits_btn = ⛓️ Circuits
admin_backends_btn = 💻 Backends
admin_blocked_btn = ❌ Block user
admin_message_btn = 📩 Send a message
admin_stat_btn = 📊 Settings
admin_menu_btn = ⏪ Admin menu
admin_users_activity_btn = 📊 User activity
admin_user_search_btn = 🔍 User search
admin_users_new_stats_btn = 📈 Daily statistics

admin_users = 
    <b>Statistics: «👥 Users»</b>

    <b>TOTAL users:</b> 👥 { $all_users }

    <b>TOP 5 by usage (days):</b>
    { $top5_days_text }

    <b>TOP 5 by usage (circuits):</b>
    { $top5_circuits_text }

    <b>TOP 5 by usage (simulations):</b>
    { $top5_simulations_text }

    <b>Usage statistics for the last 20 days:</b>
    { $stat_users20 }

admin_circuits = 
    <b>Statistics: «⛓️ Circuits»</b>

    <b>CURRENT circuits:</b> { $circuits_now }
    <b>TOTAL circuits created:</b> { $circuits_all }

    <b>CURRENT simulations:</b> { $simulations_now }
    <b>TOTAL simulations run:</b> { $simulations_all }

    <b>AVERAGE number of qubits:</b> { $avg_qubits }
    <b>AVERAGE execution time:</b> { $avg_time } sec

    <b>Circuit and simulation activity over the last 20 days:</b>
    { $stat_circuits20 }

admin_backends = 
    <b>Statistics: «💻 Backends»</b>

    <b>🚀 Simulations:</b>
    { $backends_simulations_text }

    <b>📊 Qubits:</b>
    { $backends_avg_qubits_text }

    <b>⏱️ Execution time:</b>
    { $backends_avg_time_text }

admin_block_prompt = 
    🔒 Enter the user ID or username (with or without @) to block:

admin_block_success = 
    ✅ User { $user } has been successfully blocked!

admin_block_not_found = 
    ❌ User "{ $user }" not found in the database.

admin_statistics = 
    📊 <b>User settings statistics</b>

    🔗 <b>Traffic sources:</b>
    { $ref_sources }

    🌍 <b>Telegram language:</b>
    { $tg_locales }

    🌐 <b>Languages:</b>
    { $languages }

    🎓 <b>Complexity levels:</b>
    { $complexity_levels }

    💻 <b>Backends:</b>
    { $backends }

    🤖 <b>Auto-generated circuit names:</b>
    { $automatic_name }

    🔢 <b>Text input for qubit count:</b>
    { $qubit_input }

    📈 <b>Simulation shots:</b>
    { $simulation_shots }
    Average value: { $shots_avg }

help_message = 
    🌌 <b>AriQuantum | Quantum computing emulator</b>
    <br><br>
    This bot lets you explore and experiment with quantum computing directly in Telegram.
    <br><br>
    🔹 <b>Key features:</b>
    <ul>
        <li>Create quantum circuits with 1 to 10 qubits</li>
        <li>Apply single-qubit, two-qubit, and three-qubit gates</li>
        <li>Perform measurements and analyze results</li>
        <li>Run simulations and get shot statistics</li>
    </ul>
    <br>
    💻 <b>Backends:</b>
    <ul>
        <li><b>AriQuantum</b> — our custom emulator. Fast for small circuits (up to 6 qubits), but doesn’t store measurement results in a classical register.</li>
        <li><b>Qiskit</b> — industry-standard framework by IBM. Fully supports measurements and subsequent operations.</li>
    </ul>
    <br>
    🎓 <b>Complexity levels:</b>
    <ul>
        <li>🐣 <b>Novice</b> — detailed explanations, step-by-step instructions, simplified terminology</li>
        <li>👨🏼‍🎓 <b>Student</b> — balanced approach with essential concepts without oversimplification</li>
        <li>👨🏼‍💻 <b>Researcher</b> — minimal explanations, only technical details and advanced features</li>
    </ul>
    <br>
    ⚠️ <b>Important:</b>
    <ul>
        <li>Quantum gates cannot be applied to measured qubits</li>
        <li>Circuits without measurements show the state vector in Dirac notation</li>
        <li>Circuits with measurements show the pre-measurement state + shot statistics</li>
        <li>Measurement results (computational basis states and individual shot outcomes) are mapped to classical bits in the same order as the qubits. For example, the state |110⟩ means: q₀=1, q₁=1, q₂=0 → classical result "110".</li>
    </ul>
    <br>
    ℹ️ Use the menu or commands to navigate.

admin_broadcast_prompt = 
    📢 Enter the broadcast message (Formatting is done through html tags) for all users in <b>RUSSIAN</b>:

admin_broadcast_prompt_en = 
    🇬🇧 Great. Now enter the broadcast message in <b>ENGLISH</b>:

admin_broadcast_started = 
    🚀 Broadcast started in background. You'll receive a report when done.

admin_broadcast_empty = 
    ❌ Broadcast message cannot be empty.

# =============== NEW ================

admin_new_user_notification = 
    🆕 <b>New User</b>

    👤 { $user_link }

    🆔 ID: <b>{ $user_id }</b>
    📛 Username: { $username }
    📝 Full name: <b>{ $full_name }</b>
    🔗 Source: <b>{ $source }</b>
    { $locale_flag } Telegram language: <b>{ $locale_code }</b>

admin_new_circuit_notification = 
    ⚛️ <b>New Circuit</b>

    Circuit "{ $circuit_name }" was created by { $user } with { $num_qubits } qubits.

admin_user_search_prompt = 
    🔍 <b>User Search</b>

    Send the ID, username, first name, or last name of the user.

admin_user_search_empty = ❌ The query cannot be empty.

admin_user_not_found = ❌ User matching "<code>{ $query }</code>" was not found.

admin_user_block_btn = 🚫 Block
admin_user_unblock_btn = ✅ Unblock

admin_user_status_blocked = blocked
admin_user_status_active = unblocked

admin_user_block_toggled = ✅ User has been { $status }.

admin_user_profile = 
    { $role_emoji } <b>User Profile</b>
    <br><br>
    🆔 ID: { $user_id }<br>
    📛 Username: { $username }<br>
    📝 Name: { $first_name } { $last_name }<br>
    { $is_blocked ->
        [true] 🚫 Status: <b>Blocked</b>
       *[other] ✅ Status: <b>Active</b>
    }<br>
    📅 Joined: { $date_joined }<br>
    🕐 Last activity: { $last_activity }<br>
    🔗 Source: { $ref_source }<br>
    🌍 Telegram language: { $tg_locate }<br>
    <br>
    <b>⚙️ Settings:</b><br>
    🌐 Language: { $language }<br>
    🎓 Complexity: { $complexity }<br>
    💻 Backend: { $backend }<br>
    🔢 Shots: { $shots }<br>
    🤖 Auto-name circuit: { $automatic_name }<br>
    🔢 Text input for qubits: { $qubit_input_text }<br>
    <br>
    <b>📐 Circuits:</b><br>
    • Total created: { $total_circuits_created }<br>
    • Currently in DB: { $circuits_count }<br>
    { $circuits_list }<br>
    { $circuits_more ->
        [0] { "" }
       *[other] <i>... and { $circuits_more } more circuits</i>
    }<br>
    <b>🧪 Simulations:</b><br>
    • Total run: { $total_simulations_run }<br>
    • Currently in DB: { $simulations_count }<br>
    <b>By backends:</b><br>
    { $backend_stats_list }<br>
    <b>Overall:</b><br>
    • Avg qubits: { $overall_avg_qubits }<br>
    • Avg time: { $overall_avg_time }<br>
    <br>
    <b>📊 Activity:</b><br>
    • Days active: { $activity_count }<br>
    { $activity_list }<br>
    { $activity_more ->
        [0] { "" }
       *[other] <i>... and { $activity_more } more days</i>
    }

admin_users_new_stats_text =
    📈 <b>New users by day:</b>
    
    { $stats_list }