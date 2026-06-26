import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: root

    property real currentBloodSugar: Number.NaN
    property var longHistory: []
    property var shortHistory: []
    property bool loading: true
    property string errorMessage: ""

    readonly property string proxyBaseUrl: normalizeBaseUrl(Plasmoid.configuration.proxyBaseUrl)
    readonly property int refreshIntervalSeconds: Math.max(15, Number(Plasmoid.configuration.refreshIntervalSeconds || 120))
    readonly property int longHistorySize: Math.max(2, Number(Plasmoid.configuration.longHistorySize || 45))
    readonly property int shortHistorySize: Math.max(2, Number(Plasmoid.configuration.shortHistorySize || 15))
    readonly property int maxHistorySize: Math.max(longHistorySize, shortHistorySize)
    readonly property string currentText: isNaN(currentBloodSugar) ? "--" : currentBloodSugar.toFixed(1)
    readonly property string statusText: errorMessage.length > 0 ? errorMessage : (loading ? i18n("Loading CareLink data") : i18n("Last update OK"))
    readonly property int valueWidth: Math.round(Kirigami.Units.gridUnit * 2.6)
    readonly property int graphWidth: Math.round(Kirigami.Units.gridUnit * 2.9)
    readonly property int panelSpacing: Kirigami.Units.smallSpacing
    readonly property int panelWidth: valueWidth + (graphWidth * 2) + (panelSpacing * 2)
    readonly property int panelHeight: Math.round(Kirigami.Units.gridUnit * 1.8)

    preferredRepresentation: compactRepresentation
    width: panelWidth
    height: panelHeight
    implicitWidth: panelWidth
    implicitHeight: panelHeight
    Layout.minimumWidth: panelWidth
    Layout.preferredWidth: panelWidth
    Layout.minimumHeight: Kirigami.Units.gridUnit
    switchWidth: panelWidth
    switchHeight: panelHeight
    Plasmoid.icon: "office-chart-line"

    function normalizeBaseUrl(url) {
        var normalized = String(url || "").trim()
        if (normalized.length === 0) {
            normalized = "http://localhost:8081"
        }
        while (normalized.length > 1 && normalized.charAt(normalized.length - 1) === "/") {
            normalized = normalized.slice(0, -1)
        }
        return normalized
    }

    function endpoint(path) {
        return proxyBaseUrl + path
    }

    function fetchJson(path, callback) {
        var xhr = new XMLHttpRequest()
        xhr.open("GET", endpoint(path))
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE) {
                return
            }

            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    callback("", JSON.parse(xhr.responseText))
                } catch (err) {
                    callback(i18n("Invalid JSON from proxy"), null)
                }
            } else {
                callback(i18n("Proxy HTTP %1", xhr.status), null)
            }
        }
        xhr.onerror = function() {
            callback(i18n("Cannot reach proxy"), null)
        }
        xhr.send()
    }

    function readingValue(reading) {
        if (typeof reading === "number") {
            return Number(reading)
        }
        if (reading && reading.sg !== undefined) {
            return Number(reading.sg)
        }
        return Number.NaN
    }

    function historyValues(data) {
        var values = []
        if (!Array.isArray(data)) {
            return values
        }

        for (var i = 0; i < data.length; i++) {
            var value = readingValue(data[i])
            if (!isNaN(value) && value > 0) {
                values.push(value)
            }
        }
        return values
    }

    function averageValues(values, step) {
        if (step <= 1) {
            return values
        }

        var averaged = []
        for (var i = 0; i < values.length - step; i += step) {
            var total = 0
            for (var offset = 0; offset < step; offset++) {
                total += values[i + offset]
            }
            averaged.push(Math.round((total / step) * 10) / 10)
        }
        return averaged
    }

    function refreshData() {
        loading = true
        errorMessage = ""

        fetchJson("/carelink/get-current-bsd", function(error, data) {
            if (error.length > 0) {
                errorMessage = error
                currentBloodSugar = Number.NaN
                loading = false
                return
            }

            var value = readingValue(data)
            currentBloodSugar = (!isNaN(value) && value > 0) ? value : Number.NaN
        })

        fetchJson("/carelink/get-last-bsd?last-n=" + maxHistorySize, function(error, data) {
            loading = false
            if (error.length > 0) {
                errorMessage = error
                longHistory = []
                shortHistory = []
                return
            }

            var values = historyValues(data)
            longHistory = averageValues(values.slice(-longHistorySize), 2)
            shortHistory = values.slice(-shortHistorySize)
        })
    }

    Timer {
        id: refreshTimer
        interval: root.refreshIntervalSeconds * 1000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: root.refreshData()
    }

    Connections {
        target: Plasmoid.configuration

        function onProxyBaseUrlChanged() {
            root.refreshData()
        }

        function onRefreshIntervalSecondsChanged() {
            refreshTimer.restart()
        }

        function onLongHistorySizeChanged() {
            root.refreshData()
        }

        function onShortHistorySizeChanged() {
            root.refreshData()
        }
    }

    fullRepresentation: PanelContent {}

    compactRepresentation: PanelContent {}

    component PanelContent: Item {
        id: panelContent

        width: root.panelWidth
        height: root.panelHeight
        implicitWidth: root.panelWidth
        implicitHeight: root.panelHeight
        Layout.minimumWidth: root.panelWidth
        Layout.preferredWidth: root.panelWidth
        Layout.maximumWidth: root.panelWidth
        Layout.minimumHeight: Kirigami.Units.gridUnit
        clip: true

        RowLayout {
            id: row
            width: root.panelWidth
            height: Math.max(root.panelHeight, panelContent.height)
            anchors.verticalCenter: parent.verticalCenter
            spacing: root.panelSpacing

            Controls.Label {
                Layout.alignment: Qt.AlignVCenter
                Layout.minimumWidth: root.valueWidth
                Layout.preferredWidth: root.valueWidth
                Layout.maximumWidth: root.valueWidth
                text: root.currentText
                color: root.errorMessage.length > 0 ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.textColor
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }

            HistoryGraph {
                Layout.minimumWidth: root.graphWidth
                Layout.preferredWidth: root.graphWidth
                Layout.maximumWidth: root.graphWidth
                Layout.preferredHeight: Math.max(Kirigami.Units.gridUnit, panelContent.height)
                Layout.alignment: Qt.AlignVCenter
                values: root.longHistory
                title: i18n("%1 readings", root.longHistorySize)
                pointDistance: 2.5
            }

            HistoryGraph {
                Layout.minimumWidth: root.graphWidth
                Layout.preferredWidth: root.graphWidth
                Layout.maximumWidth: root.graphWidth
                Layout.preferredHeight: Math.max(Kirigami.Units.gridUnit, panelContent.height)
                Layout.alignment: Qt.AlignVCenter
                values: root.shortHistory
                title: i18n("%1 readings", root.shortHistorySize)
                pointDistance: 1
            }
        }
    }

    component HistoryGraph: Canvas {
        id: graph

        property var values: []
        property string title: ""
        property real pointDistance: 2.5
        property real maxGraphValue: 22.0

        implicitWidth: Kirigami.Units.gridUnit * 2.5
        implicitHeight: Kirigami.Units.gridUnit
        antialiasing: true
        Controls.ToolTip.visible: graphMouseArea.containsMouse
        Controls.ToolTip.text: title

        onValuesChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        MouseArea {
            id: graphMouseArea
            anchors.fill: parent
            hoverEnabled: true
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            var borderColor = String(Kirigami.Theme.disabledTextColor)
            var dotColor = String(Kirigami.Theme.textColor)
            var padding = 2
            var innerWidth = Math.max(1, width - padding * 2)
            var innerHeight = Math.max(1, height - padding * 2)

            ctx.strokeStyle = borderColor
            ctx.lineWidth = 1
            ctx.strokeRect(0.5, 0.5, Math.max(0, width - 1), Math.max(0, height - 1))

            if (!values || values.length === 0) {
                return
            }

            ctx.fillStyle = dotColor

            var maxVisiblePoints = Math.max(1, Math.floor(innerWidth / pointDistance))
            var visibleValues = values.slice(-maxVisiblePoints)
            var graphWidth = Math.max(0, (visibleValues.length - 1) * pointDistance)
            var startX = padding + Math.max(0, (innerWidth - graphWidth) / 2)

            for (var index = 0; index < visibleValues.length; index++) {
                var x = startX + index * pointDistance
                var normalizedValue = Math.max(0, Math.min(maxGraphValue, visibleValues[index])) / maxGraphValue
                var y = padding + (1 - normalizedValue) * innerHeight
                ctx.beginPath()
                ctx.arc(x, y, 1.5, 0, Math.PI * 2, false)
                ctx.fill()
            }
        }
    }
}
