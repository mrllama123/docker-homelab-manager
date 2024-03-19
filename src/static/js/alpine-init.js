document.addEventListener('alpine:init', () => {
    Alpine.data('tableBackupSchedules', () => ({
        selected: [],
        clickRow(id) {
            if (this.selected.includes(id)) {
                this.selected = this.selected.filter((item) => item !== id)
            } else {
                this.selected.push(id)
            }
        },
        deleteSelected() {
            htmx.ajax(
                "DELETE",
                "/volumes/backup/schedules",
                {
                    source: "closest form",
                    target: "#backup-schedule-rows",
                    values: { "schedules": this.selected }
                }
            )
            this.selected = []
        }

    }))
    Alpine.data('tableBackupRestore', () => ({
        selected: [],
        clickRow(id) {
            if (this.selected.some(item => item["backup_id"] === id)){
                this.selected = this.selected.filter((item) => item["backup_id"] !== id)
            } else {
                this.selected.push({"backup_id": id, "volume_name": ""})
            }
        },
        isSelected(id) {
            return this.selected.some(item => item["backup_id"] === id)
        },
        restoreVolumes() {
            htmx.ajax(
                "POST",
                "/volumes/restore",
                {
                    source: "closest form",
                    target: "#notifications",
                    values: { "volumes": this.selected }
                }
            )
            this.selected = []
        }
    }))
    Alpine.data('mainWindowState', () => ({
        mainWindowState: Alpine.$persist({tabState: "backup-volumes"}),
        switchTab(tab) {
            this.mainWindowState.tabState = tab
        }
    }))
})
