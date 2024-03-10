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
            if (this.selected.includes(id)) {
                this.selected = this.selected.filter((item) => item !== id)
            } else {
                this.selected.push(id)
            }
        },
        restoreVolume() {
            htmx.ajax(
                "POST",
                "/volumes/backup/restore",
                {
                    source: "closest form",
                    target: "#backup-restore-rows",
                    values: { "backups": this.selected }
                }
            )
            this.selected = []
        }
    }))
})
