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
})
