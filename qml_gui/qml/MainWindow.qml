import QtQuick 6.0
import QtQuick.Window 2.15
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

Window {
    width: 800
    height: 600
    title: "ThoughtMachine QML"
    visible: true
    
    Rectangle {
        anchors.fill: parent
        
        ColumnLayout {
            anchors.fill: parent
            spacing: 5
            
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Conversation History"
                font.bold: true
                font.pixelSize: 20
                padding: 10
            }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                border.color: "gray"
                border.width: 1
                
                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 5
                    
                    ListView {
                        id: conversationView
                        model: conversationModel
                        spacing: 10
                        delegate: conversationDelegate
                        onCountChanged: {
                            // Auto-scroll to bottom when new messages added
                            positionViewAtEnd()
                        }
                    }
                }
            }
            
            // Status bar
            Rectangle {
                Layout.fillWidth: true
                height: 30
                color: "lightgray"
                
                Text {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    verticalAlignment: Text.AlignVCenter
                    text: "Status: Ready"
                }
            }
            
            // Input area
            Rectangle {
                Layout.fillWidth: true
                height: 60
                color: "#f0f0f0"
                border.color: "gray"
                border.width: 1
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 5
                    spacing: 5
                    
                    TextField {
                        id: messageInput
                        Layout.fillWidth: true
                        placeholderText: "Type your message here..."
                        Keys.onReturnPressed: {
                            if (event.modifiers & Qt.ControlModifier) {
                                // Ctrl+Enter for new line
                                insert(cursorPosition, "\n")
                            } else {
                                sendButton.clicked()
                                event.accepted = true
                            }
                        }
                        Keys.onEnterPressed: {
                            sendButton.clicked()
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
                                presenter.on_user_input(text)
                                messageInput.clear()
                            }
                        }
                    }
                }
            }
        }
    }
    
    Component {
        id: conversationDelegate
        
        Rectangle {
            width: conversationView.width
            height: contentColumn.implicitHeight + 20
            color: {
                if (model.role === "user") return "#e6f3ff"
                else if (model.role === "assistant") return "#f0fff0"
                else return "#fff0f0"
            }
            border.color: "lightgray"
            border.width: 1
            radius: 5
            
            Column {
                id: contentColumn
                anchors.fill: parent
                anchors.margins: 10
                spacing: 5
                
                RowLayout {
                    width: parent.width
                    
                    Text {
                        text: "<b>" + (model.role || "unknown") + "</b>"
                        font.pixelSize: 14
                        color: "darkblue"
                    }
                    
                    Text {
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                        text: model.createdAt ? new Date(model.createdAt).toLocaleString() : ""
                        font.pixelSize: 10
                        color: "gray"
                    }
                }
                
                Text {
                    width: parent.width
                    text: model.htmlContent || model.content || ""
                    textFormat: Text.RichText
                    wrapMode: Text.WordWrap
                    font.pixelSize: 12
                    onLinkActivated: Qt.openUrlExternally(link)
                }
                
                // Show tool info if present
                Text {
                    visible: model.toolName
                    text: "Tool: " + model.toolName
                    font.pixelSize: 11
                    color: "darkgreen"
                }
                
                Text {
                    visible: model.isFinal
                    text: "Final Answer"
                    font.pixelSize: 11
                    color: "red"
                    font.bold: true
                }
            }
        }
    }
}