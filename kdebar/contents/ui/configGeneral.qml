import QtQuick
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    id: page

    property alias cfg_proxyBaseUrl: proxyBaseUrlField.text
    property alias cfg_refreshIntervalSeconds: refreshIntervalSpin.value
    property alias cfg_longHistorySize: longHistorySpin.value
    property alias cfg_shortHistorySize: shortHistorySpin.value

    Controls.TextField {
        id: proxyBaseUrlField
        Kirigami.FormData.label: i18n("Proxy base URL:")
        placeholderText: "http://localhost:8081"
    }

    Controls.SpinBox {
        id: refreshIntervalSpin
        Kirigami.FormData.label: i18n("Refresh interval:")
        from: 15
        to: 3600
        stepSize: 15
        textFromValue: function(value) {
            return i18np("%1 second", "%1 seconds", value)
        }
        valueFromText: function(text) {
            return parseInt(text, 10)
        }
    }

    Controls.SpinBox {
        id: longHistorySpin
        Kirigami.FormData.label: i18n("Long graph readings:")
        from: 2
        to: 288
    }

    Controls.SpinBox {
        id: shortHistorySpin
        Kirigami.FormData.label: i18n("Short graph readings:")
        from: 2
        to: 288
    }
}
