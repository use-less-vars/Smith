import QtQuick 6.0
import QtQuick.Window 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

import QtCore 6.0

Dialog {
    id: configDialog
    title: "Configuration"
    modal: true
    standardButtons: Dialog.Ok | Dialog.Cancel

    width: 600
    height: 500

    property var currentConfig: ({})

    // File dialog bridge connections
    Connections {
        target: fileDialogBridge
        function onPathSelected(selectedPath, tag) {
            if (tag === "workspace") {
                workspacePathField.text = selectedPath
            } else if (tag === "logdir") {
                logDirField.text = selectedPath
            }
        }
    }

    onAccepted: {
        // Save configuration - collect all fields
        var config = {
            // API fields
            "api_key": apiKeyField.text,
            "model": modelField.text,
            "base_url": baseUrlField.text,
            "provider_type": providerTypeField.currentText,
            "provider_config": {},
            
            // Agent fields
            "temperature": temperatureField.value,
            "max_turns": maxTurnsField.value,
            "system_prompt": systemPromptField.text,
            "workspace_path": workspacePathField.text || null,
            "detail": detailField.currentText,
            "tool_output_token_limit": toolOutputTokenLimitField.value,
            
            // Token monitoring
            "token_monitor_enabled": tokenMonitorEnabledField.checked,
            "token_monitor_warning_threshold": tokenMonitorWarningThresholdField.value,
            "token_monitor_critical_threshold": tokenMonitorCriticalThresholdField.value,
            
            // Turn monitoring
            "turn_monitor_enabled": turnMonitorEnabledField.checked,
            "turn_monitor_warning_threshold": turnMonitorWarningThresholdField.value,
            "turn_monitor_critical_threshold": turnMonitorCriticalThresholdField.value,
            "critical_countdown_turns": criticalCountdownTurnsField.value,
            
            // Logging
            "enable_logging": enableLoggingField.checked,
            "log_dir": logDirField.text,
            "log_level": logLevelField.currentText,
            "enable_file_logging": enableFileLoggingField.checked,
            "enable_console_logging": enableConsoleLoggingField.checked,
            "jsonl_format": jsonlFormatField.checked,
            "max_file_size_mb": maxFileSizeMbField.value,
            "max_backup_files": maxBackupFilesField.value,
            
            // Conversation pruning
            "max_history_turns": maxHistoryTurnsField.value,
            "keep_initial_query": keepInitialQueryField.checked,
            "keep_system_messages": keepSystemMessagesField.checked
        }
        
        // Handle max_tokens (optional)
        if (!maxTokensUnlimitedCheck.checked && maxTokensField.value > 0) {
            config["max_tokens"] = maxTokensField.value
        }
        
        // Update configuration via presenter
        presenter.update_config_from_gui(config)
        
        // Save to user config file
        if (typeof presenter.save_user_config === "function") {
            // Save the full configuration (presenter.config includes merged values)
            presenter.save_user_config()
        }
    }

    onRejected: {
        // Discard changes
        loadConfig()
    }

    function loadConfig() {
        // Load current configuration from presenter
        if (typeof presenter.config !== "undefined") {
            currentConfig = presenter.config
            
            // API fields
            apiKeyField.text = currentConfig.api_key || ""
            modelField.text = currentConfig.model || ""
            baseUrlField.text = currentConfig.base_url || ""
            
            // Set provider type
            var providerIndex = providerTypeModel.indexOf(currentConfig.provider_type || "")
            if (providerIndex >= 0) {
                providerTypeField.currentIndex = providerIndex
            }
            
            // Agent fields
            temperatureField.value = currentConfig.temperature || 0.2
            maxTurnsField.value = currentConfig.max_turns || 100
            
            // Max tokens handling
            if (currentConfig.max_tokens && currentConfig.max_tokens > 0) {
                maxTokensUnlimitedCheck.checked = false
                maxTokensField.value = currentConfig.max_tokens
            } else {
                maxTokensUnlimitedCheck.checked = true
                maxTokensField.value = 2000
            }
            
            systemPromptField.text = currentConfig.system_prompt || ""
            workspacePathField.text = currentConfig.workspace_path || ""
            
            // Detail level
            var detailValue = currentConfig.detail || "normal"
            var detailIndex = detailField.find(detailValue)
            if (detailIndex >= 0) {
                detailField.currentIndex = detailIndex
            }
            
            toolOutputTokenLimitField.value = currentConfig.tool_output_token_limit || 10000
            
            // Token monitoring
            tokenMonitorEnabledField.checked = currentConfig.token_monitor_enabled !== false
            tokenMonitorWarningThresholdField.value = currentConfig.token_monitor_warning_threshold || 35000
            tokenMonitorCriticalThresholdField.value = currentConfig.token_monitor_critical_threshold || 50000
            
            // Turn monitoring
            turnMonitorEnabledField.checked = currentConfig.turn_monitor_enabled !== false
            turnMonitorWarningThresholdField.value = currentConfig.turn_monitor_warning_threshold || 0.8
            turnMonitorCriticalThresholdField.value = currentConfig.turn_monitor_critical_threshold || 0.95
            criticalCountdownTurnsField.value = currentConfig.critical_countdown_turns || 5
            
            // Logging
            enableLoggingField.checked = currentConfig.enable_logging !== false
            logDirField.text = currentConfig.log_dir || "./logs"
            
            var logLevelValue = currentConfig.log_level || "INFO"
            var logLevelIndex = logLevelField.find(logLevelValue)
            if (logLevelIndex >= 0) {
                logLevelField.currentIndex = logLevelIndex
            }
            
            enableFileLoggingField.checked = currentConfig.enable_file_logging !== false
            enableConsoleLoggingField.checked = currentConfig.enable_console_logging || false
            jsonlFormatField.checked = currentConfig.jsonl_format !== false
            maxFileSizeMbField.value = currentConfig.max_file_size_mb || 10
            maxBackupFilesField.value = currentConfig.max_backup_files || 5
            
            // Conversation pruning
            maxHistoryTurnsField.value = currentConfig.max_history_turns || 0
            keepInitialQueryField.checked = currentConfig.keep_initial_query !== false
            keepSystemMessagesField.checked = currentConfig.keep_system_messages !== false
        }
    }

    Component.onCompleted: {
        loadConfig()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 5

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            TabButton { text: "API" }
            TabButton { text: "Agent" }
            TabButton { text: "Monitoring" }
            TabButton { text: "Logging" }
            TabButton { text: "Conversation" }
        }

        StackLayout {
            id: stackLayout
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            // API Tab
            ScrollView {
                clip: true
                ColumnLayout {
                    width: stackLayout.width
                    spacing: 10
                    GroupBox {
                        title: "API Configuration"
                        Layout.fillWidth: true
                        GridLayout {
                            columns: 2
                            anchors.fill: parent
                            rowSpacing: 5
                            columnSpacing: 10
                            Label { text: "API Key:" }
                            TextField {
                                id: apiKeyField
                                Layout.fillWidth: true
                                echoMode: TextInput.Password
                                placeholderText: "Enter your API key"
                            }
                            Label { text: "Model:" }
                            TextField {
                                id: modelField
                                Layout.fillWidth: true
                                placeholderText: "e.g., gpt-4-turbo, deepseek-chat"
                            }
                            Label { text: "Base URL:" }
                            TextField {
                                id: baseUrlField
                                Layout.fillWidth: true
                                placeholderText: "e.g., https://api.openai.com/v1"
                            }
                            Label { text: "Provider Type:" }
                            ComboBox {
                                id: providerTypeField
                                Layout.fillWidth: true
                                model: ListModel {
                                    id: providerTypeModel
                                    ListElement { text: "openai" }
                                    ListElement { text: "openai_compatible" }
                                    ListElement { text: "anthropic" }
                                }
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // Agent Tab
            ScrollView {
                clip: true
                ColumnLayout {
                    width: stackLayout.width
                    spacing: 10
                    GroupBox {
                        title: "Agent Settings"
                        Layout.fillWidth: true
                        GridLayout {
                            columns: 2
                            anchors.fill: parent
                            rowSpacing: 5
                            columnSpacing: 10
                            // Temperature
                            Label { text: "Temperature:" }
                            Row {
                                Layout.fillWidth: true
                                spacing: 10
                                Slider {
                                    id: temperatureField
                                    from: 0.0
                                    to: 2.0
                                    stepSize: 0.01
                                    value: 0.2
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: temperatureField.value.toFixed(2)
                                    Layout.alignment: Qt.AlignVCenter
                                }
                            }
                            // Max Turns
                            Label { text: "Max Turns:" }
                            SpinBox {
                                id: maxTurnsField
                                from: 1
                                to: 1000
                                stepSize: 1
                                editable: true
                            }
                            // Max Tokens (optional)
                            Label { text: "Max Tokens:" }
                            RowLayout {
                                CheckBox {
                                    id: maxTokensUnlimitedCheck
                                    text: "Unlimited"
                                    checked: true
                                }
                                SpinBox {
                                    id: maxTokensField
                                    from: 1
                                    to: 1000000
                                    stepSize: 1000
                                    editable: true
                                    enabled: !maxTokensUnlimitedCheck.checked
                                }
                            }
                            // System Prompt
                            Label { text: "System Prompt:" }
                            TextArea {
                                id: systemPromptField
                                Layout.fillWidth: true
                                placeholderText: "Optional custom system prompt"
                                wrapMode: Text.Wrap
                            }
                            // Workspace Path
                            Label { text: "Workspace Path:" }
                            RowLayout {
                                TextField {
                                    id: workspacePathField
                                    Layout.fillWidth: true
                                    placeholderText: "Leave empty for unrestricted"
                                }
                                Button {
                                    text: "Browse"
                                    onClicked: fileDialogBridge.openFileDialog(workspacePathField.text, "workspace")
                                }
                            }
                            // Detail Level
                            Label { text: "Detail Level:" }
                            ComboBox {
                                id: detailField
                                model: ["minimal", "normal", "verbose"]
                            }
                            // Tool Output Token Limit
                            Label { text: "Tool Output Limit:" }
                            SpinBox {
                                id: toolOutputTokenLimitField
                                from: 1000
                                to: 100000
                                stepSize: 1000
                                editable: true
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // Monitoring Tab
            ScrollView {
                clip: true
                ColumnLayout {
                    width: stackLayout.width
                    spacing: 10
                    GroupBox {
                        title: "Token Monitoring"
                        Layout.fillWidth: true
                        GridLayout {
                            columns: 2
                            anchors.fill: parent
                            rowSpacing: 5
                            columnSpacing: 10
                            CheckBox {
                                id: tokenMonitorEnabledField
                                text: "Enable Token Monitoring"
                                checked: true
                            }
                            Item { }
                            Label { text: "Warning Threshold:" }
                            SpinBox {
                                id: tokenMonitorWarningThresholdField
                                from: 1000
                                to: 200000
                                stepSize: 1000
                                editable: true
                            }
                            Label { text: "Critical Threshold:" }
                            SpinBox {
                                id: tokenMonitorCriticalThresholdField
                                from: 1000
                                to: 200000
                                stepSize: 1000
                                editable: true
                            }
                        }
                    }
                    GroupBox {
                        title: "Turn Monitoring"
                        Layout.fillWidth: true
                        GridLayout {
                            columns: 2
                            anchors.fill: parent
                            rowSpacing: 5
                            columnSpacing: 10
                            CheckBox {
                                id: turnMonitorEnabledField
                                text: "Enable Turn Monitoring"
                                checked: true
                            }
                            Item { }
                            Label { text: "Warning Threshold:" }
                            Row {
                                Layout.fillWidth: true
                                spacing: 10
                                Slider {
                                    id: turnMonitorWarningThresholdField
                                    from: 0.0
                                    to: 1.0
                                    stepSize: 0.01
                                    value: 0.8
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: turnMonitorWarningThresholdField.value.toFixed(2)
                                    Layout.alignment: Qt.AlignVCenter
                                }
                            }
                            Label { text: "Critical Threshold:" }
                            Row {
                                Layout.fillWidth: true
                                spacing: 10
                                Slider {
                                    id: turnMonitorCriticalThresholdField
                                    from: 0.0
                                    to: 1.0
                                    stepSize: 0.01
                                    value: 0.95
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: turnMonitorCriticalThresholdField.value.toFixed(2)
                                    Layout.alignment: Qt.AlignVCenter
                                }
                            }
                            Label { text: "Critical Countdown Turns:" }
                            SpinBox {
                                id: criticalCountdownTurnsField
                                from: 1
                                to: 20
                                stepSize: 1
                                editable: true
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // Logging Tab
            ScrollView {
                clip: true
                ColumnLayout {
                    width: stackLayout.width
                    spacing: 10
                    GroupBox {
                        title: "Logging Settings"
                        Layout.fillWidth: true
                        GridLayout {
                            columns: 2
                            anchors.fill: parent
                            rowSpacing: 5
                            columnSpacing: 10
                            CheckBox {
                                id: enableLoggingField
                                text: "Enable Logging"
                                checked: true
                            }
                            Item { }
                            Label { text: "Log Directory:" }
                            RowLayout {
                                TextField {
                                    id: logDirField
                                    Layout.fillWidth: true
                                    placeholderText: "./logs"
                                }
                                Button {
                                    text: "Browse"
                                    onClicked: fileDialogBridge.openFileDialog(logDirField.text, "logdir")
                                }
                            }
                            Label { text: "Log Level:" }
                            ComboBox {
                                id: logLevelField
                                model: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                            }
                            CheckBox {
                                id: enableFileLoggingField
                                text: "Enable File Logging"
                                checked: true
                            }
                            Item { }
                            CheckBox {
                                id: enableConsoleLoggingField
                                text: "Enable Console Logging"
                                checked: false
                            }
                            Item { }
                            CheckBox {
                                id: jsonlFormatField
                                text: "JSONL Format"
                                checked: true
                            }
                            Item { }
                            Label { text: "Max File Size (MB):" }
                            SpinBox {
                                id: maxFileSizeMbField
                                from: 1
                                to: 1000
                                stepSize: 1
                                editable: true
                            }
                            Label { text: "Max Backup Files:" }
                            SpinBox {
                                id: maxBackupFilesField
                                from: 1
                                to: 50
                                stepSize: 1
                                editable: true
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // Conversation Tab
            ScrollView {
                clip: true
                ColumnLayout {
                    width: stackLayout.width
                    spacing: 10
                    GroupBox {
                        title: "Conversation Pruning"
                        Layout.fillWidth: true
                        GridLayout {
                            columns: 2
                            anchors.fill: parent
                            rowSpacing: 5
                            columnSpacing: 10
                            Label { text: "Max History Turns:" }
                            SpinBox {
                                id: maxHistoryTurnsField
                                from: 0
                                to: 1000
                                stepSize: 1
                                editable: true
                            }
                            CheckBox {
                                id: keepInitialQueryField
                                text: "Keep Initial Query"
                                checked: true
                            }
                            Item { }
                            CheckBox {
                                id: keepSystemMessagesField
                                text: "Keep System Messages"
                                checked: true
                            }
                            Item { }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }
            }
        }
    }
}