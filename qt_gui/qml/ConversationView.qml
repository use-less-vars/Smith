import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ListView {
    id: conversationView
    anchors.fill: parent
    spacing: 4
    clip: true
    
    // Model will be set via context property "conversationModel"
    model: conversationModel
    
    delegate: MessageDelegate {
        // The delegate automatically receives the model roles via its properties
    }    
    ScrollBar.vertical: ScrollBar {
        policy: ScrollBar.AlwaysOn
    }
}