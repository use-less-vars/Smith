import QtQuick 6.0
import QtQuick.Window 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

Window {
    width: 800
    height: 600
    title: "ThoughtMachine QML"
    visible: true

    property bool autoScroll: true
    property int scrollThreshold: 50

    property int inputTokens: 0
    property int outputTokens: 0
    property int contextLength: 0
    property string agentState: "Ready"

    // Input history
    property var inputHistory: []
    property int historyIndex: -1

    // Connect to status bridge signals
    Connections {
        target: statusBridge
        onTokensUpdated: (inputTokenCount, outputTokenCount) => {
            inputTokens = inputTokenCount
            outputTokens = outputTokenCount
        }
        onContextUpdated: (contextCount) => {
            contextLength = contextCount
        }
        onStateChanged: (newState) => {
            agentState = newState
        }
    }
    
    Rectangle {
        anchors.fill: parent
        
        ColumnLayout {
            anchors.fill: parent
            spacing: 5
            
            RowLayout {
                Layout.fillWidth: true
                spacing: 5
                
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.fillWidth: true
                    text: "Conversation History"
                    font.bold: true
                    font.pixelSize: 20
                    padding: 10
                }
                
                Button {
                    text: "Settings"
                    onClicked: {
                        configDialog.open()
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 5

                CheckBox {
                    id: autoScrollCheckBox
                    text: "Auto-scroll"
                    checked: autoScroll
                    onCheckedChanged: autoScroll = checked
                }
            }

            SplitView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: Qt.Vertical
                
                // Conversation view
                Rectangle {
                    SplitView.fillHeight: true
                    SplitView.minimumHeight: 100
                    border.color: "gray"
                    border.width: 1
                    clip: true

                    ScrollView {
                        anchors.fill: parent
                        anchors.margins: 5
                        clip: true

                        ListView {
                            id: conversationView
                            model: conversationModel
                            spacing: 10
                            delegate: MessageDelegate {}
                            onCountChanged: {
                                // Auto-scroll to bottom when new messages added if near bottom
                                if (autoScroll && (contentY + height >= contentHeight - scrollThreshold)) {
                                    positionViewAtEnd()
                                }
                            }
                            onContentHeightChanged: {
                                // Also scroll when content height changes (e.g., streaming updates)
                                if (autoScroll && (contentY + height >= contentHeight - scrollThreshold)) {
                                    positionViewAtEnd()
                                }
                            }
                        }
                    }
                }
                
                // Bottom panel (status bar + input area)
                Rectangle {
                    SplitView.minimumHeight: 100
                    SplitView.preferredHeight: 150
                    border.color: "gray"
                    border.width: 1
                    
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 0

                        // Status bar
                        Rectangle {
                            Layout.fillWidth: true
                            height: 30
                            color: "lightgray"
                            border.width: 0

                            Text {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                verticalAlignment: Text.AlignVCenter
                                text: "State: " + agentState + " | Input: " + inputTokens + " | Output: " + outputTokens + " | Context: " + contextLength
                            }
                        }

                        // Separator
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "gray"
                        }

                        // Input area
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#f0f0f0"
                            border.width: 0

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 5
                                spacing: 5

                                TextArea {
                                    id: messageInput
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    placeholderText: "Type your message here... (Enter to send, Shift+Enter for new line)"
                                    wrapMode: Text.Wrap
                                    inputMethodHints: Qt.ImhMultiLine
                                    readOnly: false
                                    focus: true
                                    Keys.onReturnPressed: {
                                        if (event.modifiers & Qt.ShiftModifier) {
                                            // Shift+Enter: insert new line
                                            insert(cursorPosition, "\n")
                                            event.accepted = true
                                        } else {
                                            // Enter (no modifier) or Ctrl+Enter: send
                                            sendButton.clicked()
                                            event.accepted = true
                                        }
                                    }
                                    Keys.onEnterPressed: {
                                        if (event.modifiers & Qt.ShiftModifier) {
                                            // Shift+Enter: insert new line
                                            insert(cursorPosition, "\n")
                                            event.accepted = true
                                        } else {
                                            // Enter (no modifier) or Ctrl+Enter: send
                                            sendButton.clicked()
                                            event.accepted = true
                                        }
                                    }
                                    Keys.onUpPressed: {
                                        if (inputHistory.length > 0) {
                                            if (historyIndex === -1) {
                                                // Start from most recent (newest)
                                                historyIndex = inputHistory.length - 1
                                                messageInput.text = inputHistory[historyIndex]
                                            } else if (historyIndex > 0) {
                                                // Go older (decrease index)
                                                historyIndex = historyIndex - 1
                                                messageInput.text = inputHistory[historyIndex]
                                            }
                                            // If historyIndex == 0, do nothing (already at oldest)
                                        }
                                        event.accepted = true
                                    }
                                    Keys.onDownPressed: {
                                        if (inputHistory.length > 0 && historyIndex >= 0) {
                                            if (historyIndex < inputHistory.length - 1) {
                                                // Go newer (increase index)
                                                historyIndex = historyIndex + 1
                                                messageInput.text = inputHistory[historyIndex]
                                            } else {
                                                // At newest, clear input
                                                historyIndex = -1
                                                messageInput.text = ""
                                            }
                                        }
                                        event.accepted = true
                                    }
                                }

                                Button {
                                    id: sendButton
                                    text: "Send"
                                    enabled: messageInput.text.trim().length > 0
                                    onClicked: {
                                        var text = messageInput.text.trim()
                                        if (text.length > 0) {
                                            // Add to input history
                                            inputHistory = inputHistory.concat([text])
                                            // Limit history size to 50
                                            if (inputHistory.length > 50) {
                                                inputHistory = inputHistory.slice(inputHistory.length - 50)
                                            }
                                            historyIndex = -1
                                            presenter.on_user_input(text)
                                            messageInput.clear()
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    ConfigDialog {
        id: configDialog
    }

    // Component replaced by MessageDelegate.qml
}