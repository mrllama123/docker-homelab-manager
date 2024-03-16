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
    Alpine.data('draggableWindow', () => ({
        dragging: false, 
        offsetX: 0, 
        offsetY: 0,
        startDrag() {
            if (this.$root.style.width !== '100%') {
                this.dragging = true
                this.offsetX = this.$event.clientX - this.$root.offsetLeft
                this.offsetY = this.$event.clientY - this.$root.offsetTop
            }
        },
        drag() {
            if (this.dragging) {
                this.$root.style.left = (this.$event.clientX - this.offsetX) + 'px'
                this.$root.style.top = (this.$event.clientY - this.offsetY) + 'px'
            }
        },
        stopDrag() {
            this.dragging = false
        },
        expandWindow(){
            if (this.$root.style.width === '100%') {
                this.$root.style.width = '50%'
                this.$root.style.left = '5px' 
                this.$root.style.top = '5px';
            } else {
                this.$root.style.width = '100%'; 
                this.$root.style.left = '0'; 
                this.$root.style.top = '0';
            }
        }
    }))
})
