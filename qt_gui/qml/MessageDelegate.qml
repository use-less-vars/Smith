import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// MessageDelegate.qml
// Component for displaying a single conversation message with role-based styling

Item {
    id: delegateRoot
    width: ListView.view ? ListView.view.width : parent.width
    height: contentColumn.implicitHeight + 16

    // Expose model properties for easier binding
    property var message: model
    property string messageRole: model.role || ""
    property string messageContent: model.content || ""
    property string htmlContent: model.htmlContent || ""
    property bool isFinal: model.isFinal || false
    property bool isError: model.isError || false
    property string toolName: model.toolName || ""
    
    Rectangle {
        id: background
        anchors.fill: parent
        color: {
            // Different background colors based on message role
            if (delegateRoot.messageRole === "user") {
                return "#f0f8ff"  // Light blue
            } else if (delegateRoot.messageRole === "assistant") {
                return "#f9f9f9"  // Light gray
            } else if (delegateRoot.messageRole === "tool") {
                return "#f0fff0"  // Light green
            } else if (delegateRoot.messageRole === "system") {
                return "#fff8f0"  // Light orange
            } else {
                return "#ffffff"
            }
        }
        border.color: "#e0e0e0"
        border.width: 1
        radius: 4
        
        // Highlight final answers with blue border
        Rectangle {
            visible: delegateRoot.isFinal
            anchors.fill: parent
            color: "transparent"
            border.color: "blue"
            border.width: 2
            radius: 4
        }
        
        // Error state
        Rectangle {
            visible: delegateRoot.isError
            anchors.fill: parent
            color: "transparent"
            border.color: "red"
            border.width: 2
            radius: 4
        }
    }
    
    ColumnLayout {
        id: contentColumn
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
            margins: 8
        }
        spacing: 4
        
        // Header with role icon and tool name
        RowLayout {
            id: headerRow
            Layout.fillWidth: true
            spacing: 6
            
            Text {
                id: roleIcon
                font.pixelSize: 16
                text: {
                    if (delegateRoot.messageRole === "user") {
                        return "👤"
                    } else if (delegateRoot.messageRole === "assistant") {
                        return "🤖"
                    } else if (delegateRoot.messageRole === "tool") {
                        return "🛠️"
                    } else if (delegateRoot.messageRole === "system") {
                        return "⚙️"
                    }
                    return "📄"
                }
            }
            
            Text {
                id: roleLabel
                font.bold: true
                font.pixelSize: 14
                text: {
                    var label = delegateRoot.messageRole.charAt(0).toUpperCase() + delegateRoot.messageRole.slice(1)
                    if (delegateRoot.messageRole === "tool" && delegateRoot.toolName) {
                        label += " (" + delegateRoot.toolName + ")"
                    }
                    return label
                }
                color: "#333333"
            }
            
            Item { Layout.fillWidth: true } // Spacer
            
            // Final indicator
            Text {
                visible: delegateRoot.isFinal
                text: "⭐ FINAL"
                font.bold: true
                font.pixelSize: 12
                color: "blue"
            }
            
            // Error indicator
            Text {
                visible: delegateRoot.isError
                text: "⚠️ ERROR"
                font.bold: true
                font.pixelSize: 12
                color: "red"
            }
        }
        
        // Content text - supports HTML rendering for markdown
        TextEdit {
            id: contentText
            Layout.fillWidth: true
            wrapMode: TextEdit.Wrap
            readOnly: true
            selectByMouse: true
            text: {
                // Use HTML content if available, otherwise plain text
                if (delegateRoot.htmlContent && delegateRoot.htmlContent.length > 0) {
                    return delegateRoot.htmlContent
                }
                // Plain text fallback with truncation for non-final messages
                var content = delegateRoot.messageContent
                if (!delegateRoot.isFinal && content.length > 500) {
                    return content.substring(0, 500) + "..."
                }
                return content
            }
            textFormat: delegateRoot.htmlContent && delegateRoot.htmlContent.length > 0 ? TextEdit.RichText : TextEdit.PlainText
            font.pixelSize: 14
            color: "#222222"
        }
        
        // Content length indicator
        Text {
            visible: !delegateRoot.isFinal && delegateRoot.messageContent.length > 500
            text: "(" + delegateRoot.messageContent.length + " characters total)"
            font.pixelSize: 11
            color: "#666666"
            font.italic: true
        }
    }
}